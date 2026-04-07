# ArthaAI — Indian Budget Analyzer & Investment Helper

> AI-powered financial advisor for Indian investors. Ask about SIPs, FDs, gold, stocks, tax planning, and more — backed by live RBI, NSE, and AMFI data through a RAG (Retrieval Augmented Generation) pipeline.

---

## Features

- **AI Chat Interface** — ChatGPT-style conversation with streaming responses
- **Voice Input & Output** — Speak your query, hear the answer (Whisper + gTTS)
- **RAG-Powered** — Answers grounded in live RBI, NSE, AMFI, MCX data
- **User Profiles** — Personalized advice based on income, city, risk appetite
- **Admin Panel** — Upload CSVs/PDFs, trigger web scraping, retrain model
- **Export** — Download chat as PDF or Excel, share on WhatsApp
- **Hindi + English** — Bilingual support

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + React Markdown |
| Backend | Python Flask 3 |
| AI/LLM | Anthropic Claude (claude-sonnet-4) |
| RAG | FAISS + sentence-transformers (all-MiniLM-L6-v2) |
| Speech-to-Text | OpenAI Whisper |
| Text-to-Speech | gTTS (Google) |
| PDF Export | ReportLab |
| Excel Export | openpyxl |
| Auth | Flask-JWT-Extended |
| Deployment | Render / Railway |

---

## Project Structure

```
arthaai/
├── backend/
│   ├── app.py                  ← Flask entry point
│   ├── config.py               ← All config & system prompt
│   ├── gunicorn.conf.py        ← Production server config
│   ├── requirements.txt
│   ├── .env.example            ← Copy to .env and fill values
│   ├── routes/
│   │   ├── chat.py             ← POST /api/chat (streaming)
│   │   ├── admin.py            ← /api/admin/* (JWT protected)
│   │   ├── voice.py            ← /api/voice/transcribe + /speak
│   │   └── export.py           ← /api/export/pdf, /excel, /whatsapp
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
```

---

## Quick Start (Local Development)

### 1. Clone and set up backend

```bash
cd arthaai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
```

### 2. Get your Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Paste it in `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

### 3. Run the backend

```bash
cd backend
python app.py
# Server starts at http://localhost:5000
# On first run, it auto-seeds financial data into the RAG index
```

### 4. Set up and run the frontend

```bash
cd frontend
npm install
npm run dev
# App opens at http://localhost:3000
```

### 5. Access the app

- **Chat interface:** http://localhost:3000
- **Admin panel:** http://localhost:3000 → click "Admin Panel" tab
  - Username: `admin` | Password: `arthaai@2025`
- **API health check:** http://localhost:5000/api/health

---

## API Reference

### Chat

```
POST /api/chat
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
```

### Voice

```
POST /api/voice/transcribe
Content-Type: multipart/form-data
Body: audio (file), language (en|hi)
→ {"transcript": "...", "language": "en"}

POST /api/voice/speak
Body: {"text": "...", "language": "en"}
→ MP3 audio stream
```

### Admin (requires JWT)

```
POST /api/admin/login
Body: {"username": "admin", "password": "..."}
→ {"access_token": "..."}

POST /api/admin/upload          ← Upload CSV/PDF/Excel
POST /api/admin/scrape          ← Trigger web scraping
POST /api/admin/retrain         ← Rebuild FAISS index
GET  /api/admin/status          ← Training status + RAG stats
GET  /api/admin/files           ← List uploaded files
DELETE /api/admin/files/<name>  ← Delete a file
```

### Export

```
POST /api/export/pdf            → PDF download
POST /api/export/excel          → Excel download
POST /api/export/whatsapp       → {"whatsapp_url": "https://wa.me/?text=..."}
```

---

## Adding Training Data

### Option A: Via Admin Panel UI
1. Login to Admin Panel
2. Drag & drop CSV, PDF, Excel files
3. Click "Retrain Now"

### Option B: Via API
```bash
curl -X POST http://localhost:5000/api/admin/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/budget2025.pdf"
```

### Recommended Datasets (Kaggle)
- **Indian Stock Market Historical Data** — BSE/NSE historical prices
- **Mutual Fund NAV Data** — Historical NAV of all AMFI-registered funds
- **RBI Economic Data** — Interest rates, CPI, WPI time series
- **Gold Price India** — MCX gold price history

### Data Sources Auto-Scraped on Startup
| Source | Data |
|--------|------|
| RBI | Repo rate, CRR, SLR, policy announcements |
| NSE | Nifty 50, Bank Nifty, sectoral indices |
| AMFI | Current NAVs of all mutual funds |
| MCX | Gold and silver spot prices |
| Bank Websites | FD rates (SBI, HDFC, ICICI, Axis) |

---

## Deployment on Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — Render auto-detects `render.yaml`
4. Set environment variables in Render dashboard:
   - `ANTHROPIC_API_KEY` = your key
   - `ADMIN_PASSWORD` = your secure password
5. Deploy — both frontend and backend deploy automatically

## Deployment on Railway

```bash
# Backend
cd backend
railway login
railway init
railway up

# Set env vars
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set ADMIN_PASSWORD=your_password
```

For frontend, deploy the `frontend/` folder to Vercel or Netlify:
```bash
cd frontend
npm run build
# Upload dist/ to Netlify, or use: netlify deploy --prod --dir=dist
```

---

## Customizing the AI

The system prompt in `config.py` (`SYSTEM_PROMPT`) controls how ArthaAI responds. You can:

- Add more investment categories
- Change tone (formal/casual)
- Add specific disclaimers
- Add regional languages
- Include your firm's investment philosophy

---

## Extending the RAG Pipeline

To add a new data source:

```python
# In ml/web_scraper.py, add a new method:
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
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ANTHROPIC_API_KEY not set` | Add key to `.env` file |
| Whisper slow on first use | Downloads model (~150MB) on first call — wait |
| FAISS import error | Run `pip install faiss-cpu` |
| CORS errors in browser | Ensure backend is on port 5000, Vite proxy is configured |
| PDF export fails | Run `pip install reportlab` |
| Voice input no permission | Use HTTPS in production (MediaRecorder requires secure context) |

---

## Disclaimer

ArthaAI provides general financial information and education. It is not a SEBI-registered investment advisor. Always verify information with official sources (RBI, SEBI, AMFI) and consult a qualified CA or financial advisor before making investment decisions. Investments are subject to market risks.

---

Built with ❤️ for Indian investors | Powered by Anthropic Claude + FAISS RAG
