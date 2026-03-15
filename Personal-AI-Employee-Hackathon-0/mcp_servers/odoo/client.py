"""Odoo async client — JSON-RPC calls to Odoo instance."""
import logging
import os
from datetime import datetime, timedelta, timezone
import httpx

from mcp_servers.odoo.auth import get_odoo_session, reset_session_cache, OdooAuthError
from mcp_servers.odoo.models import (
    GLSummary, ARPartner, ARAgingResult, InvoiceResult, OdooHealthResult,
)

logger = logging.getLogger(__name__)

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")


def _rpc_payload(model: str, method: str, args: list, kwargs: dict) -> dict:
    """Build a JSON-RPC payload for Odoo dataset/call_kw."""
    return {
        "jsonrpc": "2.0",
        "method": "call",
        "id": 1,
        "params": {
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }
    }


async def get_gl_summary_data(client: httpx.AsyncClient) -> dict:
    """Fetch General Ledger summary from Odoo."""
    try:
        session = await get_odoo_session(client)
        payload = _rpc_payload(
            "account.move.line", "read_group",
            args=[[], ["debit", "credit", "account_id"]],
            kwargs={"groupby": ["account_id"], "lazy": False},
        )
        headers = {"Cookie": f"session_id={session}"}
        response = await client.post(
            f"{ODOO_URL}/web/dataset/call_kw",
            json=payload, headers=headers, timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            if "session" in str(data["error"]).lower():
                reset_session_cache()
            return GLSummary(note=f"RPC error: {data['error']}").model_dump()

        result = data.get("result", [])
        total_debit = sum(r.get("debit", 0) for r in result)
        total_credit = sum(r.get("credit", 0) for r in result)

        return GLSummary(
            total_assets=total_debit,
            total_liabilities=total_credit,
            total_equity=total_debit - total_credit,
            note="Demo data" if total_debit == 0 and total_credit == 0 else "",
        ).model_dump()

    except OdooAuthError as e:
        return GLSummary(note=f"Auth error: {e}").model_dump()
    except Exception as e:
        logger.error(f"GL summary error: {e}", exc_info=True)
        return GLSummary(note=f"Error: {e}").model_dump()


async def get_ar_aging_data(client: httpx.AsyncClient) -> dict:
    """Fetch Accounts Receivable aging report."""
    try:
        session = await get_odoo_session(client)
        payload = _rpc_payload(
            "account.move", "search_read",
            args=[[["move_type", "=", "out_invoice"], ["state", "=", "posted"],
                   ["payment_state", "!=", "paid"]]],
            kwargs={"fields": ["partner_id", "amount_residual", "invoice_date_due",
                               "currency_id"],
                    "limit": 100},
        )
        headers = {"Cookie": f"session_id={session}"}
        response = await client.post(
            f"{ODOO_URL}/web/dataset/call_kw",
            json=payload, headers=headers, timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            reset_session_cache()
            return ARAgingResult().model_dump()

        today = datetime.now(timezone.utc).date()
        partners: dict[str, ARPartner] = {}

        for inv in data.get("result", []):
            name = inv.get("partner_id", [None, "Unknown"])[1] or "Unknown"
            amount = float(inv.get("amount_residual", 0))
            due_str = inv.get("invoice_date_due", "")

            if due_str:
                due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                days_overdue = (today - due_date).days
            else:
                days_overdue = 0

            if name not in partners:
                partners[name] = ARPartner(partner_name=name)
            p = partners[name]

            if days_overdue <= 0:
                p.amount_0_30 += amount
            elif days_overdue <= 30:
                p.amount_0_30 += amount
            elif days_overdue <= 60:
                p.amount_31_60 += amount
            elif days_overdue <= 90:
                p.amount_61_90 += amount
            else:
                p.amount_over_90 += amount
            p.total += amount

        partner_list = list(partners.values())
        total = sum(p.total for p in partner_list)
        return ARAgingResult(partners=partner_list, total_receivable=total).model_dump()

    except OdooAuthError:
        return ARAgingResult().model_dump()
    except Exception as e:
        logger.error(f"AR aging error: {e}", exc_info=True)
        return ARAgingResult().model_dump()


async def get_invoices_due_data(client: httpx.AsyncClient, days: int = 7) -> list:
    """Fetch invoices due within next N days."""
    try:
        session = await get_odoo_session(client)
        today = datetime.now(timezone.utc).date()
        due_by = today + timedelta(days=days)

        payload = _rpc_payload(
            "account.move", "search_read",
            args=[[["move_type", "=", "out_invoice"], ["state", "=", "posted"],
                   ["payment_state", "!=", "paid"],
                   ["invoice_date_due", "<=", due_by.isoformat()]]],
            kwargs={"fields": ["id", "partner_id", "amount_residual",
                               "invoice_date_due", "currency_id"],
                    "order": "invoice_date_due asc", "limit": 50},
        )
        headers = {"Cookie": f"session_id={session}"}
        response = await client.post(
            f"{ODOO_URL}/web/dataset/call_kw",
            json=payload, headers=headers, timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            reset_session_cache()
            return []

        results = []
        for inv in data.get("result", []):
            due_str = inv.get("invoice_date_due", "")
            if due_str:
                due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                days_remaining = (due_date - today).days
            else:
                days_remaining = 0

            results.append(InvoiceResult(
                invoice_id=inv["id"],
                partner_name=inv.get("partner_id", [None, "Unknown"])[1] or "Unknown",
                amount_due=float(inv.get("amount_residual", 0)),
                due_date=due_str,
                days_remaining=days_remaining,
                currency=inv.get("currency_id", [None, "USD"])[1] or "USD",
            ).model_dump())

        return results

    except OdooAuthError:
        return []
    except Exception as e:
        logger.error(f"Invoices due error: {e}", exc_info=True)
        return []


async def health_check_odoo(client: httpx.AsyncClient) -> dict:
    """Check Odoo connectivity and version."""
    try:
        response = await client.get(
            f"{ODOO_URL}/web/webclient/version_info",
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return OdooHealthResult(
            healthy=True,
            version=data.get("result", {}).get("server_version", "unknown"),
            db=os.getenv("ODOO_DB", ""),
        ).model_dump()
    except Exception as e:
        return OdooHealthResult(healthy=False, error=str(e)).model_dump()
