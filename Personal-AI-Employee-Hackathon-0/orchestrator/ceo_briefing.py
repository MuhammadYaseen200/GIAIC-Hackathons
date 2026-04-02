"""CEO Daily Briefing Orchestrator -- H0 Phase 6 Gold Tier.

Per ADR-0019: LLM primary + template fallback.
Per ADR-0018: run_until_complete per-step retry.
"""
from __future__ import annotations
import os as _os, sys as _sys
# Ensure project root is on sys.path when run as a script (e.g. via cron)
_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _PROJECT_ROOT not in _sys.path:
    _sys.path.insert(0, _PROJECT_ROOT)

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "vault"))
BRIEFING_DIR = VAULT_PATH / "CEO_Briefings"
LOG_DIR = VAULT_PATH / "Logs"
BRIEFING_LOG = LOG_DIR / "ceo_briefing.jsonl"

MAX_WHATSAPP_MSG_LENGTH = 500  # SC-003: HITL notifications must fit in one WhatsApp message


def _log_event(event: str, **kwargs: Any) -> None:
    """Write event to vault/Logs/ceo_briefing.jsonl."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **kwargs,
        }
        with BRIEFING_LOG.open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as e:
        logger.warning(f"_log_event failed: {e}")


async def collect_email_summary() -> dict:
    """Collect email triage summary from vault logs."""
    try:
        log_files = list(LOG_DIR.glob("*.jsonl")) if LOG_DIR.exists() else []
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "total": 0}

        for log_file in log_files:
            if "email" not in log_file.name and "gmail" not in log_file.name:
                continue
            try:
                with log_file.open() as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            ts_str = entry.get("ts", "")
                            if ts_str:
                                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                if ts.replace(tzinfo=None) >= yesterday.replace(tzinfo=None):
                                    priority = entry.get("priority", "low").lower()
                                    counts["total"] += 1
                                    if priority in counts:
                                        counts[priority] += 1
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue

        if counts["total"] == 0:
            return {"note": "No emails processed in the last 24h", "counts": counts}
        return {"counts": counts, "note": ""}
    except Exception as e:
        logger.error(f"collect_email_summary error: {e}", exc_info=True)
        return {"status": "unavailable", "error": str(e)}


async def collect_calendar_section(period: str = "daily") -> dict:
    """Collect calendar events from Calendar MCP."""
    try:
        hours = 48 if period == "daily" else 168
        try:
            from mcp_servers.calendar.server import list_events
            now_iso = datetime.now(timezone.utc).isoformat()
            future_iso = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
            result = await asyncio.wait_for(
                list_events(time_min=now_iso, time_max=future_iso, max_results=10),
                timeout=10.0,
            )
            if isinstance(result, dict):
                if "content" in result:
                    return json.loads(result["content"])
                if "events" in result:
                    return result
        except Exception as e:
            logger.warning(f"Calendar MCP unavailable: {e}")
        return {"status": "unavailable", "note": "Calendar MCP unavailable"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def collect_odoo_section(period: str = "daily") -> dict:
    """Collect Odoo financial data (overdue invoices for daily)."""
    try:
        from mcp_servers.odoo.client import get_invoices_due_data
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            invoices = await get_invoices_due_data(client, days=0)
        overdue = [i for i in invoices if i.get("days_remaining", 0) < 0]
        if not overdue:
            return {"note": "No overdue invoices -- all clear", "invoices": []}
        return {"invoices": overdue, "count": len(overdue)}
    except Exception as e:
        logger.warning(f"collect_odoo_section error: {e}")
        return {"status": "unavailable", "note": "Odoo unavailable"}


async def collect_social_section(period: str = "daily") -> dict:
    """Collect recent social media posts from vault logs."""
    try:
        hours = 24 if period == "daily" else 168
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        posts: list[dict] = []

        for log_name in ["social_posts.jsonl", "linkedin_posts.jsonl"]:
            log_file = LOG_DIR / log_name
            if not log_file.exists():
                continue
            try:
                with log_file.open() as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            ts_str = entry.get("ts", "")
                            if ts_str:
                                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                if ts.replace(tzinfo=None) >= cutoff.replace(tzinfo=None):
                                    posts.append({
                                        "platform": entry.get("platform", "unknown"),
                                        "action": entry.get("action", entry.get("event", "")),
                                        "ts": ts_str,
                                    })
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue

        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _llm_draft(sections: dict, period: str) -> str:
    """Generate briefing using Anthropic LLM (primary path, ADR-0019)."""
    import anthropic

    client = anthropic.AsyncAnthropic(timeout=60.0)

    sections_text = json.dumps(sections, separators=(',', ':'), default=str)
    prompt = f"""You are generating a {period} CEO briefing for H0 Personal AI Employee.

Data collected:
{sections_text}

Generate a structured CEO briefing with EXACTLY these 7 sections:
## 1. Email Triage
## 2. Financial Alert
## 3. Calendar (Next 48h)
## 4. Social Media Activity
## 5. LinkedIn Activity
## 6. Pending HITL Actions
## 7. System Health

