from prometheus_client import Counter, Histogram, Gauge
from backend.app.database import SessionLocal
from backend.app.models import Conversation

# Counters
REQUEST_COUNT = Counter(
    "ollive_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"]
)

# Histograms
REQUEST_LATENCY = Histogram(
    "ollive_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

def get_conversation_count() -> float:
    """Callback to query active conversation count from the database."""
    db = SessionLocal()
    try:
        count = db.query(Conversation).count()
        return float(count)
    except Exception:
        return 0.0
    finally:
        db.close()

# Gauges
ACTIVE_CONVERSATIONS = Gauge(
    "ollive_active_conversations",
    "Total active conversations in the database"
)
ACTIVE_CONVERSATIONS.set_function(get_conversation_count)
