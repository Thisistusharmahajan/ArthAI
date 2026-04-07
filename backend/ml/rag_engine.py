"""
RAG Engine — Retrieval Augmented Generation
Handles: document embedding, FAISS indexing, semantic search, context retrieval
"""
import os
import json
import pickle
import logging
import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Full RAG pipeline:
      1. Documents → chunks → embeddings (sentence-transformers)
      2. Embeddings → FAISS index (persisted to disk)
      3. Query → embed → FAISS search → top-K chunks → LLM context
    """

    def __init__(self, config):
        self.config = config
        self.index = None
        self.chunks: List[dict] = []        # [{text, source, metadata}]
        self.embedder = None
        self._load_embedder()
        self._load_index()

    # ── Embedder ──────────────────────────────────────────────

    def _load_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(self.config.EMBEDDING_MODEL)
            logger.info(f"Embedder loaded: {self.config.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Could not load embedder: {e}. Using mock mode.")
            self.embedder = None

    def _embed(self, texts: List[str]) -> np.ndarray:
        if self.embedder:
            return self.embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        # Mock: random unit vectors for testing without GPU
        dim = 384
        vecs = np.random.randn(len(texts), dim).astype(np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms

    # ── FAISS Index ───────────────────────────────────────────

    def _index_path(self):
        return os.path.join(self.config.FAISS_INDEX_DIR, "index.faiss")

    def _chunks_path(self):
        return os.path.join(self.config.FAISS_INDEX_DIR, "chunks.pkl")

    def _load_index(self):
        try:
            import faiss
            if os.path.exists(self._index_path()) and os.path.exists(self._chunks_path()):
                self.index = faiss.read_index(self._index_path())
                with open(self._chunks_path(), "rb") as f:
                    self.chunks = pickle.load(f)
                logger.info(f"FAISS index loaded — {len(self.chunks)} chunks")
            else:
                logger.info("No existing FAISS index. Will create on first training.")
        except ImportError:
            logger.warning("FAISS not installed. Running without vector search.")
        except Exception as e:
            logger.error(f"Error loading index: {e}")

    def _save_index(self):
        try:
            import faiss
            os.makedirs(self.config.FAISS_INDEX_DIR, exist_ok=True)
            faiss.write_index(self.index, self._index_path())
            with open(self._chunks_path(), "wb") as f:
                pickle.dump(self.chunks, f)
            logger.info(f"FAISS index saved — {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    # ── Document Ingestion ────────────────────────────────────

    def add_documents(self, docs: List[dict]) -> dict:
        """
        docs = [{"text": "...", "source": "rbi_circular.pdf", "metadata": {...}}]
        Returns stats dict.
        """
        if not docs:
            return {"added": 0, "total": len(self.chunks)}

        new_chunks = self._chunk_documents(docs)
        if not new_chunks:
            return {"added": 0, "total": len(self.chunks)}

        texts = [c["text"] for c in new_chunks]
        embeddings = self._embed(texts).astype(np.float32)

        try:
            import faiss
            dim = embeddings.shape[1]
            if self.index is None:
                self.index = faiss.IndexFlatIP(dim)   # Inner product (cosine on normalized vecs)
            self.index.add(embeddings)
            self.chunks.extend(new_chunks)
            self._save_index()
            return {"added": len(new_chunks), "total": len(self.chunks)}
        except ImportError:
            # No FAISS — store chunks only
            self.chunks.extend(new_chunks)
            return {"added": len(new_chunks), "total": len(self.chunks)}

    def _chunk_documents(self, docs: List[dict]) -> List[dict]:
        chunks = []
        size = self.config.CHUNK_SIZE
        overlap = self.config.CHUNK_OVERLAP
        for doc in docs:
            text = doc.get("text", "").strip()
            source = doc.get("source", "unknown")
            meta = doc.get("metadata", {})
            if not text:
                continue
            # Sliding window chunking
            start = 0
            while start < len(text):
                end = min(start + size, len(text))
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "source": source,
                        "metadata": {**meta, "chunk_start": start},
                        "added_at": datetime.utcnow().isoformat()
                    })
                start += size - overlap
        return chunks

    # ── Retrieval ─────────────────────────────────────────────

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[dict]:
        """Return top-K relevant chunks for a query."""
        k = top_k or self.config.TOP_K_RESULTS
        if not self.chunks:
            return []

        q_emb = self._embed([query]).astype(np.float32)

        try:
            import faiss
            if self.index and self.index.ntotal > 0:
                k = min(k, self.index.ntotal)
                scores, indices = self.index.search(q_emb, k)
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(self.chunks):
                        results.append({**self.chunks[idx], "score": float(score)})
                return results
        except ImportError:
            pass

        # Fallback: simple keyword search
        query_lower = query.lower()
        scored = []
        for chunk in self.chunks:
            words = query_lower.split()
            hits = sum(1 for w in words if w in chunk["text"].lower())
            scored.append((hits, chunk))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:k] if _[0] > 0]

    def build_context(self, query: str) -> str:
        """Build the context string to inject into the LLM prompt."""
        chunks = self.retrieve(query)
        if not chunks:
            return ""
        parts = ["### Retrieved Financial Data\n"]
        for i, chunk in enumerate(chunks, 1):
            src = chunk.get("source", "unknown")
            parts.append(f"[Source {i}: {src}]\n{chunk['text']}\n")
        return "\n".join(parts)

    # ── Stats ─────────────────────────────────────────────────

    def stats(self) -> dict:
        sources = {}
        for c in self.chunks:
            src = c.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        return {
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "sources": sources,
        }

    def clear(self):
        self.index = None
        self.chunks = []
        # Remove persisted files
        for p in [self._index_path(), self._chunks_path()]:
            if os.path.exists(p):
                os.remove(p)
        logger.info("RAG index cleared.")