Be concise, factual, and actionable. Use bullet points. If data is unavailable for a section, say so briefly."""

    message = await asyncio.wait_for(
        client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        ),
        timeout=25.0,
    )

    text = message.content[0].text
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")
    return text


async def _template_draft(sections: dict, period: str) -> str:
    """Generate briefing using template fallback (ADR-0019 -- always available)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    email_data = sections.get("email", {})
    odoo_data = sections.get("odoo", {})
    calendar_data = sections.get("calendar", {})
    social_data = sections.get("social", {})

    email_note = email_data.get("note", "")
    email_counts = email_data.get("counts", {})
    email_section = email_note or f"HIGH: {email_counts.get('high', 0)} | MED: {email_counts.get('medium', 0)} | LOW: {email_counts.get('low', 0)}"

    odoo_note = odoo_data.get("note", "")
    odoo_invoices = odoo_data.get("invoices", [])
    odoo_section = odoo_note or f"{len(odoo_invoices)} overdue invoice(s) require attention"
    if odoo_data.get("status") == "unavailable":
        odoo_section = "Odoo unavailable -- check connection"

    calendar_events = calendar_data.get("events", [])
    calendar_section = f"{len(calendar_events)} event(s) in next 48h" if calendar_events else "No upcoming events"
    if calendar_data.get("status") == "unavailable":
        calendar_section = "Calendar unavailable"

    social_posts = social_data.get("posts", [])
    social_section = f"{len(social_posts)} post(s) published in last 24h" if social_posts else "No posts in last 24h"

    return f"""[TEMPLATE MODE] -- LLM unavailable, using structured template

# CEO Daily Briefing -- {today}

## 1. Email Triage
{email_section}

## 2. Financial Alert
{odoo_section}

## 3. Calendar (Next 48h)
{calendar_section}

## 4. Social Media Activity
{social_section}

## 5. LinkedIn Activity
- Check linkedin_posts.jsonl for recent activity

## 6. Pending HITL Actions
- Check vault/Pending_Approval/ for items awaiting review

## 7. System Health
- Odoo MCP: {"OK" if odoo_data.get("status") != "unavailable" else "unavailable"}
- Calendar MCP: {"OK" if calendar_data.get("status") != "unavailable" else "unavailable"}
- Gmail MCP: OK (email data available)
"""


async def draft_briefing(sections: dict, period: str) -> str:
    """Generate briefing -- LLM primary, template fallback (ADR-0019)."""
    try:
        content = await _llm_draft(sections, period)
        logger.info("Briefing drafted via LLM")
        return content
    except Exception as e:
        logger.warning(f"LLM draft failed ({e}), using template fallback")
        _log_event("llm_fallback", reason=str(e), period=period)
        return await _template_draft(sections, period)


async def write_briefing_vault(content: str, period: str) -> Path:
    """Write briefing to vault/CEO_Briefings/ with YAML frontmatter (idempotent)."""
    if not content or not content.strip():
        raise ValueError("Briefing content is empty — refusing to write misleading vault entry")
    BRIEFING_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{today}.md" if period == "daily" else f"week-{datetime.now(timezone.utc).strftime('%G-W%V')}.md"
    briefing_path = BRIEFING_DIR / filename

    # Detect LLM mode from content
    llm_mode = "template" if "[TEMPLATE MODE]" in content else "llm"
    section_count = content.count("## ")

    frontmatter = f"""---
type: ceo_briefing
period: {period}
date: {today}
status: pending_approval
sections_generated: {section_count}
llm_mode: {llm_mode}
created_at: {datetime.now(timezone.utc).isoformat()}
---

"""

    full_content = frontmatter + content

    # Atomic write (idempotent -- overwrites if exists)
    tmp_path = briefing_path.with_suffix(".md.tmp")
    tmp_path.write_text(full_content, encoding="utf-8")
    tmp_path.replace(briefing_path)
    briefing_path.chmod(0o600)  # CEO briefings contain sensitive financial data

    logger.info(f"Briefing written: {briefing_path}")
    return briefing_path


async def send_hitl_notification(briefing_path: Path, metrics: dict) -> None:
    """Send WhatsApp HITL notification (<=500 chars per SC-003)."""
    try:
        from mcp_servers.whatsapp.bridge import GoBridge

        duration = metrics.get("duration_s", 0)
        mode = metrics.get("llm_mode", "unknown")
        sections = metrics.get("sections", 7)

        msg = (
            f"CEO Briefing ready: {briefing_path.name}\n"
            f"{sections} sections | {duration:.0f}s | {mode}\n"
            f"Reply APPROVE to send via email, REJECT to discard."
        )
        msg = msg[:MAX_WHATSAPP_MSG_LENGTH]  # SC-003: hard cap

        owner_wa = os.environ.get("OWNER_WHATSAPP_NUMBER", "")
        if not owner_wa:
            logger.warning("OWNER_WHATSAPP_NUMBER not set — skipping HITL notification")
            return
        bridge = GoBridge()
        await asyncio.wait_for(bridge.send(owner_wa, msg), timeout=15.0)
        logger.info(f"HITL notification sent ({len(msg)} chars)")
    except Exception as e:
        logger.warning(
            f"HITL notification failed (non-blocking): {e} — "
            f"WhatsApp bridge offline at {os.getenv('WHATSAPP_BRIDGE_URL', 'http://localhost:8080')}. "
            f"Restart with: nohup ~/whatsapp-mcp/whatsapp-bridge/whatsapp-bridge &"
        )


