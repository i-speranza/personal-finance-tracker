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


def apply_sqlite_light_migrations() -> bool:
    """Add columns / tables missing on older SQLite files (create_all does not ALTER).

    Returns True if `average_unit_cost_after_trade` was added to portfolio transactions this run
    (caller should run cost-basis backfill).
    """
    if "sqlite" not in DATABASE_URL:
        return False
    added_average_cost_column = False
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
                if "average_unit_cost_after_trade" not in tx_cols:
                    conn.execute(
                        text(
                            "ALTER TABLE investment_portfolio_transactions "
                            "ADD COLUMN average_unit_cost_after_trade FLOAT"
                        )
                    )
                    logger.info(
                        "SQLite: added column investment_portfolio_transactions.average_unit_cost_after_trade"
                    )
                    added_average_cost_column = True

            mq = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name='investment_portfolio_market_quotes'"
                )
            ).fetchone()
            if not mq:
                conn.execute(
                    text(
                        """
                        CREATE TABLE investment_portfolio_market_quotes (
                            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                            as_of_date DATE NOT NULL,
                            asset_pk INTEGER NOT NULL,
                            market_unit_price FLOAT NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(asset_pk) REFERENCES investment_portfolio_assets (id)
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_inv_portfolio_market_quote_date_asset "
                        "ON investment_portfolio_market_quotes (as_of_date, asset_pk)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_inv_portfolio_market_quotes_as_of_date "
                        "ON investment_portfolio_market_quotes (as_of_date)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_inv_portfolio_market_quotes_asset_pk "
                        "ON investment_portfolio_market_quotes (asset_pk)"
                    )
                )
                logger.info("SQLite: created table investment_portfolio_market_quotes")
    except Exception:  # noqa: BLE001
        logger.exception("SQLite light migration failed")
    return added_average_cost_column


def backfill_investment_average_unit_costs() -> None:
    """Populate average_unit_cost_after_trade for all assets (e.g. after SQLite adds the column)."""
    try:
        from .investment_cost_basis import recalculate_average_unit_costs_for_all_assets

        db = SessionLocal()
        try:
            recalculate_average_unit_costs_for_all_assets(db)
            db.commit()
            logger.info("SQLite: backfilled investment_portfolio_transactions.average_unit_cost_after_trade")
        finally:
            db.close()
    except Exception:  # noqa: BLE001
        logger.exception("SQLite: backfill average_unit_cost_after_trade failed")


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
