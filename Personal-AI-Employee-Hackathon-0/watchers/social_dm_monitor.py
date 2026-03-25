"""Social DM Monitor — P3 watcher for keyword-triggered HITL escalation.

Polls Facebook DMs, Instagram mentions, and Twitter DMs for keywords.
On match → sends WhatsApp HITL notification via GoBridge.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "vault"))
KEYWORDS_FILE = VAULT_PATH / "Config" / "social_keywords.md"
AUDIT_LOG = VAULT_PATH / "Logs" / "audit.jsonl"

# Lazy import GoBridge to avoid import error when bridge not running
try:
    from mcp_servers.whatsapp.bridge import GoBridge
except ImportError:
    GoBridge = None  # type: ignore


def _log_audit(action: str, outcome: str, error: str = "") -> None:
    """Write audit log entry."""
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "agent": "social_dm_monitor",
            "attempt": 1,
            "outcome": outcome,
            "error": error,
        }
        with AUDIT_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"_log_audit failed: {e}")


async def load_keywords() -> list[str]:
    """Read DM monitoring keywords from vault/Config/social_keywords.md."""
    try:
        text = KEYWORDS_FILE.read_text()
        keywords = [k.strip() for k in text.replace("\n", ",").split(",") if k.strip()]
        return keywords
    except Exception as e:
        logger.warning(f"load_keywords failed: {e}")
        return ["job", "hire", "freelance", "client", "project", "urgent",
                "contract", "offer", "payment", "invoice", "business"]


async def should_escalate(text: str, keywords: list[str]) -> bool:
    """Return True if any keyword appears in text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


async def _twitter_request(endpoint: str) -> list[dict]:
    """Make authenticated Twitter API request. Raises on 403."""
    import httpx
    import os
    bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        raise Exception("No TWITTER_BEARER_TOKEN")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://api.twitter.com/2/{endpoint}",
            headers={"Authorization": f"Bearer {bearer}"},
            timeout=10,
        )
        if r.status_code == 403:
            raise Exception(f"403 Forbidden — elevated access required")
        r.raise_for_status()
        return r.json().get("data", [])


async def check_facebook_dms() -> list[dict]:
    """Check Facebook Page conversations for unread DMs. Returns [] on error."""
    try:
        import httpx
        import os
        page_id = os.getenv("FACEBOOK_PAGE_ID", "")
        token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        if not page_id or not token:
            return []
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://graph.facebook.com/v21.0/{page_id}/conversations",
                params={"access_token": token, "fields": "snippet,participants"},
                timeout=10,
            )
            r.raise_for_status()
            return r.json().get("data", [])
    except Exception as e:
        logger.warning(f"check_facebook_dms error: {e}")
        return []


async def check_instagram_mentions() -> list[dict]:
    """Check Instagram mentions. Returns [] if no IG account configured."""
    try:
        import httpx
        import os
        ig_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
        token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        if not ig_id or not token:
            logger.info("Instagram account not configured — skipping DM check")
            return []
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://graph.facebook.com/v21.0/{ig_id}/mentions",
                params={"access_token": token, "fields": "text,from"},
                timeout=10,
            )
            r.raise_for_status()
            return r.json().get("data", [])
    except Exception as e:
        logger.warning(f"check_instagram_mentions error: {e}")
        return []


async def check_twitter_dms() -> list[dict]:
    """Check Twitter DMs. Returns [] with warning on 403 (elevated access needed)."""
    try:
        return await _twitter_request("dm_events?dm_event.fields=text,sender_id")
    except Exception as e:
        logger.warning(f"check_twitter_dms error (likely 403 — Free tier): {e}")
        return []


async def notify_owner(platform: str, sender: str, snippet: str) -> None:
    """Send WhatsApp HITL notification for keyword match in DM/mention."""
    msg = (
        f"[{platform.upper()} DM] From: {sender}\n"
        f"Snippet: {snippet[:200]}\n"
        f"Possible business enquiry — check {platform} now."
    )
    msg = msg[:500]  # SC-003: ≤500 chars
    try:
        if GoBridge is not None:
            bridge = GoBridge()
            await bridge.send(msg)
        else:
            logger.warning(f"GoBridge unavailable — DM alert: {msg}")
    except Exception as e:
        logger.error(f"notify_owner failed: {e}")


async def run_dm_monitor() -> dict:
    """Check all 3 platforms, escalate keyword matches, return summary."""
    keywords = await load_keywords()

    results = {
        "facebook": await check_facebook_dms(),
        "instagram": await check_instagram_mentions(),
        "twitter": await check_twitter_dms(),
    }

    escalated = []
    for platform, items in results.items():
        for item in items:
            text = item.get("snippet", "") or item.get("text", "") or ""
            if await should_escalate(text, keywords):
                sender = (
                    item.get("participants", {}).get("data", [{}])[0].get("name", "unknown")
                    if platform == "facebook"
                    else item.get("from", {}).get("username", "unknown")
                    if platform == "instagram"
                    else item.get("sender_id", "unknown")
                )
                await notify_owner(platform, str(sender), text[:200])
                escalated.append({"platform": platform, "sender": str(sender)})

    summary = {
        "checked": list(results.keys()),
        "items_found": {p: len(v) for p, v in results.items()},
        "escalated": len(escalated),
    }
    _log_audit("dm_monitor.run", "success")
    return summary
