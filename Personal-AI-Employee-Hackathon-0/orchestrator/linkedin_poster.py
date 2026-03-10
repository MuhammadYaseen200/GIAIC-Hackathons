#!/usr/bin/env python3
"""
LinkedIn posting workflow: draft -> HITL approval -> publish.

Entry points:
  --draft "topic"   Manual trigger (FR-006)
  --auto            Cron trigger -- picks random topic from vault/Config/linkedin_topics.md
  --check           Process pending approvals (run by orchestrator)

Reuses:
  - run_privacy_gate (watchers/privacy_gate.py)
  - GoBridge (mcp_servers/whatsapp/bridge.py)
  - vault_ops (orchestrator/vault_ops.py)
  - atomic_write, render_yaml_frontmatter, sanitize_filename (watchers/utils.py)
"""
import argparse
import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

# ── Project root guard ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIR = "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0"
if not str(PROJECT_ROOT).startswith(REQUIRED_DIR):
    print(f"WRONG DIRECTORY: {PROJECT_ROOT}\nRequired: {REQUIRED_DIR}\nSTOP.")
    sys.exit(1)

sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import anthropic

from mcp_servers.linkedin.auth import AuthRequiredError
from mcp_servers.linkedin.client import LinkedInAPIError, post_to_linkedin
from mcp_servers.whatsapp.bridge import GoBridge
from orchestrator.hitl_manager import _generate_draft_id
from orchestrator.vault_ops import move_to_done, update_frontmatter
from watchers.privacy_gate import run_privacy_gate
from watchers.utils import atomic_write, render_yaml_frontmatter, sanitize_filename

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [linkedin_poster] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("linkedin_poster")

# ── Vault paths ─────────────────────────────────────────────────────────────────
VAULT_PENDING = PROJECT_ROOT / "vault" / "Pending_Approval"
VAULT_DONE = PROJECT_ROOT / "vault" / "Done"
VAULT_REJECTED = PROJECT_ROOT / "vault" / "Rejected"
VAULT_LOGS = PROJECT_ROOT / "vault" / "Logs"
TOPICS_FILE = PROJECT_ROOT / "vault" / "Config" / "linkedin_topics.md"
POSTS_JSONL = VAULT_LOGS / "linkedin_posts.jsonl"
OWNER_WA = os.environ.get("OWNER_WHATSAPP_NUMBER", "")

# ── Helpers ─────────────────────────────────────────────────────────────────────


def _ensure_dirs():
    for d in [VAULT_PENDING, VAULT_DONE, VAULT_REJECTED, VAULT_LOGS]:
        d.mkdir(parents=True, exist_ok=True)


