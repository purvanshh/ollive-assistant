# Contributing to Ollive

Thank you for your interest in contributing! Ollive is an intelligent AI gateway that routes between local and frontier models with safety guardrails and automated evaluation.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/anomalyco/ollive-assistant/issues) to avoid duplicates
2. Use the bug report template when filing
3. Include: OS, Python/Node versions, steps to reproduce, expected vs actual behavior, relevant logs

### Suggesting Features

1. Open a feature request issue
2. Describe the problem your feature solves
3. Provide examples of how it would work
4. Indicate if you're willing to implement it

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `make test`
5. Run linting: `make lint`
6. Commit with descriptive messages
7. Push and open a PR against `main`

### PR Guidelines

- Keep PRs focused on a single change
- Include tests for new functionality
- Update documentation if you change user-facing behavior
- Ensure the build passes (backend tests + frontend TypeScript check)
- Link to the issue you're addressing

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 22+
- Ollama (for local model inference)
- Docker (optional, for containerized development)

### Quick Start

```bash
git clone https://github.com/anomalyco/ollive-assistant.git
cd ollive-assistant

python -m venv venv
source venv/bin/activate
pip install -e ./backend
cp .env.example .env

cd frontend && npm install && cd ..

make dev
```

### With Docker

```bash
cp .env.production .env
docker compose up -d
docker exec ollive-ollama ollama pull Qwen/Qwen2.5-0.5B-Instruct
```

## Project Structure

```
ollive-assistant/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routers/      # API route modules
│   │   ├── repositories/ # Data access layer
│   │   ├── models.py     # SQLAlchemy ORM models
│   │   └── main.py       # App factory
│   └── migrations/       # Alembic migrations
├── frontend/             # Next.js 16 frontend
│   └── src/
│       ├── app/          # App router pages
│       ├── components/   # Reusable UI components
│       └── contexts/     # React contexts
├── evaluation/           # Evaluation suite
│   ├── suites/v1.0/     # 200-prompt benchmark
│   ├── run_eval.py      # CLI + API-callable runner
│   └── judge.py         # GPT-4.1 judge
├── oss_assistant/        # OSS model wrapper (Ollama)
├── frontier_assistant/   # Frontier model wrapper (OpenAI/Gemini)
├── guardrails/           # Llama Guard 3 safety layer
└── docs/                 # ADRs and documentation
```

## Conventions

### Python
- Follow [PEP 8](https://peps.python.org/pep-0008/) with 88-character line limit (Ruff)
- Type hints required for all function signatures
- Use `pathlib.Path` for file paths, not `os.path`
- Structured JSON logging with request ID correlation

### TypeScript/React
- Use functional components with hooks
- Client components run with `"use client"` directive
- Type all props and state
- Use shadcn/ui components from `@/components/ui/`

### Git Commits
- Use present tense ("Add feature" not "Added feature")
- Reference issue numbers when applicable
- Keep first line under 72 characters

## Testing

```bash
# Backend tests
make test

# Frontend type check
cd frontend && npx tsc --noEmit

# Pre-commit hooks
pre-commit run --all-files
```

## Getting Help

- Open a [GitHub Discussion](https://github.com/anomalyco/ollive-assistant/discussions)
- Tag maintainers with `@ollive-team` for urgent issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
