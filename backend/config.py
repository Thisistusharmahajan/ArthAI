# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Config:
#     # ── Anthropic ──────────────────────────────────────────────
#     ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
#     CLAUDE_MODEL = "claude-sonnet-4-20250514"

#     # ── Flask ──────────────────────────────────────────────────
#     SECRET_KEY = os.getenv("SECRET_KEY", "arthaai-secret-change-in-production")
#     JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "arthaai-jwt-secret")
#     DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

#     # ── Paths ──────────────────────────────────────────────────
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     DATA_DIR = os.path.join(BASE_DIR, "data")
#     UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
#     FAISS_INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")
#     EXPORT_DIR = os.path.join(DATA_DIR, "exports")

#     # ── ML / Embeddings ────────────────────────────────────────
#     EMBEDDING_MODEL = "all-MiniLM-L6-v2"
#     CHUNK_SIZE = 800
#     CHUNK_OVERLAP = 100
#     TOP_K_RESULTS = 6

#     # ── Admin credentials (change in production) ───────────────
#     ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
#     ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "arthaai@2025")

#     # ── Data source URLs ───────────────────────────────────────
#     SCRAPE_SOURCES = {
#         "rbi_rates": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
#         "rbi_policy": "https://www.rbi.org.in/Scripts/MonetaryPolicy.aspx",
#         "nse_indices": "https://www.nseindia.com/api/allIndices",
#         "amfi_nav": "https://www.amfiindia.com/spages/NAVAll.txt",
#         "sebi_circulars": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=2&smid=0",
#     }

#     # ── System prompt ─────────────────────────────────────────
#     SYSTEM_PROMPT = """You are ArthaAI, an expert Indian financial advisor and budget analyst.
# You have deep knowledge of:
# - Indian mutual funds (SIPs, ELSS, flexi-cap, debt funds, liquid funds)
# - Stock markets (NSE, BSE, Nifty 50, Sensex, sectoral indices)
# - Fixed deposits (SBI, HDFC, ICICI, Axis — rates, tenures, TDS rules)
# - Government schemes (PPF, NPS, Sukanya Samriddhi, Senior Citizen Savings Scheme)
# - Gold & silver (SGB, Gold ETF, physical gold, MCX prices)
# - Tax planning (Section 80C, 80D, 80CCD, HRA, capital gains tax)
# - Real estate (home loans, EMI, PMAY, stamp duty)
# - Insurance (term life, health, ULIP comparison)
# - Indian Budget implications for different income classes
# - RBI monetary policy and its effects on savings and loans

# Rules:
# 1. Always give advice in Indian context — mention actual fund names, SEBI-registered platforms, and Indian tax laws.
# 2. Classify users into income brackets: Low (<₹5L/yr), Middle (₹5–15L), Upper Middle (₹15–30L), Rich (₹30L–1Cr), Super Rich (>₹1Cr).
# 3. Use context from the provided documents to give data-backed answers.
# 4. Format responses with clear sections using **bold** headers.
# 5. Always mention risk levels (Low / Moderate / High) for each recommendation.
# 6. Quote actual rates and figures when available from context.
# 7. Suggest 2–3 concrete options ranked by suitability for the user's profile.
# 8. For tax queries, always recommend consulting a CA for final decisions.
# 9. Respond in the same language the user writes in (Hindi or English).
# 10. Never guarantee returns — always say "expected" or "historical average."

# You have access to real-time data from RBI, NSE, AMFI, and MCX through the RAG pipeline.
# """

#     @classmethod
#     def ensure_dirs(cls):
#         for d in [cls.DATA_DIR, cls.UPLOAD_DIR, cls.FAISS_INDEX_DIR, cls.EXPORT_DIR]:
#             os.makedirs(d, exist_ok=True)


import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Google Gemini ──────────────────────────────────────────
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.5-flash"
    # ── Flask ──────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "arthaai-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "arthaai-jwt-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # ── Paths ──────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
    FAISS_INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")
    EXPORT_DIR = os.path.join(DATA_DIR, "exports")

    # ── ML / Embeddings ────────────────────────────────────────
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    TOP_K_RESULTS = 6

    # ── Admin credentials (change in production) ───────────────
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "arthaai@2025")

    # ── Data source URLs ───────────────────────────────────────
    SCRAPE_SOURCES = {
        "rbi_rates": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
        "rbi_policy": "https://www.rbi.org.in/Scripts/MonetaryPolicy.aspx",
        "nse_indices": "https://www.nseindia.com/api/allIndices",
        "amfi_nav": "https://www.amfiindia.com/spages/NAVAll.txt",
        "sebi_circulars": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=2&smid=0",
    }

    # ── System prompt ─────────────────────────────────────────
    SYSTEM_PROMPT = """You are ArthaAI, an expert Indian financial advisor and budget analyst.
You have deep knowledge of:
- Indian mutual funds (SIPs, ELSS, flexi-cap, debt funds, liquid funds)
- Stock markets (NSE, BSE, Nifty 50, Sensex, sectoral indices)
- Fixed deposits (SBI, HDFC, ICICI, Axis — rates, tenures, TDS rules)
- Government schemes (PPF, NPS, Sukanya Samriddhi, Senior Citizen Savings Scheme)
- Gold & silver (SGB, Gold ETF, physical gold, MCX prices)
- Tax planning (Section 80C, 80D, 80CCD, HRA, capital gains tax)
- Real estate (home loans, EMI, PMAY, stamp duty)
- Insurance (term life, health, ULIP comparison)
- Indian Budget implications for different income classes
- RBI monetary policy and its effects on savings and loans

Rules:
1. Always give advice in Indian context — mention actual fund names, SEBI-registered platforms, and Indian tax laws.
2. Classify users into income brackets: Low (<₹5L/yr), Middle (₹5–15L), Upper Middle (₹15–30L), Rich (₹30L–1Cr), Super Rich (>₹1Cr).
3. Use context from the provided documents to give data-backed answers.
4. Format responses with clear sections using **bold** headers.
5. Always mention risk levels (Low / Moderate / High) for each recommendation.
6. Quote actual rates and figures when available from context.
7. Suggest 2–3 concrete options ranked by suitability for the user's profile.
8. For tax queries, always recommend consulting a CA for final decisions.
9. Respond in the same language the user writes in (Hindi or English).
10. Never guarantee returns — always say "expected" or "historical average."

You have access to real-time data from RBI, NSE, AMFI, and MCX through the RAG pipeline.
"""

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.DATA_DIR, cls.UPLOAD_DIR, cls.FAISS_INDEX_DIR, cls.EXPORT_DIR]:
            os.makedirs(d, exist_ok=True)