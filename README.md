# 🌾 PestGuard AI — Deep Learning Insect Pest Recognition System

> **Department 2 Backend** · Capstone Project — Bahçeşehir University, AI Engineering · 2026  
> **Stage 5** — Docker Containerization & Full Deployment

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PestGuard AI System                      │
├──────────────┬──────────────┬───────────────┬───────────────┤
│  🔬 D3       │  🧠 D2       │  👁️ D1        │  🌤️ External  │
│  CNN Model   │  RAG + LLM   │  Grad-CAM     │  Open-Meteo   │
│  (IP-102)    │  Agent       │  XAI Engine   │  Weather API  │
│  [pending]   │  [active]    │  [pending]    │  [active]     │
└──────┬───────┴──────┬───────┴───────┬───────┴───────┬───────┘
       │              │               │               │
       └──────────────┴───────────────┴───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   FastAPI Backend  │
                    │   Port 8000       │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Dasher Frontend   │
                    │  /app endpoint     │
                    └───────────────────┘
```

## 🚀 Quick Start

### Option A: Docker (Recommended)
```bash
# 1. Clone and navigate
cd capstone-dept2

# 2. Set your API keys
cp backend/.env.example backend/.env
# Edit .env with your GOOGLE_API_KEY and GROQ_API_KEY

# 3. Build and run
docker-compose up --build

# 4. Open browser
# Dashboard: http://localhost:8000/app
# Swagger:   http://localhost:8000/docs
```

### Option B: Local Development
```bash
# 1. Navigate to backend
cd capstone-dept2/backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API keys
cp .env.example .env
# Edit .env with your keys

# 5. Download RAG documents & build index
python rag/download_documents.py
python rag/build_index.py

# 6. Run the server
python main.py
```

Then open: **http://localhost:8000/app** (Dashboard) or **http://localhost:8000/docs** (Swagger)

---

## 📡 API Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/` | Health check + system status | ✅ Live |
| `POST` | `/predict` | Upload image → pest classification | ✅ Mock + VLM |
| `POST` | `/chat` | RAG-powered pest management advisor | ✅ Live |
| `GET` | `/weather/{lat}/{lon}` | Real weather + spray safety | ✅ Live |
| `GET` | `/heatmap` | Get outbreak heatmap data | ✅ Live |
| `POST` | `/heatmap/report` | Submit anonymized pest report | ✅ Live |
| `GET` | `/app` | Frontend dashboard | ✅ Live |
| `GET` | `/docs` | Swagger API documentation | ✅ Auto |

---

## 📂 Project Structure

```
capstone-dept2/
├── docker-compose.yml          ← One-command deployment
├── README.md                   ← This file
│
├── backend/
│   ├── Dockerfile              ← Multi-stage production image
│   ├── .dockerignore
│   ├── main.py                 ← FastAPI entry point (23KB, 439 lines)
│   ├── mock_api.py             ← D3/D1 mock responses (swap point)
│   ├── requirements.txt        ← 12 Python packages
│   ├── .env.example            ← API key template
│   │
│   ├── agent/                  ← LLM Chatbot (Stage 2)
│   │   ├── chatbot.py          ← RAG + multi-LLM agent
│   │   └── prompts.py          ← Prompt templates
│   │
│   ├── rag/                    ← RAG Pipeline (Stage 2)
│   │   ├── download_documents.py  ← Fetches 20+ PDFs
│   │   ├── build_index.py      ← ChromaDB vector index
│   │   └── retriever.py        ← Semantic retrieval
│   │
│   ├── vlm/                    ← Vision-Language Model (Stage 3)
│   │   └── describe.py         ← Gemini/Groq vision
│   │
│   ├── weather/                ← Weather Service (Stage 3)
│   │   └── service.py          ← Open-Meteo + FAO spray safety
│   │
│   ├── core/                   ← Utilities (Stage 5)
│   │   ├── logger.py           ← Structured logging
│   │   ├── retry.py            ← Auto-retry with backoff
│   │   └── validators.py       ← Input validation
│   │
│   ├── static/                 ← Frontend (Stage 4)
│   │   ├── index.html          ← Dasher-based SPA dashboard
│   │   ├── css/                ← Theme + custom styles
│   │   └── js/                 ← Dashboard logic
│   │
│   ├── data/
│   │   ├── documents/          ← RAG source PDFs
│   │   └── chroma_db/          ← Vector index (auto-built)
│   │
│   └── tests/
│       ├── test_all.py         ← 60-test comprehensive suite
│       └── test_results.json   ← Last test run output
│
└── dasher-1.0.0/               ← Dasher template source (reference)
```

---

## 🔬 Testing

```bash
# Start server first
python main.py

# Run full 60-test suite (in another terminal)
python tests/test_all.py
```

### Test Categories (60 tests)

| Category | Tests | Coverage |
|----------|-------|----------|
| System & Health | T01–T05 | API status, stage, VLM, weather |
| Prediction Pipeline | T06–T12 | Upload, validation, confidence |
| VLM Vision Engine | T13–T18 | Description, pre-filter, formats |
| RAG + LLM Chatbot | T19–T28 | Chat, sources, sessions, context |
| Weather & Spray Safety | T29–T36 | FAO thresholds, multi-location |
| Heatmap & Outbreak | T37–T42 | CRUD, anonymization, dedup |
| Failover & Resilience | T43–T48 | Degradation, CORS, failover |
| Edge Cases & Security | T49–T55 | XSS, SQLi, PII, Swagger |
| Performance & Load | T56–T60 | Latency benchmarks |

---

## 🐳 Docker

### Build & Run
```bash
docker-compose up --build      # Build + start
docker-compose up -d           # Background mode
docker-compose down            # Stop all
docker-compose logs -f api     # Follow logs
```

### Image Details
- **Base:** `python:3.11-slim` (multi-stage)
- **Size:** ~800MB (with ML dependencies)
- **Security:** Non-root user (`pestguard`)
- **Health check:** Every 30s on `/`
- **Volumes:** uploads, data, logs persisted

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Google Gemini API key (free at aistudio.google.com) |
| `GROQ_API_KEY` | ✅ | Groq API key (free at console.groq.com) |
| `OPENWEATHER_API_KEY` | ❌ | Optional (Open-Meteo used by default, no key needed) |

---

## 🔄 Mock → Real Swap Points

When D1/D3 deliver their APIs:

| File | Function | Replace With |
|------|----------|--------------|
| `mock_api.py` | `get_prediction()` | HTTP call to D3's CNN inference endpoint |
| `mock_api.py` | `get_gradcam()` | HTTP call to D1's Grad-CAM XAI endpoint |

---

## 📋 Development Stages

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Foundation — Mock API + Project Structure | ✅ Complete |
| 2 | RAG Brain — ChromaDB + LLM Agent (Gemini/Groq) | ✅ Complete |
| 3 | VLM + Weather — Vision analysis + spray safety | ✅ Complete |
| 4 | Frontend — Dasher dashboard + full SPA | ✅ Complete |
| 5 | Docker — Containerization + testing + docs | ✅ Complete |

---

## 👥 Team

- **Department 2** — Integration, RAG, LLM, Frontend, Deployment
- **Department 1** — Grad-CAM / XAI Engine (pending integration)
- **Department 3** — CNN Classification Model on IP-102 (pending integration)

---

*© 2026 PestGuard AI — Department 2 Capstone · BAU*
