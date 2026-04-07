ArthaAI — Indian Budget Analyzer & Investment HelperAI-powered financial advisor for Indian investors. Ask about SIPs, FDs, gold, stocks, tax planning, and more — backed by live RBI, NSE, and AMFI data through a RAG (Retrieval Augmented Generation) pipeline.FeaturesAI Chat Interface — ChatGPT-style conversation with streaming responsesVoice Input & Output — Speak your query, hear the answer (Whisper + gTTS)RAG-Powered — Answers grounded in live RBI, NSE, AMFI, MCX dataUser Profiles — Personalized advice based on income, city, risk appetiteAdmin Panel — Upload CSVs/PDFs, trigger web scraping, retrain modelExport — Download chat as PDF or Excel, share on WhatsAppHindi + English — Bilingual supportTech StackLayerTechnologyFrontendReact 18 + Vite + React MarkdownBackendPython Flask 3AI/LLMGoogle Gemini (gemini-2.5-flash)RAGFAISS + sentence-transformers (all-MiniLM-L6-v2)Speech-to-TextOpenAI WhisperText-to-SpeechgTTS (Google)PDF ExportReportLabExcel ExportopenpyxlAuthFlask-JWT-ExtendedDeploymentRender / RailwayProject StructurePlaintextarthaai/
├── backend/
│   ├── app.py              ← Flask entry point
│   ├── config.py           ← All config & system prompt
│   ├── gunicorn.conf.py    ← Production server config
│   ├── requirements.txt
│   ├── .env.example        ← Copy to .env and fill values
│   ├── routes/
│   │   ├── chat.py         ← POST /api/chat (streaming)
│   │   ├── admin.py        ← /api/admin/* (JWT protected)
│   │   ├── voice.py        ← /api/voice/transcribe + /speak
│   │   └── export.py       ← /api/export/pdf, /excel, /whatsapp
│   └── ml/
│       ├── rag_engine.py       ← FAISS vector store + retrieval
│       ├── document_loader.py  ← PDF/CSV/Excel/JSON ingestion
│       └── web_scraper.py      ← RBI, NSE, AMFI, MCX scrapers
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx             ← Layout, routing, sidebar
│       ├── index.css
│       ├── main.jsx
│       ├── api/
│       │   └── client.js       ← All API calls (axios + fetch SSE)
│       └── pages/
│           ├── Chat.jsx        ← Full chat UI with voice + export
│           └── Admin.jsx       ← Data management dashboard
│
└── render.yaml                 ← One-click Render deployment
Quick Start (Local Development)1. Clone and set up backendBashcd arthaai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
2. Get your Google Gemini API keyGo to Google AI StudioCreate an API key (Free Tier available)Paste it in .env as GEMINI_API_KEY=AIzaSy...3. Run the backendBashcd backend
python app.py
# Server starts at http://localhost:5000
# On first run, it auto-seeds financial data into the RAG index
4. Set up and run the frontendBashcd frontend
npm install
npm run dev
# App opens at http://localhost:5173
5. Access the appChat interface: http://localhost:5173Admin panel: http://localhost:5173 → click "Admin Panel" tabUsername: admin | Password: arthaai@2025API health check: http://localhost:5000/api/healthAPI ReferenceChatJSONPOST /api/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Should I invest in SIP or FD?"}
  ],
  "profile": {
    "name": "Rahul",
    "city": "Mumbai",
    "monthly_income": 120000,
    "monthly_savings": 30000,
    "risk_appetite": "Moderate"
  },
  "stream": true
}

→ SSE stream of {"token": "..."} events, ends with [DONE]
VoicePlaintextPOST /api/voice/transcribe
Content-Type: multipart/form-data
Body: audio (file), language (en|hi)
→ {"transcript": "...", "language": "en"}

POST /api/voice/speak
Body: {"text": "...", "language": "en"}
→ MP3 audio stream
Admin (requires JWT)PlaintextPOST /api/admin/login
Body: {"username": "admin", "password": "..."}
→ {"access_token": "..."}

POST /api/admin/upload          ← Upload CSV/PDF/Excel
POST /api/admin/scrape          ← Trigger web scraping
POST /api/admin/retrain         ← Rebuild FAISS index
GET  /api/admin/status          ← Training status + RAG stats
GET  /api/admin/files           ← List uploaded files
DELETE /api/admin/files/<name>  ← Delete a file
ExportPlaintextPOST /api/export/pdf            → PDF download
POST /api/export/excel          → Excel download
POST /api/export/whatsapp       → {"whatsapp_url": "https://wa.me/?text=..."}
Adding Training DataOption A: Via Admin Panel UILogin to Admin PanelDrag & drop CSV, PDF, Excel filesClick "Retrain Now"Option B: Via APIBashcurl -X POST http://localhost:5000/api/admin/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/budget2025.pdf"
Recommended Datasets (Kaggle)Indian Stock Market Historical Data — BSE/NSE historical pricesMutual Fund NAV Data — Historical NAV of all AMFI-registered fundsRBI Economic Data — Interest rates, CPI, WPI time seriesGold Price India — MCX gold price historyData Sources Auto-Scraped on StartupSourceDataRBIRepo rate, CRR, SLR, policy announcementsNSENifty 50, Bank Nifty, sectoral indicesAMFICurrent NAVs of all mutual fundsMCXGold and silver spot pricesBank WebsitesFD rates (SBI, HDFC, ICICI, Axis)Deployment on RenderPush code to GitHubGo to render.com → New → BlueprintConnect your repo — Render auto-detects render.yamlSet environment variables in Render dashboard:GEMINI_API_KEY = your keyADMIN_PASSWORD = your secure passwordDeploy — both frontend and backend deploy automaticallyDeployment on RailwayBash# Backend
cd backend
railway login
railway init
railway up

# Set env vars
railway variables set GEMINI_API_KEY=AIzaSy...
railway variables set ADMIN_PASSWORD=your_password
For frontend, deploy the frontend/ folder to Vercel or Netlify:Bashcd frontend
npm run build
# Upload dist/ to Netlify, or use: netlify deploy --prod --dir=dist
Customizing the AIThe system prompt in config.py (SYSTEM_PROMPT) controls how ArthaAI responds. You can:Add more investment categoriesChange tone (formal/casual)Add specific disclaimersAdd regional languagesInclude your firm's investment philosophyExtending the RAG PipelineTo add a new data source:Python# In ml/web_scraper.py, add a new method:
def scrape_sebi_circulars(self) -> dict:
    r = requests.get("https://www.sebi.gov.in/...", headers=HEADERS)
    # Parse and return:
    return {
        "text": "parsed text content",
        "source": "SEBI Circulars",
        "metadata": {"type": "regulatory"}
    }

# Then add it to scrape_all():
docs.append(self.scrape_sebi_circulars())
TroubleshootingIssueFixGEMINI_API_KEY not setAdd key to .env fileWhisper slow on first useDownloads model (~150MB) on first call — waitFAISS import errorRun pip install faiss-cpuCORS errors in browserEnsure backend is on port 5000, Vite proxy is configuredPDF export failsRun pip install reportlabVoice input no permissionUse HTTPS in production (MediaRecorder requires secure context)

DisclaimerArthaAI provides general financial information and education. It is not a SEBI-registered investment advisor. Always verify information with official sources (RBI, SEBI, AMFI) and consult a qualified CA or financial advisor before making investment decisions. Investments are subject to market risks.Built with ❤️ for Indian investors | Powered by Google Gemini + FAISS RAG