def _log_event(event: str, topic: str, status: str, extra: Optional[dict] = None):
    """Append one JSONL line to linkedin_posts.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat() + "Z",
        "event": event,
        "topic": topic,
        "status": status,
    }
    if extra:
        entry.update(extra)
    POSTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTS_JSONL, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _count_today_posts() -> int:
    """Count posts with status=published for today (UTC date)."""
    if not POSTS_JSONL.exists():
        return 0
    today = date.today().isoformat()
    count = 0
    for line in POSTS_JSONL.read_text().splitlines():
        try:
            entry = json.loads(line)
            if entry.get("status") == "published" and entry.get("ts", "").startswith(today):
                count += 1
        except json.JSONDecodeError:
            continue
    return count


def _load_topics() -> list[str]:
    """Read vault/Config/linkedin_topics.md and return non-empty bullet lines."""
    if not TOPICS_FILE.exists():
        logger.warning(f"Topics file not found: {TOPICS_FILE}")
        return ["AI agent development and automation"]
    lines = TOPICS_FILE.read_text().splitlines()
    topics = []
    for line in lines:
        stripped = line.strip().lstrip("- ").strip()
        if stripped and not stripped.startswith("#"):
            topics.append(stripped)
    return topics or ["AI learning and development"]


async def _draft_post_content(topic: str) -> str:
    """Draft LinkedIn post via Claude (150-300 words, professional tone)."""
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])  # async — avoids blocking event loop
    system = (
        "You are a professional content writer for a Pakistani AI developer and freelancer. "
        "Write LinkedIn posts that are professional, engaging, and authentic. "
        "Focus on: AI/ML learning, web development, Python automation, freelance work, hackathons. "
        "NEVER include personal information, financial details, or anything sensitive. "
        "Format: 2-4 paragraphs, 150-300 words, end with 2-3 relevant hashtags."
    )
    user_msg = f"Write a LinkedIn post about: {topic}"
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": user_msg}],
        system=system,
    )
    return response.content[0].text.strip()


async def _send_hitl_notification(topic: str, post_text: str, draft_path: Path, draft_id: str) -> None:
    """Send WhatsApp HITL notification with enriched content (SC-001, FR-005)."""
    preview = post_text[:300].replace("\n", " ") + ("..." if len(post_text) > 300 else "")
    short_id = draft_id[-12:]  # Last 12 chars — short enough to type easily
    slug = draft_path.name
    message = (
        f"*LinkedIn Draft Ready* -- HITL Approval Required\n\n"
        f"*Topic:* {topic}\n"
        f"*Type:* LinkedIn Post\n"
        f"*Draft ID:* `{short_id}`\n\n"
        f"*Preview:*\n{preview}\n\n"
        f"*Vault Path:* vault/Pending_Approval/{slug}\n\n"
        f"Reply *approve {short_id}* to publish\n"
        f"Reply *reject {short_id}* to discard\n\n"
        f"Auto-expires in 24h if no reply."
    )
    bridge = GoBridge()
    await bridge.send(OWNER_WA, message)


def _write_draft_vault_file(topic: str, post_text: str) -> tuple[Path, str]:
    """Write LinkedIn draft to vault/Pending_Approval/<timestamp>_linkedin_<slug>.md.

    Returns (path, draft_id) — draft_id enables WhatsApp HITL routing via HITLManager.
    """
    draft_id = _generate_draft_id()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    slug = sanitize_filename(topic)[:30]
    filename = f"{ts}_linkedin_{slug}.md"
    path = VAULT_PENDING / filename

    frontmatter_fields = {
        "type": "linkedin_post",
        "draft_id": draft_id,
        "topic": topic,
        "status": "pending_approval",
        "created_at": ts,
        "expires_at": datetime.now(timezone.utc).timestamp() + 86400,  # 24h
    }
    content = render_yaml_frontmatter(frontmatter_fields) + "\n\n" + post_text
    atomic_write(path, content)
    return path, draft_id


def _move_to_rejected(draft_path: Path) -> None:
    """Move draft file to vault/Rejected/."""
    VAULT_REJECTED.mkdir(parents=True, exist_ok=True)
    dest = VAULT_REJECTED / draft_path.name
    draft_path.rename(dest)


async def _call_post_update(post_text: str) -> dict:
    """Call LinkedIn API via MCP client. Returns dict with post_id."""
    return await post_to_linkedin(post_text, "PUBLIC")


# ── Core workflow ───────────────────────────────────────────────────────────────


async def draft_and_notify(topic: str) -> dict:
    """
    Main draft workflow:
    1. PrivacyGate check on topic
    2. Draft post content via LLM
    3. PrivacyGate check on post content
    4. Rate limit check
    5. Write vault file
    6. Send WhatsApp HITL notification
    7. Log event=drafted
    """
    _ensure_dirs()

    # Step 1: Privacy gate on topic
    topic_check = run_privacy_gate(topic, "text")
    if topic_check.media_blocked:
        logger.warning(f"Privacy gate blocked topic: {topic[:50]}")
        _log_event("draft_blocked", topic, "privacy_blocked")
        return {"status": "privacy_blocked", "reason": "topic_blocked"}

    # Step 2: Rate limit check (before LLM draft — T022)
    today_count = _count_today_posts()
    if today_count >= 1:
        logger.info(f"Rate limit: {today_count} post(s) published today. Queuing for tomorrow.")
        if OWNER_WA:
            try:
                bridge = GoBridge()
                await bridge.send(
                    OWNER_WA,
                    f"LinkedIn rate limit: already posted today. "
                    f"Topic '{topic[:50]}' queued for tomorrow.",
                )
            except Exception as e:
                logger.warning(f"WhatsApp rate-limit notice failed: {e}")
        _log_event("rate_limited", topic, "rate_limited")
        return {"status": "rate_limited"}

    # Step 3: Draft post content
    try:
        post_text = await _draft_post_content(topic)
    except Exception as e:
        logger.error(f"LLM draft failed: {e}", exc_info=True)
        _log_event("draft_error", topic, "llm_error", {"error": str(e)})
        return {"status": "error", "reason": f"LLM error: {e}"}

    # Step 4: Privacy gate on drafted content
    content_check = run_privacy_gate(post_text, "text")
    if content_check.media_blocked:
        logger.warning("Privacy gate blocked post content.")
        _log_event("draft_blocked", topic, "privacy_blocked_content")
        return {"status": "privacy_blocked", "reason": "content_blocked"}

    # Step 5: Write vault file (returns path + draft_id for HITL routing)
    draft_path, draft_id = _write_draft_vault_file(topic, post_text)

    # Step 6: WhatsApp HITL notification (non-fatal — draft survives if WA unavailable)
    try:
        await _send_hitl_notification(topic, post_text, draft_path, draft_id)
    except Exception as e:
        logger.error(f"WhatsApp notification failed: {e}. Draft saved at {draft_path}.")

    # Step 7: Log drafted event
    _log_event("drafted", topic, "pending_approval", {"vault_file": draft_path.name, "draft_id": draft_id})
    logger.info(f"Draft created: {draft_path}")
    return {"status": "drafted", "vault_file": str(draft_path)}


async def publish_approved(draft_path: Path) -> dict:
    """
    Publish an approved LinkedIn draft.
    Called by orchestrator when HITL status=approved.
    """
    if not draft_path.exists():
        logger.error(f"Draft file not found: {draft_path}")
        return {"status": "error", "reason": "file_not_found"}

    content = draft_path.read_text()
    # Extract post_text (body after frontmatter)
    parts = content.split("---", 2)
    post_text = parts[2].strip() if len(parts) >= 3 else content.strip()
    # Extract topic from frontmatter
    topic = "unknown"
    for line in (parts[1].splitlines() if len(parts) >= 3 else []):
        if line.startswith("topic:"):
            topic = line.split(":", 1)[1].strip()
            break

    try:
        result = await _call_post_update(post_text)
        post_id = result.get("post_id", "")
        update_frontmatter(draft_path, {"status": "published", "linkedin_post_id": post_id})
        move_to_done(draft_path, VAULT_DONE)
        _log_event("published", topic, "published", {"post_id": post_id})
        logger.info(f"Published to LinkedIn: {post_id}")
        return {"status": "published", "post_id": post_id}
    except AuthRequiredError as e:
        logger.error(f"Auth error during publish: {e}")
        update_frontmatter(draft_path, {"status": "auth_error"})
        _log_event("publish_error", topic, "auth_error", {"error": str(e)})
        return {"status": "auth_error", "reason": str(e)}
    except LinkedInAPIError as e:
        logger.error(f"LinkedIn API error during publish: {e.status_code} {e.detail}")
        update_frontmatter(draft_path, {"status": "api_error", "error": e.detail})
        _log_event(
            "publish_error",
            topic,
            "api_error",
            {"status_code": e.status_code, "detail": e.detail},
        )
        # Graceful degradation: do NOT delete draft; can retry later
        return {"status": "api_error", "reason": f"API {e.status_code}: {e.detail}"}


async def handle_rejected(draft_path: Path) -> dict:
    """Move rejected draft to vault/Rejected/ and log."""
    content = draft_path.read_text()
    topic = "unknown"
    parts = content.split("---", 2)
    for line in (parts[1].splitlines() if len(parts) >= 3 else []):
        if line.startswith("topic:"):
            topic = line.split(":", 1)[1].strip()
            break
    update_frontmatter(draft_path, {"status": "rejected"})
    _move_to_rejected(draft_path)
    _log_event("rejected", topic, "rejected")
    return {"status": "rejected"}


async def check_pending_approvals() -> None:
    """
    Scan vault/Pending_Approval/ for LinkedIn drafts and process approved/rejected/expired.
    Called by orchestrator every 15 minutes (via cron).
    """
    if not VAULT_PENDING.exists():
        return
    for draft_path in VAULT_PENDING.glob("*_linkedin_*.md"):
        content = draft_path.read_text()
        parts = content.split("---", 2)
        if len(parts) < 2:
            continue
        status = None
        expires_at = None
        for line in parts[1].splitlines():
            if line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
            if line.startswith("expires_at:"):
                try:
                    expires_at = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

        if status == "approved":
            await publish_approved(draft_path)
        elif status == "rejected":
            await handle_rejected(draft_path)
        elif status == "pending_approval" and expires_at and time.time() > expires_at:
            logger.info(f"Draft expired: {draft_path.name}")
            await handle_rejected(draft_path)
            _log_event("expired", "unknown", "expired", {"file": draft_path.name})


async def process_linkedin_vault_triggers(
    needs_action_dir: Path,
    done_dir: Path,
) -> None:
    """
    Scan vault/Needs_Action/ for linkedin trigger items (T029-T031).

    Detects files with:
      - frontmatter type=linkedin_post (T030)
      - frontmatter tags containing '#linkedin' (T031)

    For each match:
      1. Extract topic from frontmatter
      2. Call draft_and_notify(topic)
      3. Move trigger file to done_dir

    Called by orchestrator._run_poll_cycle() every 15 minutes (ADR-0015).
    """
    if not needs_action_dir.exists():
        return

    done_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(needs_action_dir.glob("*.md")):
        try:
            content = path.read_text()
            parts = content.split("---", 2)
            if len(parts) < 2:
                continue

            fm_text = parts[1]
            # Extract fields from raw frontmatter text
            item_type = ""
            topic = ""
            tags_raw = ""
            for line in fm_text.splitlines():
                if line.startswith("type:"):
                    item_type = line.split(":", 1)[1].strip().strip("'\"")
                elif line.startswith("topic:"):
                    topic = line.split(":", 1)[1].strip().strip("'\"")
                elif line.startswith("tags:"):
                    tags_raw = line.split(":", 1)[1].strip()

            is_linkedin = (
                item_type == "linkedin_post"
                or "#linkedin" in tags_raw
            )
            if not is_linkedin:
                continue

            if not topic:
                topic = "LinkedIn post"

            logger.info(f"Vault trigger: type=linkedin_post topic='{topic}' file={path.name}")
            result = await draft_and_notify(topic)
            logger.info(f"Vault trigger result: {result}")

            # Move trigger to Done regardless of draft result
            dest = done_dir / path.name
            path.rename(dest)

        except Exception as e:
            logger.error(f"Error processing linkedin vault trigger {path.name}: {e}", exc_info=True)


async def run_auto_mode() -> None:
    """--auto: Pick random topic from topic file and draft."""
    topics = _load_topics()
    topic = random.choice(topics)
    logger.info(f"Auto mode: selected topic '{topic}'")
    result = await draft_and_notify(topic)
    logger.info(f"Auto mode result: {result}")


# ── CLI ─────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="LinkedIn poster workflow")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--draft", metavar="TOPIC", help="Draft a post on given topic")
    group.add_argument(
        "--auto", action="store_true", help="Auto-draft from topic file (cron)"
    )
    group.add_argument("--check", action="store_true", help="Check pending approvals")
    args = parser.parse_args()

    if args.draft:
        asyncio.run(draft_and_notify(args.draft))
    elif args.auto:
        asyncio.run(run_auto_mode())
    elif args.check:
        asyncio.run(check_pending_approvals())


if __name__ == "__main__":
    main()
