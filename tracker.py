"""Track target user's trading activity on Polymarket."""

import logging
from datetime import datetime
from typing import Optional

import requests

from models import Trade, TradeSide

logger = logging.getLogger(__name__)


class Tracker:
    """Polls the Polymarket Data API to detect new trades from a target user."""

    def __init__(self, data_api_url: str, target_address: str):
        self.data_api_url = data_api_url.rstrip("/")
        self.target_address = target_address.lower()
        self.last_seen_timestamp: Optional[datetime] = None

    def get_new_trades(self) -> list[Trade]:
        """
        Fetch recent trades from the target user.
        Returns only trades newer than the last seen timestamp.
        """
        try:
            trades = self._fetch_activity()
            new_trades = self._filter_new_trades(trades)

            if new_trades:
                # Update last seen timestamp to the most recent trade
                self.last_seen_timestamp = max(t.timestamp for t in new_trades)
                logger.info(f"Found {len(new_trades)} new trades")

            return new_trades
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []

    def _fetch_activity(self) -> list[Trade]:
        """Fetch trading activity from the Data API."""
        url = f"{self.data_api_url}/activity"
        params = {"user": self.target_address}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        trades = []

        for item in data:
            # Filter for TRADE activity type
            if item.get("type") != "TRADE":
                continue

            trade = self._parse_trade(item)
            if trade:
                trades.append(trade)

        return trades

    def _parse_trade(self, item: dict) -> Optional[Trade]:
        """Parse a trade from the API response."""
        try:
            # Parse timestamp - handle different formats
            timestamp_str = item.get("timestamp") or item.get("createdAt")
            if timestamp_str:
                # Handle ISO format with or without Z suffix
                timestamp_str = timestamp_str.replace("Z", "+00:00")
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.utcnow()

            side_str = item.get("side", "").upper()
            side = TradeSide.BUY if side_str == "BUY" else TradeSide.SELL

            return Trade(
                trade_id=str(item.get("id", item.get("transactionHash", ""))),
                market_id=item.get("conditionId", item.get("marketId", "")),
                token_id=item.get("assetId", item.get("tokenId", "")),
                side=side,
                size=float(item.get("size", 0)),
                price=float(item.get("price", 0)),
                timestamp=timestamp,
                outcome=item.get("outcome", item.get("title", "YES")),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse trade: {e}, item: {item}")
            return None

    def _filter_new_trades(self, trades: list[Trade]) -> list[Trade]:
        """Filter trades to only include those newer than last seen."""
        if self.last_seen_timestamp is None:
            # First run - don't process any existing trades
            # Just record the most recent timestamp
            if trades:
                self.last_seen_timestamp = max(t.timestamp for t in trades)
                logger.info(
                    f"Initial sync: found {len(trades)} existing trades, "
                    f"will track new trades from {self.last_seen_timestamp}"
                )
            return []

        # Return only trades newer than last seen
        new_trades = [
            t for t in trades
            if t.timestamp > self.last_seen_timestamp
        ]

        # Sort by timestamp ascending (oldest first)
        new_trades.sort(key=lambda t: t.timestamp)
        return new_trades

    def set_last_seen(self, timestamp: datetime) -> None:
        """Set the last seen timestamp (used for resuming from database state)."""
        self.last_seen_timestamp = timestamp
