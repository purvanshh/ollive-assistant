---
title: Ollive OSS Assistant
emoji: 🫒
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.15.0
app_file: space_app.py
pinned: false
license: mit
---

# 🫒 Ollive — Intelligent AI Gateway

**Local-First. Safety-Bound. Cost-Aware.**

Ollive is an open-source intelligent AI gateway that routes queries between local open-source models and frontier cloud APIs — with local safety guardrails, automated evaluation, and real-time cost tracking.

---

## Why Ollive?

| Problem | Ollive's Solution |
|---------|-------------------|
| Frontier APIs are expensive for simple queries | Routes simple queries to free local OSS models |
| Local models can't handle complex reasoning | Routes complex queries to GPT-4.1 / Gemini 2.5 Flash |
| AI safety requires sending data to third parties | Llama Guard 3 runs entirely locally for content checks |
| No way to compare model quality objectively | Built-in 200-prompt evaluation suite with blind GPT-4.1 judge |
| API costs are unpredictable | Real-time per-message cost display + daily budget tracking |

---

## Architecture

```
User → Frontend (Next.js) → Backend (FastAPI)
                               ├── Guardrail (Llama Guard 3)
                               ├── Router (Heuristic Classifier)
                               ├── OSS Model (Qwen via Ollama)
                               └── Frontier Model (Gemini / GPT-4.1)
                                     ├── Web Search Tool (Serper)
                                     ├── Code Execution (E2B Sandbox)
                                     └── File Parser (PDF, CSV, TXT)
```

**Evaluation Pipeline:**
```
200 Prompts → Model A + Model B → Blind GPT-4.1 Judge → Scores + A/B Comparison → Charts + Reports
```

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/anomalyco/ollive-assistant.git
cd ollive-assistant
cp .env.production .env
# Edit .env with your API keys
docker compose up -d
docker exec ollive-ollama ollama pull Qwen/Qwen2.5-0.5B-Instruct
```

Open **http://localhost:3000** — Chat, **/eval** — Evaluation Dashboard, **/admin** — Admin Dashboard.

### Manual

```bash
python -m venv venv
source venv/bin/activate
pip install -e ./backend
cp .env.example .env
make db-upgrade
make dev
```

---

## Features

### Core Chat
- **Streaming SSE** — Real-time token-by-token response delivery
- **Conversation Memory** — Full history persisted in SQLite with auto-generated titles
- **Multi-Model** — Seamless switching between local OSS and frontier cloud models
- **File Upload** — Parse PDF, CSV, and TXT files with PII redaction

### Intelligent Routing
- **Heuristic Classifier** — Routes simple queries to OSS (free), complex queries to Frontier (paid)
- **Model Override** — User can force OSS or Frontier per message
- **Routing Transparency** — Reason displayed in chat ("Routed to Gemini: detected coding intent")

### Safety & Guardrails
- **Llama Guard 3 (1B)** — Local content safety check covering 14 harm categories
- **<300ms Latency** — Safety checks add minimal overhead
- **Audit Logs** — All blocked prompts logged with reason codes
- **Keyword Fallback** — Pattern-based filtering when guard model is unavailable

### Tools
- **Web Search** — Serper.dev API integration with source citations
- **Code Execution** — E2B sandbox for Python with 30s timeout
- **Calculator** — Deterministic math via Python `eval` in sandbox

### Evaluation Suite
- **200 Prompts** — 6 dimensions: factual accuracy, safety adversarial, reasoning, coding, bias, multimodal
- **Blind Judge** — GPT-4.1 scores responses without knowing which model produced them
- **Per-Dimension Scoring** — 1-5 rubrics for factual accuracy, bias, refusal appropriateness
- **A/B Comparison** — Direct head-to-head with reasoning
- **Dashboard** — Bar charts, pie charts, radar charts, detailed score tables

### Observability & Admin
- **Admin Dashboard** — 7-day cost trends, model usage distribution, guardrail block rate, audit logs
- **Cost Tracking** — Per-message cost display + daily budget warning at $1.00
- **User Feedback** — Thumbs up/down on every assistant message
- **Prometheus Metrics** — Request count, latency histograms, active conversations
- **Structured Logging** — JSON logs with request ID correlation

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check (DB, Ollama, Frontier status) |
| `POST` | `/api/v1/conversations` | Create conversation |
| `GET` | `/api/v1/conversations` | List user conversations |
| `DELETE` | `/api/v1/conversations/{id}` | Delete conversation |
| `POST` | `/api/v1/chat` | SSE-streaming chat completion |
| `POST` | `/api/v1/files/upload` | Upload & parse file (PDF/CSV/TXT) |
| `POST` | `/api/v1/feedback` | Submit thumbs up/down on message |
| `POST` | `/api/v1/evaluations/runs` | Trigger evaluation run |
| `GET` | `/api/v1/evaluations/runs` | List evaluation runs |
| `GET` | `/api/v1/evaluations/runs/{id}/stats` | Aggregated run statistics |
| `GET` | `/api/v1/evaluations/stats` | Cross-run overall stats |
| `GET` | `/api/v1/admin/dashboard` | Admin dashboard with charts |
| `GET` | `/api/v1/admin/audit-logs` | Security audit log viewer |
| `GET` | `/metrics` | Prometheus metrics |

Full OpenAPI docs at **http://localhost:8000/docs**.

---

## Configuration

Copy `.env.example` to `.env` and set:

```bash
API_KEY=your-secure-api-key
OPENAI_API_KEY=sk-...          # Required for frontier model + judge
GOOGLE_API_KEY=...              # Required for Gemini models
FRONTIER_MODEL=gemini-2.5-flash # or gpt-4.1
OSS_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
JUDGE_MODEL=gpt-4.1-mini
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full production deployment guide and all configuration options.