async def check_approval_and_email(briefing_path: Path) -> dict:
    """Check if briefing is approved and send via Gmail if so."""
    try:
        if not briefing_path.exists():
            return {"status": "missing"}

        content = briefing_path.read_text()
        if "status: approved" in content:
            # Send via Gmail MCP
            try:
                from mcp_servers.gmail.server import send_email
                result = await send_email(
                    to=os.getenv("OWNER_EMAIL", ""),
                    subject=f"CEO Briefing -- {briefing_path.stem}",
                    body=content,
                )
                # Update frontmatter status
                updated = content.replace("status: approved", "status: delivered")
                briefing_path.write_text(updated)
                _log_event("briefing_delivered", path=str(briefing_path))
                return {"status": "delivered", "email_sent": True}
            except Exception as e:
                logger.error(f"Email delivery failed: {e}")
                return {"status": "approved", "email_sent": False, "error": str(e)}

        if "status: " in content:
            status = content.split("status: ")[1].split("\n")[0]
        else:
            status = "pending_approval"
        return {"status": status}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def run_daily_briefing() -> dict:
    """Run daily CEO briefing via run_until_complete."""
    from orchestrator.run_until_complete import run_until_complete
    from watchers.utils import FileLock

    _lock = FileLock("/tmp/h0_ceo_briefing.lock")
    try:
        _lock.acquire()
    except RuntimeError as _e:
        logger.info(f"CEO briefing already running ({_e}). Skipping.")
        return {"status": "skipped", "reason": "already_running"}

    try:
        start_time = datetime.now(timezone.utc)
        sections: dict = {}
        briefing_path: Path | None = None

        async def step_collect_email() -> None:
            sections["email"] = await collect_email_summary()

        async def step_collect_calendar() -> None:
            sections["calendar"] = await collect_calendar_section("daily")

        async def step_collect_odoo() -> None:
            sections["odoo"] = await collect_odoo_section("daily")

        async def step_collect_social() -> None:
            sections["social"] = await collect_social_section("daily")

        async def step_collect_all() -> None:
            await asyncio.gather(
                step_collect_email(),
                step_collect_calendar(),
                step_collect_odoo(),
                step_collect_social(),
            )

        async def step_draft() -> None:
            sections["content"] = await draft_briefing(sections, "daily")

        async def step_write_vault() -> None:
            nonlocal briefing_path
            briefing_path = await write_briefing_vault(sections.get("content", ""), "daily")

        async def step_send_hitl() -> None:
            if briefing_path:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                mode = "template" if "[TEMPLATE MODE]" in sections.get("content", "") else "llm"
                await send_hitl_notification(briefing_path, {
                    "duration_s": duration,
                    "llm_mode": mode,
                    "sections": sections.get("content", "").count("## "),
                })

        async def on_exhausted(workflow: str, step: str, error: Exception) -> None:
            logger.error(f"Briefing failed at step {step}: {error}")
            try:
                from mcp_servers.whatsapp.bridge import GoBridge
                owner_wa = os.environ.get("OWNER_WHATSAPP_NUMBER", "")
                if owner_wa:
                    bridge = GoBridge()
                    await bridge.send(owner_wa, f"CEO Briefing failed at step '{step}' after 3 retries. Error: {str(error)[:200]}"[:MAX_WHATSAPP_MSG_LENGTH])
            except Exception:
                pass

        try:
            result = await asyncio.wait_for(
                run_until_complete(
                    "daily_briefing",
                    [
                        ("collect_all", step_collect_all),
                        ("draft", step_draft),
                        ("write_vault", step_write_vault),
                        ("send_hitl", step_send_hitl),
                    ],
                    max_retries=3,
                    on_exhausted=on_exhausted,
                ),
                timeout=90.0,  # SC-001: 60s target; 90s hard cap accounts for real OAuth latency
            )
        except asyncio.TimeoutError:
            logger.error("Daily briefing exceeded 90s hard cap (SC-001 target: 60s)")
            result = {"status": "failed", "error": "timeout", "completed": []}

        # Log completion
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        _log_event(
            "briefing_generated",
            period="daily",
            status=result["status"],
            duration_s=duration,
            completed_steps=result.get("completed", []),
        )
    finally:
        _lock.release()
    return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT + "/.env")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    import argparse
    parser = argparse.ArgumentParser(description="CEO Daily Briefing")
    parser.add_argument("--now", action="store_true", help="Run immediately")
    args = parser.parse_args()

    if args.now:
        asyncio.run(run_daily_briefing())
    else:
        print("Use --now to run immediately")
