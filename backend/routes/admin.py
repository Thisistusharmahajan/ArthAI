"""
Admin Route — /api/admin/*
Handles: file uploads, web scraping, model retraining, stats
Protected by simple JWT auth (extend with proper user management in production)
"""
import os
import logging
import threading
from datetime import timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import create_access_token, jwt_required

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt", ".md"}

# Global training status tracker
_training_status = {
    "is_training": False,
    "progress": {},
    "last_trained": None,
    "total_chunks": 0,
}


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ── Auth ──────────────────────────────────────────────────────

@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    from config import Config
    if (data.get("username") == Config.ADMIN_USERNAME and
            data.get("password") == Config.ADMIN_PASSWORD):
        token = create_access_token(identity="admin", expires_delta=timedelta(hours=12))
        return jsonify({"access_token": token, "message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401


# ── File Upload ───────────────────────────────────────────────

@admin_bp.route("/api/admin/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file in request"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Supported: {ALLOWED_EXTENSIONS}"}), 400

    from config import Config
    filename = secure_filename(file.filename)
    dest = os.path.join(Config.UPLOAD_DIR, filename)
    file.save(dest)

    # Auto-ingest into RAG
    try:
        from ml.document_loader import DocumentLoader
        rag = current_app.config["RAG_ENGINE"]
        docs = DocumentLoader.load(dest, source_name=filename)
        result = rag.add_documents(docs)
        return jsonify({
            "message": f"File uploaded and ingested successfully",
            "filename": filename,
            "docs_extracted": len(docs),
            "chunks_added": result["added"],
            "total_chunks": result["total"],
        })
    except Exception as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
        return jsonify({
            "message": "File uploaded but ingestion failed",
            "filename": filename,
            "error": str(e),
        }), 207


# ── Web Scraping ──────────────────────────────────────────────

@admin_bp.route("/api/admin/scrape", methods=["POST"])
@jwt_required()
def trigger_scrape():
    data = request.get_json() or {}
    sources = data.get("sources", "all")  # "all" or list of source names

    def run_scrape():
        try:
            from ml.web_scraper import FinancialScraper
            scraper = FinancialScraper()
            docs = scraper.scrape_all()
            rag = current_app.config["RAG_ENGINE"]
            result = rag.add_documents(docs)
            _training_status["total_chunks"] = result["total"]
            logger.info(f"Scrape complete: {len(docs)} sources, {result['added']} new chunks")
        except Exception as e:
            logger.error(f"Background scrape failed: {e}", exc_info=True)

    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()
    return jsonify({"message": "Scraping started in background", "sources": sources})


# ── Retrain / Rebuild Index ───────────────────────────────────

@admin_bp.route("/api/admin/retrain", methods=["POST"])
@jwt_required()
def retrain():
    """Rebuild the FAISS index from all uploaded files + scraped data."""
    if _training_status["is_training"]:
        return jsonify({"error": "Training already in progress"}), 409

    def run_training():
        _training_status["is_training"] = True
        _training_status["progress"] = {}
        try:
            from config import Config
            from ml.document_loader import DocumentLoader
            from ml.web_scraper import FinancialScraper

            rag = current_app.config["RAG_ENGINE"]
            rag.clear()
            all_docs = []

            # Step 1: Load all uploaded files
            _training_status["progress"]["files"] = "loading"
            upload_dir = Config.UPLOAD_DIR
            for fname in os.listdir(upload_dir):
                fpath = os.path.join(upload_dir, fname)
                if allowed_file(fname):
                    try:
                        docs = DocumentLoader.load(fpath, source_name=fname)
                        all_docs.extend(docs)
                    except Exception as e:
                        logger.warning(f"Could not load {fname}: {e}")
            _training_status["progress"]["files"] = f"done ({len(all_docs)} docs)"

            # Step 2: Scrape live data
            _training_status["progress"]["scraping"] = "running"
            scraper = FinancialScraper()
            web_docs = scraper.scrape_all()
            all_docs.extend(web_docs)
            _training_status["progress"]["scraping"] = f"done ({len(web_docs)} sources)"

            # Step 3: Embed and index
            _training_status["progress"]["embedding"] = "running"
            result = rag.add_documents(all_docs)
            _training_status["progress"]["embedding"] = "done"
            _training_status["progress"]["faiss_index"] = "done"
            _training_status["total_chunks"] = result["total"]

            from datetime import datetime
            _training_status["last_trained"] = datetime.utcnow().isoformat()
            logger.info(f"Retraining complete: {result['total']} total chunks")
        except Exception as e:
            logger.error(f"Retraining failed: {e}", exc_info=True)
            _training_status["progress"]["error"] = str(e)
        finally:
            _training_status["is_training"] = False

    thread = threading.Thread(target=run_training, daemon=True)
    thread.start()
    return jsonify({"message": "Retraining started", "status": "running"})


# ── Training Status ───────────────────────────────────────────

@admin_bp.route("/api/admin/status", methods=["GET"])
@jwt_required()
def training_status():
    rag = current_app.config["RAG_ENGINE"]
    rag_stats = rag.stats()
    return jsonify({
        **_training_status,
        "rag_stats": rag_stats,
    })


# ── RAG Stats (public for dashboard) ─────────────────────────

@admin_bp.route("/api/stats", methods=["GET"])
def public_stats():
    rag = current_app.config["RAG_ENGINE"]
    stats = rag.stats()
    return jsonify({
        "total_chunks": stats["total_chunks"],
        "sources_count": len(stats["sources"]),
        "last_trained": _training_status.get("last_trained"),
    })


# ── List Uploaded Files ───────────────────────────────────────

@admin_bp.route("/api/admin/files", methods=["GET"])
@jwt_required()
def list_files():
    from config import Config
    files = []
    for fname in os.listdir(Config.UPLOAD_DIR):
        fpath = os.path.join(Config.UPLOAD_DIR, fname)
        if os.path.isfile(fpath):
            files.append({
                "name": fname,
                "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "type": os.path.splitext(fname)[1].lstrip(".").upper(),
            })
    return jsonify({"files": files})


# ── Delete File ───────────────────────────────────────────────

@admin_bp.route("/api/admin/files/<filename>", methods=["DELETE"])
@jwt_required()
def delete_file(filename):
    from config import Config
    safe = secure_filename(filename)
    fpath = os.path.join(Config.UPLOAD_DIR, safe)
    if os.path.exists(fpath):
        os.remove(fpath)
        return jsonify({"message": f"{safe} deleted"})
    return jsonify({"error": "File not found"}), 404
