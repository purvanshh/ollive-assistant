import os
import sys
import uuid
import time
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

# Setup logging config
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ollive")

from backend.app.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize vector search virtual tables
    logger.info(json.dumps({"event": "startup", "status": "initializing_vector_table"}))
    from backend.app.database import SessionLocal
    from backend.app.repositories.message import MessageRepository
    db = SessionLocal()
    try:
        MessageRepository.init_vector_table(db)
        logger.info(json.dumps({"event": "startup", "status": "vector_table_initialized"}))
    except Exception as e:
        logger.error(json.dumps({"event": "startup", "status": "vector_table_failed", "error": str(e)}))
    finally:
        db.close()
    yield
    # Shutdown logic (none needed)

app = FastAPI(
    title="Ollive Intelligent AI Gateway",
    description="Intelligent API routing, local guardrails, tool use, and automated evaluation.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handler for Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured JSON Logging + X-Request-ID Middleware
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    start_time = time.perf_counter()
    status_code = 500
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        process_time = (time.perf_counter() - start_time) * 1000
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host if request.client else "unknown",
            "status_code": status_code,
            "latency_ms": round(process_time, 2)
        }
        logger.info(json.dumps(log_data))
        
        response.headers["X-Request-ID"] = request_id
        
        # Record Prometheus metrics
        path = request.url.path
        if path != "/metrics":
            from backend.app.metrics import REQUEST_COUNT, REQUEST_LATENCY
            REQUEST_COUNT.labels(method=request.method, endpoint=path, status_code=str(status_code)).inc()
            REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(process_time / 1000.0)
            
        return response
    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host if request.client else "unknown",
            "status_code": 500,
            "latency_ms": round(process_time, 2),
            "error": str(e)
        }
        logger.error(json.dumps(log_data))
        
        # Record Prometheus metrics
        path = request.url.path
        if path != "/metrics":
            from backend.app.metrics import REQUEST_COUNT, REQUEST_LATENCY
            REQUEST_COUNT.labels(method=request.method, endpoint=path, status_code="500").inc()
            REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(process_time / 1000.0)
            
        raise e

# Include Routers
from backend.app.routers import health, conversations, chat, evaluations
app.include_router(health.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")

# Mount Prometheus metrics endpoint
from prometheus_client import make_asgi_app
app.mount("/metrics", make_asgi_app())

@app.get("/")
def read_root():
    return {"message": "Welcome to Ollive Intelligent AI Gateway API. Visit /docs for OpenAPI documentation."}
