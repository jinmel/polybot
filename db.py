"""SQLite database layer for Polybot."""

import sqlite3
from datetime import datetime
from typing import Optional

from models import Position, ProcessedTrade, TradeSide


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id TEXT NOT NULL,
            token_id TEXT NOT NULL,
            side TEXT NOT NULL,
            amount REAL NOT NULL,
            entry_price REAL NOT NULL,
            outcome TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_trades (
            trade_id TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def save_position(conn: sqlite3.Connection, position: Position) -> int:
    """Save a new position to the database. Returns the position ID."""
    cursor = conn.execute(
        """
        INSERT INTO positions (market_id, token_id, side, amount, entry_price, outcome, opened_at, closed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            position.market_id,
            position.token_id,
            position.side.value,
            position.amount,
            position.entry_price,
            position.outcome,
            position.opened_at.isoformat(),
            position.closed_at.isoformat() if position.closed_at else None,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_open_positions(conn: sqlite3.Connection) -> list[Position]:
    """Get all open positions."""
    cursor = conn.execute(
        "SELECT * FROM positions WHERE closed_at IS NULL"
    )
    rows = cursor.fetchall()
    return [_row_to_position(row) for row in rows]


def get_position_by_token(
    conn: sqlite3.Connection, token_id: str
) -> Optional[Position]:
    """Get an open position by token ID."""
    cursor = conn.execute(
        "SELECT * FROM positions WHERE token_id = ? AND closed_at IS NULL",
        (token_id,),
    )
    row = cursor.fetchone()
    return _row_to_position(row) if row else None


def close_position(conn: sqlite3.Connection, position_id: int) -> None:
    """Mark a position as closed."""
    conn.execute(
        "UPDATE positions SET closed_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), position_id),
    )
    conn.commit()


def is_trade_processed(conn: sqlite3.Connection, trade_id: str) -> bool:
    """Check if a trade has already been processed."""
    cursor = conn.execute(
        "SELECT 1 FROM processed_trades WHERE trade_id = ?",
        (trade_id,),
    )
    return cursor.fetchone() is not None


def mark_trade_processed(conn: sqlite3.Connection, trade_id: str) -> None:
    """Mark a trade as processed."""
    conn.execute(
        "INSERT OR IGNORE INTO processed_trades (trade_id, processed_at) VALUES (?, ?)",
        (trade_id, datetime.utcnow().isoformat()),
    )
    conn.commit()


def get_last_processed_trade(conn: sqlite3.Connection) -> Optional[ProcessedTrade]:
    """Get the most recently processed trade."""
    cursor = conn.execute(
        "SELECT * FROM processed_trades ORDER BY processed_at DESC LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        return ProcessedTrade(
            trade_id=row["trade_id"],
            processed_at=datetime.fromisoformat(row["processed_at"]),
        )
    return None


def _row_to_position(row: sqlite3.Row) -> Position:
    """Convert a database row to a Position object."""
    return Position(
        id=row["id"],
        market_id=row["market_id"],
        token_id=row["token_id"],
        side=TradeSide(row["side"]),
        amount=row["amount"],
        entry_price=row["entry_price"],
        outcome=row["outcome"],
        opened_at=datetime.fromisoformat(row["opened_at"]),
        closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
    )
