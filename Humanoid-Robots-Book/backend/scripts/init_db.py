"""
Database Initialization Script
Creates all tables in Neon Postgres using SQLAlchemy models.

Usage:
    python scripts/init_db.py
"""

# import sys
# import asyncio
# from pathlib import Path

# # Add backend/src to Python path
# backend_dir = Path(__file__).parent.parent
# sys.path.insert(0, str(backend_dir / "src"))

# from dotenv import load_dotenv
# load_dotenv()  # Load environment variables BEFORE imports

# from sqlalchemy.ext.asyncio import create_async_engine
# from db.models import Base
# from config import get_settings

# async def init_database():
#     """
#     Create all database tables defined in SQLAlchemy models.

#     This will:
#     1. Connect to Neon Postgres
#     2. Create tables: chat_sessions, chat_messages, query_logs
#     3. Create indexes and constraints
#     """
#     settings = get_settings()

#     # Create async engine
#     engine = create_async_engine(
#         settings.database_url,
#         echo=True,  # Print SQL statements for debugging
#         future=True
#     )

#     print("🔧 Connecting to Neon Postgres...")
#     print(f"📍 Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'}")

#     try:
#         # Create all tables
#         async with engine.begin() as conn:
#             print("\n🏗️  Creating tables from SQLAlchemy models...")
#             await conn.run_sync(Base.metadata.create_all)

#         print("\n✅ Database initialization complete!")
#         print("\nCreated tables:")
#         print("  - chat_sessions (session_id, started_at, chapter_context, user_agent)")
#         print("  - chat_messages (message_id, session_id, role, content, citations)")
#         print("  - query_logs (query_id, session_id, question, answer, tokens_used)")
#         print("\nCreated indexes:")
#         print("  - idx_messages_session_time (chat_messages)")
#         print("  - idx_query_logs_session (query_logs)")
#         print("  - idx_query_logs_timestamp (query_logs)")
#         print("  - idx_sessions_started (chat_sessions)")
#         print("  - idx_messages_citations (chat_messages JSONB index)")

#     except Exception as e:
#         print(f"\n❌ Error creating tables: {e}")
#         print("\nTroubleshooting:")
#         print("  1. Check DATABASE_URL in .env file")
#         print("  2. Verify Neon Postgres is accessible")
#         print("  3. Ensure database exists")
#         sys.exit(1)
#     finally:
#         await engine.dispose()

# if __name__ == "__main__":
#     print("=" * 60)
#     print("DATABASE INITIALIZATION SCRIPT")
#     print("=" * 60)
#     print()

#     asyncio.run(init_database())

#     print("\n" + "=" * 60)
#     print("Next Steps:")
#     print("  1. Run ingestion: python scripts/ingest_docs.py")
#     print("  2. Start backend: uvicorn src.main:app --reload")
#     print("  3. Start frontend: npm start")
#     print("=" * 60)



import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Force load the .env file
load_dotenv()

# Add the src directory to the python path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.db.models import Base
from src.config import settings

async def init_database():
    print("="*60)
    print("DATABASE INITIALIZATION SCRIPT")
    print("="*60)

    # --- THE FIX: Manually Clean the URL ---
    # 1. Get the raw URL from environment or settings
    db_url = os.getenv("DATABASE_URL", settings.database_url)
    
    # 2. Force the correct driver (postgresql+asyncpg)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        
    # 3. CRITICAL: Remove 'sslmode' if it exists (asyncpg hates it)
    if "sslmode=require" in db_url:
        db_url = db_url.replace("sslmode=require", "")
        
    # 4. Clean up any double && or trailing ? from the removal
    db_url = db_url.replace("&&", "&").replace("?&", "?").rstrip("&").rstrip("?")
    
    # 5. Ensure 'ssl=require' is present (Neon needs this)
    if "ssl=require" not in db_url:
        if "?" in db_url:
            db_url += "&ssl=require"
        else:
            db_url += "?ssl=require"

    print(f"🔧 Corrected URL for AsyncPG: {db_url.split('@')[-1]}") 

    try:
        engine = create_async_engine(
            db_url,
            echo=True,
            future=True
        )

        async with engine.begin() as conn:
            print("🔄 Connecting to Neon...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ SUCCESS: Tables created successfully!")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure your .env DATABASE_URL starts with postgresql://")
        print("  2. Ensure your Neon password is correct")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(init_database())