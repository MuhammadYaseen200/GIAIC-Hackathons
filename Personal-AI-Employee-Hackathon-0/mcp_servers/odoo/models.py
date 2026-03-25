"""Pydantic models for Odoo MCP server responses."""
from pydantic import BaseModel
from typing import Optional


class GLSummary(BaseModel):
    """General Ledger summary data."""
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    net_income: float = 0.0
    currency: str = "USD"
    as_of_date: str = ""
    note: str = ""


class ARPartner(BaseModel):
    """Accounts Receivable partner aging entry."""
    partner_name: str
    amount_0_30: float = 0.0
    amount_31_60: float = 0.0
    amount_61_90: float = 0.0
    amount_over_90: float = 0.0
    total: float = 0.0


class ARAgingResult(BaseModel):
    """Full AR aging report."""
    partners: list[ARPartner] = []
    total_receivable: float = 0.0
    currency: str = "USD"


class InvoiceResult(BaseModel):
    """Invoice due in next N days."""
    invoice_id: int
    partner_name: str
    amount_due: float
    due_date: str
    days_remaining: int
    currency: str = "USD"


class OdooHealthResult(BaseModel):
    """Odoo connection health check."""
    healthy: bool
    version: str = ""
    db: str = ""
    error: str = ""
