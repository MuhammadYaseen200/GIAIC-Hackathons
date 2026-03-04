"""Demo 4: WhatsApp Go bridge — send a real message to your phone.

Usage:
    PYTHONPATH=. .venv/bin/python demos/demo4_whatsapp_send.py
"""
import asyncio
import os
from dotenv import load_dotenv
from mcp_servers.whatsapp.bridge import GoBridge, _to_jid

load_dotenv()

OWNER = os.getenv("OWNER_WHATSAPP_NUMBER", "")


async def demo():
    print("\n📱 WhatsApp Bridge — Live Demo")
    print("=" * 50)

    if not OWNER:
        print("❌ OWNER_WHATSAPP_NUMBER not set in .env")
        return

    bridge = GoBridge()

    # Health check
    health = await bridge.health()
    print(f"Bridge health: {health.status} ({health.bridge_url})")
    if health.status != "healthy":
        print("❌ Bridge not reachable — is whatsapp-bridge running?")
        return

    # Send message
    jid = _to_jid(OWNER)
    print(f"\nSending to: {jid}")
    msg = (
        "🤖 AI Employee — Live Demo\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Privacy Gate: redacting OTPs, passwords, card numbers\n"
        "✅ HITL: approve/reject drafts via WhatsApp replies\n"
        "✅ Calendar: reading your Google Calendar\n"
        "✅ WhatsApp bridge: THIS MESSAGE is the live proof\n\n"
        "Phase 5 COMPLETE — 32/32 tasks, 533 tests."
    )
    try:
        result = await bridge.send(OWNER, msg)
        print(f"✅ Sent! message_id={result.message_id}, status={result.status}")
    except Exception as e:
        print(f"❌ Send failed: {e}")

    print("\n" + "=" * 50)
    print("WhatsApp demo complete.\n")


asyncio.run(demo())
