"""
Document Loader — ingests PDF, CSV, Excel, JSON, plain text
Returns normalized [{text, source, metadata}] for the RAG engine.
"""
import os
import io
import logging
import pandas as pd
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentLoader:

    # ── Public entry point ────────────────────────────────────

    @staticmethod
    def load(filepath: str, source_name: Optional[str] = None) -> List[dict]:
        """Auto-detect file type and load."""
        ext = os.path.splitext(filepath)[1].lower()
        name = source_name or os.path.basename(filepath)
        loaders = {
            ".pdf": DocumentLoader._load_pdf,
            ".csv": DocumentLoader._load_csv,
            ".xlsx": DocumentLoader._load_excel,
            ".xls": DocumentLoader._load_excel,
            ".json": DocumentLoader._load_json,
            ".txt": DocumentLoader._load_text,
            ".md": DocumentLoader._load_text,
        }
        loader = loaders.get(ext)
        if not loader:
            raise ValueError(f"Unsupported file type: {ext}")
        docs = loader(filepath)
        for d in docs:
            d.setdefault("source", name)
            d.setdefault("metadata", {})
            d["metadata"]["loaded_at"] = datetime.utcnow().isoformat()
            d["metadata"]["file_type"] = ext.lstrip(".")
        logger.info(f"Loaded {len(docs)} document(s) from {name}")
        return docs

    @staticmethod
    def load_from_text(text: str, source_name: str, metadata: dict = None) -> List[dict]:
        """Load from a raw string (e.g. scraped web content)."""
        return [{
            "text": text.strip(),
            "source": source_name,
            "metadata": metadata or {},
        }]

    # ── PDF ───────────────────────────────────────────────────

    @staticmethod
    def _load_pdf(filepath: str) -> List[dict]:
        docs = []
        # Try pdfplumber first (better text extraction)
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        docs.append({
                            "text": text,
                            "metadata": {"page": i + 1, "total_pages": len(pdf.pages)}
                        })
            if docs:
                return docs
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")

        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        docs.append({
                            "text": text,
                            "metadata": {"page": i + 1}
                        })
        except Exception as e:
            logger.error(f"PDF loading failed: {e}")

        return docs

    # ── CSV ───────────────────────────────────────────────────

    @staticmethod
    def _load_csv(filepath: str) -> List[dict]:
        try:
            df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="skip")
            return DocumentLoader._dataframe_to_docs(df, filepath)
        except Exception as e:
            logger.error(f"CSV loading failed: {e}")
            return []

    # ── Excel ─────────────────────────────────────────────────

    @staticmethod
    def _load_excel(filepath: str) -> List[dict]:
        docs = []
        try:
            xl = pd.ExcelFile(filepath)
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                sheet_docs = DocumentLoader._dataframe_to_docs(df, f"{filepath}[{sheet}]")
                for d in sheet_docs:
                    d["metadata"]["sheet"] = sheet
                docs.extend(sheet_docs)
        except Exception as e:
            logger.error(f"Excel loading failed: {e}")
        return docs

    # ── JSON ──────────────────────────────────────────────────

    @staticmethod
    def _load_json(filepath: str) -> List[dict]:
        import json
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
                return DocumentLoader._dataframe_to_docs(df, filepath)
            elif isinstance(data, dict):
                text = json.dumps(data, indent=2, ensure_ascii=False)
                return [{"text": text, "metadata": {}}]
        except Exception as e:
            logger.error(f"JSON loading failed: {e}")
        return []

    # ── Plain text ────────────────────────────────────────────

    @staticmethod
    def _load_text(filepath: str) -> List[dict]:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return [{"text": text, "metadata": {}}]
        except Exception as e:
            logger.error(f"Text loading failed: {e}")
            return []

    # ── DataFrame → docs ──────────────────────────────────────

    @staticmethod
    def _dataframe_to_docs(df: pd.DataFrame, source: str, rows_per_chunk: int = 50) -> List[dict]:
        """
        Convert a DataFrame to text chunks.
        - Summarize schema first
        - Then chunk rows into readable text blocks
        """
        docs = []
        df = df.fillna("N/A")

        # Schema summary
        schema_lines = [f"Dataset: {os.path.basename(source)}"]
        schema_lines.append(f"Columns ({len(df.columns)}): {', '.join(str(c) for c in df.columns)}")
        schema_lines.append(f"Rows: {len(df)}")
        # Numeric summary
        num_cols = df.select_dtypes(include="number").columns.tolist()
        for col in num_cols[:8]:
            try:
                schema_lines.append(
                    f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, "
                    f"mean={df[col].mean():.2f}"
                )
            except Exception:
                pass
        docs.append({"text": "\n".join(schema_lines), "metadata": {"type": "schema_summary"}})

        # Row chunks
        for start in range(0, len(df), rows_per_chunk):
            chunk_df = df.iloc[start:start + rows_per_chunk]
            text = chunk_df.to_string(index=False, max_colwidth=80)
            docs.append({
                "text": text,
                "metadata": {"type": "data_rows", "row_start": start, "row_end": start + len(chunk_df)}
            })

        return docs
