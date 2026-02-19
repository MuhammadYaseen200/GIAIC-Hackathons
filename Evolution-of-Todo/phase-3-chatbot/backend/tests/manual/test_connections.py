#!/usr/bin/env python3
"""
Connection validation script for Neon DB and OpenRouter API.
Tests both services to verify credentials and connectivity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()


async def test_neon_db():
    """Test Neon PostgreSQL database connection."""
    print("=" * 60)
    print("Testing Neon Database Connection")
    print("=" * 60)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment")
        return False

    print(f"[DB] Connection String: {database_url[:50]}...")

    try:
        # Create async engine
        engine = create_async_engine(database_url, echo=False)

        # Test connection
        async with engine.connect() as conn:
            # Basic connection test
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("[OK] Connection successful!")
            print(f"[VER] PostgreSQL Version: {version[:80]}")

            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            print(f"\n[TBL] Tables found ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")

            # Check specific required tables (plural form)
            required_tables = {"users", "tasks", "conversations"}
            missing_tables = required_tables - set(tables)

            if missing_tables:
                print(f"\n[!!] WARNING: Missing required tables: {missing_tables}")
                print("   Run migrations: uv run alembic upgrade head")
                return False
            else:
                print("\n[OK] All required tables present")

            # Count records in each table
            print("\n[CNT] Record Counts:")
            for table in required_tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   - {table}: {count} records")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"[ERR] Database connection failed: {str(e)}")
        return False


async def test_openrouter_api():
    """Test OpenRouter API key and connectivity."""
    print("\n" + "=" * 60)
    print("Testing OpenRouter API Connection")
    print("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    if not api_key:
        print("[ERR] ERROR: OPENROUTER_API_KEY not found in environment")
        return False

    print(f"[KEY] API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"[URL] Base URL: {base_url}")
    print(f"[MOD] Model: {model}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test API with simple completion request
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000"),
                    "X-Title": os.getenv("OPENROUTER_APP_NAME", "Evolution of Todo - Phase 3"),
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Respond with 'OK' if you receive this."}
                    ],
                    "max_tokens": 10,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print("[OK] API connection successful!")
                print(f"[MSG] Test Response: {content}")

                # Check for usage/credits info
                usage = data.get("usage", {})
                if usage:
                    print("[TOK] Token Usage:")
                    print(f"   - Prompt: {usage.get('prompt_tokens', 0)}")
                    print(f"   - Completion: {usage.get('completion_tokens', 0)}")
                    print(f"   - Total: {usage.get('total_tokens', 0)}")

                return True
            else:
                print(f"[ERR] API request failed: HTTP {response.status_code}")
                print(f"[RSP] Response: {response.text[:200]}")
                return False

    except httpx.TimeoutException:
        print("[ERR] API request timed out")
        return False
    except Exception as e:
        print(f"[ERR] API connection failed: {str(e)}")
        return False


async def main():
    """Run all connection tests."""
    print("\n[*] Starting Connection Validation")
    print("=" * 60)
    print(f"Working Directory: {os.getcwd()}")
    print(f"Environment File: {Path('.env').absolute()}")
    print("=" * 60 + "\n")

    # Run tests
    db_ok = await test_neon_db()
    api_ok = await test_openrouter_api()

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Neon Database:    {'[OK] PASS' if db_ok else '[ERR] FAIL'}")
    print(f"OpenRouter API:   {'[OK] PASS' if api_ok else '[ERR] FAIL'}")
    print("=" * 60)

    if db_ok and api_ok:
        print("\n[OK] GO: All systems ready for server startup")
        sys.exit(0)
    else:
        print("\n[!!] NO-GO: Fix issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    # Windows-specific fix for psycopg async mode
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
