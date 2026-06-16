# Ollive Roadmap

## Current Status: v1.0.0 (June 2026)

All 20 implementation phases complete. Core features operational:
- Local + Frontier model routing
- Streaming SSE chat with conversation memory
- Llama Guard 3 safety guardrails
- Web search + code execution tools
- File parsing (PDF, CSV, TXT)
- 200-prompt evaluation suite with blind GPT-4.1 judge
- Admin dashboard with cost tracking and audit logs
- Docker Compose production deployment
- Evaluation dashboard with charts and comparison views

---

## Short-Term (1-3 months)

### Q3 2026

| Feature | Priority | Description |
|---------|----------|-------------|
| **User Authentication** | P0 | JWT-based auth with user registration, replacing single API key |
| **Conversation Search** | P1 | Semantic search across conversation history using sqlite-vec |
| **Multimodal Input** | P1 | Image upload + vision model support for Gemini/GPT-4o |
| **PostgreSQL Support** | P1 | Production database with connection pooling |
| **Redis Caching** | P1 | Session management, rate limiting, and response caching |
| **Export Conversations** | P2 | Markdown/PDF export of chat history |
| **Custom System Prompts** | P2 | User-configurable system prompts per conversation |
| **Model Fine-Tuning Feedback** | P2 | Use thumbs up/down data to fine-tune routing heuristics |

---

## Medium-Term (3-6 months)

### Q4 2026

| Feature | Priority | Description |
|---------|----------|-------------|
| **Multi-Tenant Support** | P1 | Organization workspaces with role-based access control |
| **Hard Budget Caps** | P1 | Per-user spending limits with automatic cutoff |
| **CI/CD Evaluation Pipeline** | P1 | GitHub Actions workflow runs eval suite on PRs, posts comparison |
| **Model Playground** | P2 | Side-by-side model comparison in UI (not just eval suite) |
| **RAG Pipeline** | P2 | Document ingestion + chunking + retrieval for long documents |
| **Plugin System** | P2 | Community-contributed tools (weather, stocks, calendar, etc.) |
| **Mobile PWA** | P2 | Progressive Web App with offline OSS chat capability |
| **Langfuse Dashboard** | P2 | Integrated observability with trace viewer |

---

## Long-Term (6-12 months)

### 2026-2027

| Feature | Priority | Description |
|---------|----------|-------------|
| **On-Premise Deployment Guide** | P1 | Enterprise deployment with Vault secrets, audit compliance |
| **Model A/B Testing Framework** | P1 | Canary deployments for new models with automatic rollback |
| **Custom Guardrail Policies** | P2 | Organization-specific safety policies beyond MLCommons taxonomy |
| **Federated Evaluation** | P2 | Privacy-preserving eval across deployments without sharing data |
| **Agent Framework** | P2 | Multi-step autonomous agents with planning, tools, and memory |
| **API Marketplace** | P3 | Monetized tool/plugin marketplace for third-party integrations |
| **SOC 2 Compliance** | P3 | Formal security certification for enterprise sales |

---

## Completed (v1.0.0)

| Phase | Status | Description |
|-------|--------|-------------|
| 1-4 | ✅ | Project scaffolding, database, API foundation, health checks |
| 5-7 | ✅ | OSS model (Ollama), frontier model (Gemini), streaming SSE |
| 8 | ✅ | Conversation memory & persistence |
| 9-10 | ✅ | Guardrail layer (Llama Guard 3), query router |
| 11 | ✅ | Cost transparency & user model override |
| 12-14 | ✅ | Web search, code execution (E2B), file parsing |
| 15-17 | ✅ | Evaluation suite, blind judge, reporting & visualization |
| 18 | ✅ | Admin dashboard & human feedback loop |
| 19 | ✅ | Docker Compose production deployment |
| 20 | ✅ | Documentation, ADRs, community launch |

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:
- Bug fixes and performance improvements
- New tools and integrations
- Evaluation prompt contributions
- Documentation improvements
- Community model adapters

Priority is guided by community feedback — open an issue to propose features or upvote existing ones.
