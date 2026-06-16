# Ollive Deployment Guide

## Quick Deploy with Docker Compose

### Prerequisites
- Docker Engine 24+ and Docker Compose v2
- NVIDIA GPU + nvidia-container-toolkit (optional, for GPU-accelerated Ollama)

### One-Command Launch
```bash
cp .env.production .env
docker compose up -d
```

This starts three services:
- **ollive-ollama** (port 11434) — Local OSS model inference
- **ollive-backend** (port 8000) — FastAPI gateway + API
- **ollive-frontend** (port 3000) — Next.js chat UI

Verify health:
```bash
curl http://localhost:8000/api/v1/health
# → {"status":"ok","dependencies":{"database":"connected","ollama":"connected","frontier":"connected"}}
```

### Pull OSS Model (Optional)
```bash
docker exec ollive-ollama ollama pull Qwen/Qwen2.5-0.5B-Instruct
```

### View Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop & Cleanup
```bash
docker compose down
docker compose down -v   # also remove volumes (database + ollama models)
```

---

## Manual Deployment (Without Docker)

### Backend
```bash
python -m venv venv
source venv/bin/activate
pip install -e ./backend
cp .env.example .env
alembic upgrade head
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm run start
```

---

## Hugging Face Spaces Deployment

### Option A: Docker Space

1. Create a new Space on Hugging Face with the **Docker** SDK
2. Set `Dockerfile.space` as the Dockerfile
3. Add the following Secrets in Space Settings:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
   - `FRONTIER_MODEL`
   - `JUDGE_MODEL`
   - `LANGFUSE_PUBLIC_KEY` (optional)
   - `LANGFUSE_SECRET_KEY` (optional)

### Option B: Gradio Space (CPU-only)

1. Create a new Space with the **Gradio** SDK
2. Upload the repository
3. The Space auto-detects `requirements.txt` and runs `space_app.py`
4. On CPU: Qwen2.5-0.5B-Instruct runs at ~200-400ms per token
5. The Gradio UI provides chat, model selection, safety toggles, and cost display

---

## Render / Railway Deployment

### Backend (Web Service)
- **Build Command:** `pip install -e ./backend`
- **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** Set all keys from `.env.production`
- **Disk:** Mount a persistent disk at `/app/data` for SQLite

### Frontend (Static Site / Web Service)
- **Build Command:** `cd frontend && npm install && npm run build`
- **Start Command:** `cd frontend && node server.js`
- **Environment:** `NEXT_PUBLIC_API_URL` set to backend URL

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | — | API key for authenticating requests |
| `DATABASE_URL` | No | `sqlite:///./data/ollive.db` | SQLite or PostgreSQL connection string |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key (for frontier model + judge) |
| `GOOGLE_API_KEY` | No | — | Google AI API key (for Gemini models) |
| `FRONTIER_MODEL` | No | `gemini-2.5-flash` | Frontier model identifier |
| `OSS_MODEL_NAME` | No | `Qwen/Qwen2.5-0.5B-Instruct` | OSS model for Ollama |
| `OLLAMA_URL` | No | `http://ollama:11434` | Ollama server URL |
| `JUDGE_MODEL` | No | `gpt-4.1-mini` | Judge model for evaluations |
| `FRONTEND_URL` | No | `http://localhost:3000` | CORS allowed origin |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL for frontend |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse observability (optional) |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse observability (optional) |
| `SERPER_API_KEY` | No | — | Serper.dev API for web search |
| `E2B_API_KEY` | No | — | E2B sandbox for code execution |
