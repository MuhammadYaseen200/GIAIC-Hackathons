"""Vercel serverless entry point for FastAPI application.

This module adapts the FastAPI app for Vercel's serverless environment.
"""

from app.main import app

# Vercel expects a variable named 'app' or a handler function
# Our FastAPI app is already named 'app', so we just need to expose it
handler = app
