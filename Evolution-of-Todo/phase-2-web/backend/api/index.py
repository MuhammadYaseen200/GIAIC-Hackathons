"""Vercel serverless entry point for FastAPI application.

This module adapts the FastAPI app for Vercel's serverless environment.
Includes error handling to help debug deployment issues.
"""

import sys
import traceback

try:
    from app.main import app

    # Vercel expects a variable named 'app' or a handler function
    # Our FastAPI app is already named 'app', so we just need to expose it
    handler = app

    # Log successful import for debugging
    print("✅ FastAPI app imported successfully", file=sys.stderr)
    print(f"✅ Available routes: {[route.path for route in app.routes]}", file=sys.stderr)

except ImportError as e:
    print("❌ IMPORT ERROR in api/index.py:", file=sys.stderr)
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    print("❌ Traceback:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print("\n❌ Python path:", file=sys.stderr)
    print(f"❌ {sys.path}", file=sys.stderr)
    raise

except Exception as e:
    print("❌ UNEXPECTED ERROR in api/index.py:", file=sys.stderr)
    print(f"❌ Error type: {type(e).__name__}", file=sys.stderr)
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    print("❌ Traceback:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise
