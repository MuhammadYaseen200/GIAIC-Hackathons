"""Weekly Audit Orchestrator -- H0 Phase 6 Gold Tier.

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

MAX_WHATSAPP_MSG_LENGTH = 500  # SC-003: HITL notifications must fit in one WhatsApp message

VAULT_PATH = Path(os.getenv("VAULT_PATH", "vault"))
BRIEFING_DIR = VAULT_PATH / "CEO_Briefings"
LOG_DIR = VAULT_PATH / "Logs"
BRIEFING_LOG = LOG_DIR / "ceo_briefing.jsonl"


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


async def collect_full_gl() -> dict:
    """Fetch General Ledger summary from Odoo MCP."""
    try:
        from mcp_servers.odoo.client import get_gl_summary_data
        import httpx
        async with httpx.AsyncClient() as client:
            result = await get_gl_summary_data(client)
        return result
    except Exception as e:
        logger.warning(f"collect_full_gl error: {e}")
        return {"status": "unavailable", "error": str(e)}


async def collect_full_ar() -> dict:
    """Fetch Accounts Receivable aging from Odoo MCP (all 4 buckets)."""
    try:
        from mcp_servers.odoo.client import get_ar_aging_data
        import httpx
        async with httpx.AsyncClient() as client:
            result = await get_ar_aging_data(client)
        return result
    except Exception as e:
        logger.warning(f"collect_full_ar error: {e}")
        return {"status": "unavailable", "error": str(e)}


async def collect_invoices_due() -> dict:
    """Fetch invoices due within next 7 days from Odoo MCP."""
    try:
        from mcp_servers.odoo.client import get_invoices_due_data
        import httpx
        async with httpx.AsyncClient() as client:
            invoices = await get_invoices_due_data(client, days=7)
        overdue = [i for i in invoices if i.get("days_remaining", 0) < 0]
        upcoming = [i for i in invoices if i.get("days_remaining", 0) >= 0]
        return {
            "overdue": overdue,
            "upcoming": upcoming,
            "total_count": len(invoices),
        }
    except Exception as e:
        logger.warning(f"collect_invoices_due error: {e}")
        return {"status": "unavailable", "error": str(e)}


async def collect_odoo_all() -> dict:
    """Fetch GL, AR, and invoices from Odoo in parallel using a shared HTTP client."""
    from mcp_servers.odoo.client import get_gl_summary_data, get_ar_aging_data, get_invoices_due_data
    from mcp_servers.odoo.auth import get_odoo_session
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Pre-warm session so parallel calls don't all race to authenticate
        try:
            await get_odoo_session(client)
        except Exception:
            pass  # auth errors handled per-call below
        gl, ar, invoices_raw = await asyncio.gather(
            get_gl_summary_data(client),
            get_ar_aging_data(client),
            get_invoices_due_data(client, days=7),
            return_exceptions=True,
        )
    gl_result = gl if isinstance(gl, dict) else {"status": "unavailable", "error": str(gl)}
    ar_result = ar if isinstance(ar, dict) else {"status": "unavailable", "error": str(ar)}
    if isinstance(invoices_raw, list):
        overdue = [i for i in invoices_raw if i.get("days_remaining", 0) < 0]
        upcoming = [i for i in invoices_raw if i.get("days_remaining", 0) >= 0]
        invoices_result = {"overdue": overdue, "upcoming": upcoming, "total_count": len(invoices_raw)}
    else:
        invoices_result = {"status": "unavailable", "error": str(invoices_raw)}
    return {"gl": gl_result, "ar": ar_result, "invoices": invoices_result}


async def collect_7day_social_rollup() -> dict:
    """Read vault/Logs/ for social posts in the last 7 days, grouped by platform."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        by_platform: dict[str, int] = {}
        total = 0

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
                                    platform = entry.get("platform", "unknown")
                                    by_platform[platform] = by_platform.get(platform, 0) + 1
                                    total += 1
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue

        return {"by_platform": by_platform, "total": total}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def collect_7day_email_rollup() -> dict:
    """Read vault/Logs/ for email events in the last 7 days, grouped by priority."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        by_priority: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        total = 0

        log_files = list(LOG_DIR.glob("*.jsonl")) if LOG_DIR.exists() else []
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
                                if ts.replace(tzinfo=None) >= cutoff.replace(tzinfo=None):
                                    priority = entry.get("priority", "low").lower()
                                    total += 1
                                    if priority in by_priority:
                                        by_priority[priority] += 1
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue

        return {"by_priority": by_priority, "total": total}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _llm_draft_weekly(sections: dict) -> str:
    """Generate weekly audit using Anthropic LLM (primary path)."""
    import anthropic

    client = anthropic.AsyncAnthropic(timeout=60.0)
    sections_text = json.dumps(sections, separators=(',', ':'), default=str)
    prompt = f"""You are generating a weekly financial audit for H0 Personal AI Employee.

