# """
# ArthaAI — Indian Budget Analyzer & Investment Helper
# Flask Backend Entry Point
# """
# import os
# import logging
# from flask import Flask, jsonify
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# import anthropic

# from config import Config

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
# )
# logger = logging.getLogger(__name__)


# def create_app() -> Flask:
#     app = Flask(__name__)

#     # ── Config ────────────────────────────────────────────────
#     app.config["SECRET_KEY"] = Config.SECRET_KEY
#     app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
#     Config.ensure_dirs()

#     # ── Extensions ────────────────────────────────────────────
#     CORS(app, resources={r"/api/*": {"origins": "*"}})
#     JWTManager(app)

#     # ── Anthropic client ──────────────────────────────────────
#     if Config.ANTHROPIC_API_KEY:
#         app.config["ANTHROPIC_CLIENT"] = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
#         logger.info("Anthropic client initialized")
#     else:
#         app.config["ANTHROPIC_CLIENT"] = None
#         logger.warning("ANTHROPIC_API_KEY not set — chat will return mock responses")

#     # ── RAG Engine ────────────────────────────────────────────
#     from ml.rag_engine import RAGEngine
#     rag = RAGEngine(Config)
#     app.config["RAG_ENGINE"] = rag
#     logger.info(f"RAG engine ready — {rag.stats()['total_chunks']} chunks loaded")

#     # ── Seed initial financial data if index is empty ─────────
#     if rag.stats()["total_chunks"] == 0:
#         _seed_initial_data(rag)

#     # ── Blueprints ────────────────────────────────────────────
#     from routes.chat import chat_bp
#     from routes.admin import admin_bp
#     from routes.voice import voice_bp
#     from routes.export import export_bp

#     app.register_blueprint(chat_bp)
#     app.register_blueprint(admin_bp)
#     app.register_blueprint(voice_bp)
#     app.register_blueprint(export_bp)

#     # ── Health check ──────────────────────────────────────────
#     @app.route("/api/health")
#     def health():
#         rag_stats = rag.stats()
#         return jsonify({
#             "status": "ok",
#             "service": "ArthaAI Backend",
#             "rag_chunks": rag_stats["total_chunks"],
#             "anthropic_configured": bool(Config.ANTHROPIC_API_KEY),
#         })

#     @app.errorhandler(404)
#     def not_found(e):
#         return jsonify({"error": "Endpoint not found"}), 404

#     @app.errorhandler(500)
#     def server_error(e):
#         return jsonify({"error": "Internal server error"}), 500

#     logger.info("ArthaAI backend started successfully")
#     return app


# def _seed_initial_data(rag):
#     """Seed the RAG index with curated base financial knowledge on first startup."""
#     logger.info("Seeding initial financial knowledge base...")
#     from ml.web_scraper import FinancialScraper
#     try:
#         scraper = FinancialScraper()
#         docs = scraper.scrape_all()
#         result = rag.add_documents(docs)
#         logger.info(f"Seeded {result['added']} chunks from {len(docs)} financial data sources")
#     except Exception as e:
#         logger.error(f"Seeding failed: {e}")


# if __name__ == "__main__":
#     app = create_app()
#     port = int(os.getenv("PORT", 5000))
#     app.run(
#         host="0.0.0.0",
#         port=port,
#         debug=Config.DEBUG,
#         use_reloader=False,   # Disable reloader to prevent double RAG init
#     )

"""
ArthaAI — Indian Budget Analyzer & Investment Helper
Flask Backend Entry Point
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import google.generativeai as genai # <-- Swapped Anthropic for Gemini

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    Config.ensure_dirs()

    # ── Extensions ────────────────────────────────────────────
    # Updated CORS to handle the headers required for Auth
    CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])
    JWTManager(app)

    # ── Gemini client ──────────────────────────────────────
    # Replaced Anthropic with Google Gemini
    if hasattr(Config, 'GEMINI_API_KEY') and Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        app.config["GEMINI_CONFIGURED"] = True
        logger.info("Google Gemini client initialized")
    else:
        app.config["GEMINI_CONFIGURED"] = False
        logger.warning("GEMINI_API_KEY not set — chat will return mock responses")

    # ── RAG Engine ────────────────────────────────────────────
    from ml.rag_engine import RAGEngine
    rag = RAGEngine(Config)
    app.config["RAG_ENGINE"] = rag
    logger.info(f"RAG engine ready — {rag.stats()['total_chunks']} chunks loaded")

    # ── Seed initial financial data if index is empty ─────────
    if rag.stats()["total_chunks"] == 0:
        _seed_initial_data(rag)

    # ── Blueprints ────────────────────────────────────────────
    from routes.chat import chat_bp
    from routes.admin import admin_bp
    from routes.voice import voice_bp
    from routes.export import export_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(export_bp)

    # ── Global CORS Preflight Handler ─────────────────────────
    # This prevents the Axios network error by approving preflight OPTIONS requests
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        return response

    # ── Health check ──────────────────────────────────────────
    @app.route("/api/health")
    def health():
        rag_stats = rag.stats()
        return jsonify({
            "status": "ok",
            "service": "ArthaAI Backend",
            "rag_chunks": rag_stats["total_chunks"],
            "gemini_configured": app.config.get("GEMINI_CONFIGURED", False),
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    logger.info("ArthaAI backend started successfully")
    return app


def _seed_initial_data(rag):
    """Seed the RAG index with curated base financial knowledge on first startup."""
    logger.info("Seeding initial financial knowledge base...")
    from ml.web_scraper import FinancialScraper
    try:
        scraper = FinancialScraper()
        docs = scraper.scrape_all()
        result = rag.add_documents(docs)
        logger.info(f"Seeded {result['added']} chunks from {len(docs)} financial data sources")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=Config.DEBUG,
        use_reloader=False,   # Disable reloader to prevent double RAG init
    )