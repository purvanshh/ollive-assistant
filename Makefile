.PHONY: dev dev-backend dev-frontend install-all clean \
        docker-build docker-up docker-down docker-logs \
        test lint db-migrate db-upgrade

install-all:
	./venv/bin/pip install -e ./backend
	cd frontend && npm install

dev:
	@echo "Starting backend (port 8000) and frontend (port 3000)..."
	@make -j 2 dev-backend dev-frontend

dev-backend:
	PYTHONPATH=./backend ./venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-pull-oss:
	docker exec ollive-ollama ollama pull Qwen/Qwen2.5-0.5B-Instruct

test:
	cd backend && PYTHONPATH=.. ./../venv/bin/python -m pytest tests/ -v

lint:
	./venv/bin/ruff check backend/ evaluation/ oss_assistant/ frontier_assistant/ guardrails/ shared/

db-migrate:
	cd backend && PYTHONPATH=. ./../venv/bin/alembic revision --autogenerate -m "auto_migration"

db-upgrade:
	cd backend && PYTHONPATH=. ./../venv/bin/alembic upgrade head
