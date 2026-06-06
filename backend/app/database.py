import os
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ollive.db")

# Setup event listener for SQLite to load sqlite-vec
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite-specific connect args
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    
    @event.listens_for(Engine, "connect")
    def load_sqlite_extensions(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            try:
                import sqlite_vec
                dbapi_connection.enable_load_extension(True)
                sqlite_vec.load(dbapi_connection)
                dbapi_connection.enable_load_extension(False)
            except Exception as e:
                # Fallback silent fail if sqlite-vec cannot be loaded
                print(f"Warning: Failed to load sqlite-vec extension: {e}")
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injection helper for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
