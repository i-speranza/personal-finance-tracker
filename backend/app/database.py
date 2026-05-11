"""Database connection and session management."""
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Database path - relative to project root
default_db_path = Path(__file__).parent.parent.parent / "data" / "finance.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# Ensure data directory exists
if "sqlite" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def apply_sqlite_light_migrations() -> None:
    """Add columns missing on older SQLite files (create_all does not ALTER)."""
    if "sqlite" not in DATABASE_URL:
        return
    try:
        with engine.begin() as conn:
            r = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='investment_portfolio_assets'")
            ).fetchone()
            if r:
                cols = {row[1] for row in conn.execute(text("PRAGMA table_info(investment_portfolio_assets)")).fetchall()}
                if "broker" not in cols:
                    conn.execute(text("ALTER TABLE investment_portfolio_assets ADD COLUMN broker VARCHAR"))
                    logger.info("SQLite: added column investment_portfolio_assets.broker")

            tx = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='investment_portfolio_transactions'")
            ).fetchone()
            if tx:
                tx_cols = {
                    row[1] for row in conn.execute(text("PRAGMA table_info(investment_portfolio_transactions)")).fetchall()
                }
                if "plus_minus_manual" in tx_cols:
                    conn.execute(text("ALTER TABLE investment_portfolio_transactions DROP COLUMN plus_minus_manual"))
                    logger.info(
                        "SQLite: dropped legacy column investment_portfolio_transactions.plus_minus_manual"
                    )
    except Exception:  # noqa: BLE001
        logger.exception("SQLite light migration failed")


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
