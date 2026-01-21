"""Manage copied positions in the database."""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

import db
from models import Position, Trade, TradeSide

logger = logging.getLogger(__name__)


class PositionManager:
    """Tracks copied positions in SQLite."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record_entry(self, trade: Trade, amount: float, entry_price: float) -> int:
        """
        Record a new position entry from copying a trade.

        Args:
            trade: The trade being copied
            amount: Amount in USDC we're trading
            entry_price: Price at which we entered

        Returns:
            Position ID
        """
        # Calculate position size based on amount and price
        size = amount / entry_price if entry_price > 0 else 0

        position = Position(
            id=None,
            market_id=trade.market_id,
            token_id=trade.token_id,
            side=trade.side,
            amount=size,
            entry_price=entry_price,
            outcome=trade.outcome,
            opened_at=datetime.utcnow(),
        )

        position_id = db.save_position(self.conn, position)
        logger.info(
            f"Recorded position entry: id={position_id}, "
            f"token={trade.token_id}, size={size:.4f}, price={entry_price:.4f}"
        )

        # Mark the trade as processed
        db.mark_trade_processed(self.conn, trade.trade_id)

        return position_id

    def record_exit(self, trade: Trade) -> bool:
        """
        Record a position exit from copying a sell trade.

        Args:
            trade: The sell trade being copied

        Returns:
            True if a position was closed, False otherwise
        """
        position = db.get_position_by_token(self.conn, trade.token_id)
        if position is None:
            logger.warning(
                f"No open position found for token {trade.token_id}, "
                "cannot record exit"
            )
            return False

        db.close_position(self.conn, position.id)
        logger.info(f"Closed position: id={position.id}, token={trade.token_id}")

        # Mark the trade as processed
        db.mark_trade_processed(self.conn, trade.trade_id)

        return True

    def has_position(self, token_id: str) -> bool:
        """Check if we have an open position for a token."""
        position = db.get_position_by_token(self.conn, token_id)
        return position is not None

    def get_position(self, token_id: str) -> Optional[Position]:
        """Get an open position by token ID."""
        return db.get_position_by_token(self.conn, token_id)

    def get_all_open_positions(self) -> list[Position]:
        """Get all open positions."""
        return db.get_open_positions(self.conn)

    def is_trade_processed(self, trade_id: str) -> bool:
        """Check if a trade has already been processed."""
        return db.is_trade_processed(self.conn, trade_id)

    def mark_processed(self, trade_id: str) -> None:
        """Mark a trade as processed without recording a position."""
        db.mark_trade_processed(self.conn, trade_id)