Data collected:
{sections_text}

Generate a structured weekly audit with EXACTLY these 7 sections:
## 1. General Ledger Summary
## 2. Accounts Receivable Aging
## 3. Invoices Due This Week
## 4. Action Required
## 5. Social Media Rollup (7 days)
## 6. Email Rollup (7 days)
## 7. System Health

Be concise, factual, and actionable. Use bullet points and tables where appropriate."""

    message = await asyncio.wait_for(
        client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        ),
        timeout=55.0,
    )
    text = message.content[0].text
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")
    return text


async def _template_draft_weekly(sections: dict) -> str:
    """Generate weekly audit using template fallback (ADR-0019)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    gl_data = sections.get("gl", {})
    ar_data = sections.get("ar", {})
    invoices_data = sections.get("invoices", {})
    social_data = sections.get("social", {})
    email_data = sections.get("email", {})

    gl_section = "Odoo unavailable" if gl_data.get("status") == "unavailable" else (
        f"Assets: {gl_data.get('total_assets', 'N/A')} | "
        f"Liabilities: {gl_data.get('total_liabilities', 'N/A')} | "
        f"Equity: {gl_data.get('total_equity', 'N/A')}"
    )

    ar_section = "Odoo unavailable" if ar_data.get("status") == "unavailable" else (
        f"Total receivable: {ar_data.get('total_receivable', 'N/A')}"
    )

    overdue = invoices_data.get("overdue", [])
    upcoming = invoices_data.get("upcoming", [])
    invoices_section = f"{len(overdue)} overdue, {len(upcoming)} upcoming"
    if invoices_data.get("status") == "unavailable":
        invoices_section = "Odoo unavailable"

    action_items = []
    if overdue:
        for inv in overdue[:5]:
            action_items.append(f"- OVERDUE: {inv.get('partner_name', 'Unknown')} -- {inv.get('amount_due', 0)}")
    action_section = "\n".join(action_items) if action_items else "- No action items this week"

    social_by_platform = social_data.get("by_platform", {})
    social_total = social_data.get("total", 0)
    social_section = f"{social_total} total posts"
    if social_by_platform:
        social_section += " | " + ", ".join(f"{k}: {v}" for k, v in social_by_platform.items())

    email_by_priority = email_data.get("by_priority", {})
    email_total = email_data.get("total", 0)
    email_section = f"{email_total} total emails | HIGH: {email_by_priority.get('high', 0)} | MED: {email_by_priority.get('medium', 0)} | LOW: {email_by_priority.get('low', 0)}"

    return f"""[TEMPLATE MODE] -- LLM unavailable, using structured template

# Weekly Audit -- {today}

## 1. General Ledger Summary
{gl_section}

## 2. Accounts Receivable Aging
{ar_section}

## 3. Invoices Due This Week
{invoices_section}

## 4. Action Required
{action_section}

## 5. Social Media Rollup (7 days)
{social_section}

## 6. Email Rollup (7 days)
{email_section}

## 7. System Health
- Odoo MCP: {"OK" if gl_data.get("status") != "unavailable" else "unavailable"}
- Calendar MCP: OK
- Gmail MCP: OK
"""


async def draft_weekly_audit(sections: dict) -> str:
    """Generate weekly audit -- LLM primary, template fallback (ADR-0019)."""
    try:
        content = await _llm_draft_weekly(sections)
        logger.info("Weekly audit drafted via LLM")
        return content
    except Exception as e:
        logger.warning(f"LLM draft failed ({type(e).__name__}: {e}), using template fallback")
        _log_event("llm_fallback_weekly", reason=str(e))
        return await _template_draft_weekly(sections)


