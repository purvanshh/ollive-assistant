.PHONY: dev dev-backend dev-frontend install-all clean

install-all:
	./venv/bin/pip install -e ./backend
	cd frontend && npm install

dev:
	@echo "Starting backend (port 8000) and frontend (port 3000)..."
	@make -j 2 dev-backend dev-frontend

dev-backend:
	PYTHONPATH=./backend ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