---

## Evaluation Guide

### Running Evaluations

**Via CLI:**
```bash
python -m evaluation.run_eval --model-a oss --model-b frontier --run-type full
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/evaluations/runs \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"run_type": "smoke", "judge_model": "gpt-4.1-mini"}'
```

### Viewing Results

1. **Web Dashboard:** Navigate to `/eval` in the frontend for charts and comparison tables
2. **CLI Report:** `python -m evaluation.report` generates `comparison.png`
3. **Cost Analysis:** `python -m evaluation.cost_analysis` generates `cost_latency_table.md`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, Alembic, SQLite + sqlite-vec |
| Frontend | Next.js 16, React 19, Tailwind CSS, shadcn/ui, Recharts |
| OSS Models | Ollama (Qwen2.5-0.5B-Instruct) |
| Frontier APIs | OpenAI GPT-4.1, Google Gemini 2.5 Flash |
| Safety | Llama Guard 3 (1B) via Ollama |
| Evaluation | GPT-4.1-mini judge, 200-prompt benchmark suite |
| Observability | Prometheus, Langfuse, structured JSON logging |
| Deployment | Docker Compose, Hugging Face Spaces |

---

## Project Structure

```
ollive-assistant/
├── backend/              # FastAPI backend (routes, models, repositories)
├── frontend/             # Next.js 16 frontend (chat, eval, admin)
├── evaluation/           # Judge, runner, reports, 200-prompt benchmark
├── oss_assistant/        # OSS model wrapper (Ollama)
├── frontier_assistant/   # Frontier model wrapper (OpenAI/Gemini)
├── guardrails/           # Llama Guard 3 safety layer
├── shared/               # Langfuse observability wrapper
├── docs/adr/             # Architecture Decision Records
├── docker-compose.yml    # Full-stack Docker deployment
├── DEPLOYMENT.md         # Production deployment guide
├── ROADMAP.md            # Future development plans
└── CONTRIBUTING.md       # Contributor guidelines
```

---

## Architecture Decisions

See [docs/adr/](docs/adr/) for detailed Architecture Decision Records:

- [ADR 001](docs/adr/001-routing-strategy.md) — Heuristic keyword-based model routing
- [ADR 002](docs/adr/002-guardrail-architecture.md) — Local Llama Guard 3 with keyword fallback
- [ADR 003](docs/adr/003-judge-blindness.md) — Strictly blind GPT-4.1 A/B comparison
- [ADR 004](docs/adr/004-cost-tracking.md) — Per-message cost + daily budget tracking

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, conventions, and PR guidelines.

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

---

## License

MIT © 2026 Ollive Contributors

---

## Acknowledgments

- [MLCommons](https://mlcommons.org/) for the AI safety taxonomy
- [Ollama](https://ollama.com/) for local model serving
- [Qwen](https://github.com/QwenLM/Qwen2.5) for the open-source model
- [Llama Guard 3](https://ai.meta.com/blog/llama-guard-3/) for safety classification
- [sqlite-vec](https://github.com/asg017/sqlite-vec) for embedded vector search
