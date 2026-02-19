"""Development server launcher with Windows event loop compatibility.

psycopg3 (async PostgreSQL driver) requires SelectorEventLoop on Windows.
Uvicorn 0.40+ defaults to ProactorEventLoop on Windows, which is incompatible.
This launcher sets the correct event loop policy BEFORE uvicorn creates its loop.

Usage: uv run python run_server.py
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="none",  # Disable uvicorn's loop factory to use our policy
    )
