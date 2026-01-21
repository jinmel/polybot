"""Execute trades on Polymarket via the CLOB API."""

import logging
from typing import Optional

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON

from models import TradeSide

logger = logging.getLogger(__name__)

# Price slippage buffer (e.g., 0.02 = 2%)
SLIPPAGE_BUFFER = 0.02


class Executor:
    """Executes trades using the Polymarket CLOB client."""

    def __init__(self, clob_url: str, private_key: str, chain_id: int = POLYGON):
        self.client = ClobClient(
            clob_url,
            key=private_key,
            chain_id=chain_id,
            signature_type=0,  # EOA wallet
        )
        self._initialized = False

    def initialize(self) -> None:
        """Initialize API credentials. Must be called before trading."""
        if self._initialized:
            return

        try:
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)
            self._initialized = True
            logger.info("Executor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize executor: {e}")
            raise

    def buy(self, token_id: str, amount: float) -> Optional[str]:
        """
        Place a buy order for the given token.

        Args:
            token_id: The token to buy
            amount: Amount in USDC to spend

        Returns:
            Order ID if successful, None otherwise
        """
        self._ensure_initialized()

        try:
            # Get current market price
            price = self._get_price(token_id, TradeSide.BUY)
            if price is None:
                logger.error(f"Could not get price for token {token_id}")
                return None

            # Add slippage buffer for buy orders (willing to pay slightly more)
            limit_price = min(price + SLIPPAGE_BUFFER, 0.99)

            # Calculate size based on amount and price
            size = amount / limit_price

            order_args = OrderArgs(
                token_id=token_id,
                price=limit_price,
                size=size,
                side="BUY",
                order_type=OrderType.GTC,
            )

            logger.info(
                f"Placing BUY order: token={token_id}, "
                f"price={limit_price:.4f}, size={size:.4f}"
            )

            response = self.client.create_and_post_order(order_args)
            order_id = response.get("orderID") or response.get("order_id")

            if order_id:
                logger.info(f"Order placed successfully: {order_id}")
            else:
                logger.warning(f"Order response: {response}")

            return order_id

        except Exception as e:
            logger.error(f"Failed to place buy order: {e}")
            return None

    def sell(self, token_id: str, size: float) -> Optional[str]:
        """
        Place a sell order for the given token.

        Args:
            token_id: The token to sell
            size: Number of shares to sell

        Returns:
            Order ID if successful, None otherwise
        """
        self._ensure_initialized()

        try:
            # Get current market price
            price = self._get_price(token_id, TradeSide.SELL)
            if price is None:
                logger.error(f"Could not get price for token {token_id}")
                return None

            # Subtract slippage buffer for sell orders (willing to accept slightly less)
            limit_price = max(price - SLIPPAGE_BUFFER, 0.01)

            order_args = OrderArgs(
                token_id=token_id,
                price=limit_price,
                size=size,
                side="SELL",
                order_type=OrderType.GTC,
            )

            logger.info(
                f"Placing SELL order: token={token_id}, "
                f"price={limit_price:.4f}, size={size:.4f}"
            )

            response = self.client.create_and_post_order(order_args)
            order_id = response.get("orderID") or response.get("order_id")

            if order_id:
                logger.info(f"Order placed successfully: {order_id}")
            else:
                logger.warning(f"Order response: {response}")

            return order_id

        except Exception as e:
            logger.error(f"Failed to place sell order: {e}")
            return None

    def _get_price(self, token_id: str, side: TradeSide) -> Optional[float]:
        """Get the current price for a token."""
        try:
            side_str = "BUY" if side == TradeSide.BUY else "SELL"
            response = self.client.get_price(token_id, side_str)

            # Response format: {"price": "0.5"}
            price_str = response.get("price")
            if price_str:
                return float(price_str)

            return None
        except Exception as e:
            logger.error(f"Failed to get price: {e}")
            return None

    def _ensure_initialized(self) -> None:
        """Ensure the executor is initialized."""
        if not self._initialized:
            self.initialize()
