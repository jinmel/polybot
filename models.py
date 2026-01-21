"""Data models for Polybot."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TradeSide(Enum):
    """Trade direction."""

    BUY = "BUY"
    SELL = "SELL"


class TradeType(Enum):
    """Type of trade action."""

    OPEN = "OPEN"
    CLOSE = "CLOSE"


@dataclass
class Trade:
    """Represents a trade from the target user."""

    trade_id: str
    market_id: str
    token_id: str
    side: TradeSide
    size: float
    price: float
    timestamp: datetime
    outcome: str  # YES or NO

    @property
    def is_buy(self) -> bool:
        return self.side == TradeSide.BUY

    @property
    def is_sell(self) -> bool:
        return self.side == TradeSide.SELL


@dataclass
class Position:
    """Represents a copied position."""

    id: Optional[int]
    market_id: str
    token_id: str
    side: TradeSide
    amount: float
    entry_price: float
    opened_at: datetime
    closed_at: Optional[datetime] = None
    outcome: str = ""

    @property
    def is_open(self) -> bool:
        return self.closed_at is None


@dataclass
class ProcessedTrade:
    """Record of a processed trade from the target user."""

    trade_id: str
    processed_at: datetime
