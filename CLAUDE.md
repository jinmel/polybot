# Polybot - Polymarket Copy Trading Bot

A simple copy trading bot that tracks a target user on Polymarket and mirrors their trades.

## What it does

- Monitors a target wallet's trading activity on Polymarket
- Copies trade direction (BUY/SELL) with a fixed amount
- Closes positions when target closes theirs

## Tech Stack

- Python 3.9+
- py-clob-client (official Polymarket SDK)
- uv for dependency management

## Project Structure

```
polybot/
├── CLAUDE.md           # Project documentation
├── pyproject.toml      # uv dependencies
├── .env.example        # Template for environment variables
├── config.py           # Configuration (credentials, settings)
├── db.py               # SQLite database layer
├── models.py           # Data classes for trades, positions
├── tracker.py          # Track target user activity
├── position_manager.py # Track our copied positions
├── executor.py         # Execute trades via CLOB
└── main.py             # Entry point
```

## API Reference

| API | Base URL | Purpose |
|-----|----------|---------|
| **Data API** | `https://data-api.polymarket.com` | Track user activity & positions |
| **CLOB API** | `https://clob.polymarket.com` | Place trades, get market data |

## Running the Bot

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the bot
uv run python main.py
```

## Coding Style

1. Keep it simple and straightforward
2. Use clear variable names and modular functions
3. Add comments where necessary to explain complex logic
4. Avoid over-abstraction - prefer explicit over clever
5. Focus on core functionality - additional features can be added later
