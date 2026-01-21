"""Configuration management for Polybot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    private_key: str
    target_address: str
    trade_amount: float
    poll_interval: int
    db_path: str
    chain_id: int = 137  # Polygon mainnet
    clob_url: str = "https://clob.polymarket.com"
    data_api_url: str = "https://data-api.polymarket.com"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable is required")

        target_address = os.getenv("TARGET_ADDRESS")
        if not target_address:
            raise ValueError("TARGET_ADDRESS environment variable is required")

        trade_amount = float(os.getenv("TRADE_AMOUNT", "10"))
        poll_interval = int(os.getenv("POLL_INTERVAL", "10"))
        db_path = os.getenv("DB_PATH", "polybot.db")

        return cls(
            private_key=private_key,
            target_address=target_address,
            trade_amount=trade_amount,
            poll_interval=poll_interval,
            db_path=db_path,
        )
