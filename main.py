"""Polybot - Polymarket Copy Trading Bot."""

import logging
import signal
import sys
import time
from datetime import datetime

import db
from config import Config
from executor import Executor
from models import TradeSide
from position_manager import PositionManager
from tracker import Tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info("Shutdown signal received, stopping...")
    running = False


def main():
    """Main entry point for the copy trading bot."""
    global running

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration
    try:
        config = Config.from_env()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Target address: {config.target_address}")
        logger.info(f"Trade amount: ${config.trade_amount}")
        logger.info(f"Poll interval: {config.poll_interval}s")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize database
    conn = db.init_db(config.db_path)
    logger.info(f"Database initialized: {config.db_path}")

    # Initialize components
    tracker = Tracker(config.data_api_url, config.target_address)
    executor = Executor(config.clob_url, config.private_key, config.chain_id)
    position_manager = PositionManager(conn)

    # Initialize executor (derives API credentials)
    try:
        executor.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize executor: {e}")
        sys.exit(1)

    # Resume from last processed trade if available
    last_processed = db.get_last_processed_trade(conn)
    if last_processed:
        tracker.set_last_seen(last_processed.processed_at)
        logger.info(f"Resuming from last processed trade at {last_processed.processed_at}")

    logger.info("Starting main loop...")
    logger.info("Press Ctrl+C to stop")

    while running:
        try:
            # Fetch new trades from target user
            new_trades = tracker.get_new_trades()

            for trade in new_trades:
                # Skip if already processed
                if position_manager.is_trade_processed(trade.trade_id):
                    logger.debug(f"Trade {trade.trade_id} already processed, skipping")
                    continue

                logger.info(
                    f"New trade detected: {trade.side.value} {trade.outcome} "
                    f"@ {trade.price:.4f} (size: {trade.size:.4f})"
                )

                if trade.is_buy:
                    # Copy the buy trade
                    order_id = executor.buy(trade.token_id, config.trade_amount)
                    if order_id:
                        position_manager.record_entry(
                            trade, config.trade_amount, trade.price
                        )
                        logger.info(f"Copied BUY trade: order_id={order_id}")
                    else:
                        logger.warning(f"Failed to copy BUY trade for {trade.token_id}")
                        # Still mark as processed to avoid repeated failures
                        position_manager.mark_processed(trade.trade_id)

                elif trade.is_sell:
                    # Check if we have a position to close
                    position = position_manager.get_position(trade.token_id)
                    if position:
                        order_id = executor.sell(trade.token_id, position.amount)
                        if order_id:
                            position_manager.record_exit(trade)
                            logger.info(f"Copied SELL trade: order_id={order_id}")
                        else:
                            logger.warning(
                                f"Failed to copy SELL trade for {trade.token_id}"
                            )
                            position_manager.mark_processed(trade.trade_id)
                    else:
                        logger.info(
                            f"Target sold {trade.token_id} but we have no position, skipping"
                        )
                        position_manager.mark_processed(trade.trade_id)

            # Sleep before next poll
            time.sleep(config.poll_interval)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            # Continue running despite errors
            time.sleep(config.poll_interval)

    # Cleanup
    conn.close()
    logger.info("Bot stopped")


if __name__ == "__main__":
    main()