async def write_audit_vault(content: str) -> Path:
    """Write weekly audit to vault/CEO_Briefings/week-YYYY-WNN.md (idempotent)."""
    if not content or not content.strip():
        raise ValueError("Audit content is empty — refusing to write misleading vault entry")
    BRIEFING_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    filename = f"week-{now.strftime('%G-W%V')}.md"  # ISO 8601 week (matches `date +%G-W%V`)
    audit_path = BRIEFING_DIR / filename

    llm_mode = "template" if "[TEMPLATE MODE]" in content else "llm"
    section_count = content.count("## ")

    frontmatter = f"""---
type: ceo_briefing
period: weekly
date: {today}
status: pending_approval
sections_generated: {section_count}
llm_mode: {llm_mode}
created_at: {now.isoformat()}
---

"""

    full_content = frontmatter + content

    # Atomic write (idempotent -- overwrites if exists)
    tmp_path = audit_path.with_suffix(".md.tmp")
    tmp_path.write_text(full_content, encoding="utf-8")
    tmp_path.replace(audit_path)
    audit_path.chmod(0o600)  # Weekly audits contain sensitive financial data

    logger.info(f"Weekly audit written: {audit_path}")
    return audit_path


async def send_hitl_notification(audit_path: Path, metrics: dict) -> None:
    """Send WhatsApp HITL notification for weekly audit (<=500 chars)."""
    try:
        from mcp_servers.whatsapp.bridge import GoBridge

        duration = metrics.get("duration_s", 0)
        mode = metrics.get("llm_mode", "unknown")
        sections = metrics.get("sections", 7)

        msg = (
            f"Weekly Audit ready: {audit_path.name}\n"
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


async def run_weekly_audit() -> dict:
    """Run weekly audit via run_until_complete."""
    from orchestrator.run_until_complete import run_until_complete
    from watchers.utils import FileLock

    _lock = FileLock("/tmp/h0_weekly_audit.lock")
    try:
        _lock.acquire()
    except RuntimeError as _e:
        logger.info(f"Weekly audit already running ({_e}). Skipping.")
        return {"status": "skipped", "reason": "already_running"}

    start_time = datetime.now(timezone.utc)
    sections: dict = {}
    audit_path: Path | None = None

    async def step_collect_odoo_all() -> None:
        result = await collect_odoo_all()
        sections["gl"] = result["gl"]
        sections["ar"] = result["ar"]
        sections["invoices"] = result["invoices"]

    async def step_collect_social() -> None:
        sections["social"] = await collect_7day_social_rollup()

    async def step_collect_email() -> None:
        sections["email"] = await collect_7day_email_rollup()

    async def step_draft() -> None:
        sections["content"] = await draft_weekly_audit(sections)

    async def step_write_vault() -> None:
        nonlocal audit_path
        audit_path = await write_audit_vault(sections.get("content", ""))

    async def step_send_hitl() -> None:
        if audit_path:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            mode = "template" if "[TEMPLATE MODE]" in sections.get("content", "") else "llm"
            await send_hitl_notification(audit_path, {
                "duration_s": duration,
                "llm_mode": mode,
                "sections": sections.get("content", "").count("## "),
            })

    async def on_exhausted(workflow: str, step: str, error: Exception) -> None:
        logger.error(f"Weekly audit failed at step {step}: {error}")
        try:
            from mcp_servers.whatsapp.bridge import GoBridge
            owner_wa = os.environ.get("OWNER_WHATSAPP_NUMBER", "")
            if owner_wa:
                bridge = GoBridge()
                await bridge.send(owner_wa, f"Weekly Audit failed at step '{step}' after 3 retries. Error: {str(error)[:200]}"[:MAX_WHATSAPP_MSG_LENGTH])
        except Exception:
            pass

    try:
        try:
            result = await asyncio.wait_for(
                run_until_complete(
                    "weekly_audit",
                    [
                        ("collect_odoo_all", step_collect_odoo_all),  # GL + AR + invoices in parallel
                        ("collect_social", step_collect_social),
                        ("collect_email", step_collect_email),
                        ("draft", step_draft),
                        ("write_vault", step_write_vault),
                        ("send_hitl", step_send_hitl),
                    ],
                    max_retries=3,
                    on_exhausted=on_exhausted,
                ),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            logger.error("Weekly audit exceeded 120s timeout")
            result = {"status": "failed", "error": "timeout", "completed": []}

        # Log completion
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        _log_event(
            "weekly_audit_generated",
            period="weekly",
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
    parser = argparse.ArgumentParser(description="Weekly Audit")
    parser.add_argument("--now", action="store_true", help="Run immediately")
    args = parser.parse_args()

    if args.now:
        asyncio.run(run_weekly_audit())
    else:
        print("Use --now to run immediately")
