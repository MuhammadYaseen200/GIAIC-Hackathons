# ADR-0016: Odoo API Protocol Selection

- **Status:** Accepted
- **Date:** 2026-03-11
- **Feature:** ceo-briefing-odoo-gold (Phase 6)
- **Context:** Phase 6 requires reading financial data from a self-hosted Odoo 18 Community
  instance running on localhost:8069. Three protocol options exist for remote access to Odoo
  business objects: XML-RPC (legacy), JSON-RPC (current internal), and REST API (new, partial
  coverage). The protocol choice determines the client library, error handling shape, auth
  mechanism, and long-term upgrade path.

## Decision

Use **Odoo JSON-RPC via `/web/dataset/call_kw`** as the sole protocol for all Odoo data access
in the `mcp_servers/odoo/` server.

- **Auth**: `POST /web/session/authenticate` → session `id` cookie → reuse per process
- **Queries**: `POST /web/dataset/call_kw` with JSON body (`model`, `method`, `args`, `kwargs`)
- **Client**: Plain `httpx.AsyncClient` (no additional library; same as all other MCP clients)
- **Session lifecycle**: In-memory singleton per process (Odoo sessions live ~1h; reset on 401)
- **Coverage**: `account.account`, `account.move`, `account.move.line` — read-only Phase 6

## Consequences

### Positive

- No new library dependency — `httpx` already installed project-wide
- Same singleton auth pattern as `mcp_servers/linkedin/auth.py` (ADR-0006) — zero learning curve
- JSON-RPC is the authoritative internal protocol for Odoo 16–18+; stable, well-documented
- Async-native: `httpx.AsyncClient` integrates cleanly with `fastmcp` async tool pattern
- Payload structure is consistent across all Odoo models — one `_rpc_payload()` builder function covers all queries

### Negative

- Session cookie auth is less standard than Bearer tokens — requires custom re-login logic on 401
- No automatic schema discovery (must hard-code field names per model)
- If Odoo instance restarts, in-memory session invalidated; first post-restart query fails then auto-recovers (one extra request)
- Odoo REST API (available in Odoo 17+) would eventually provide OpenAPI docs, but has incomplete model coverage in Odoo 18 Community — switching later is a viable migration path

## Alternatives Considered

**Alternative A: XML-RPC (`xmlrpc.client`)**
- Standard Python library, no extra install
- Rejected: Officially deprecated in Odoo 17+, synchronous only (blocks async event loop),
  XML parsing overhead, poor error messages vs JSON

**Alternative B: Odoo REST API (`/api/v2/...`)**
- Available since Odoo 17, Bearer token auth, OpenAPI-documented
- Rejected: Incomplete model coverage in Odoo 18 Community (financial models not exposed);
  requires separate REST API app installation; not available out-of-box on self-hosted Community

**Alternative C: `odoorpc` or `OdooRPC` library**
- Higher-level Python wrapper around XML-RPC/JSON-RPC
- Rejected: Additional dependency; synchronous by default; adds abstraction layer that
  complicates async integration (ADR-0002 pattern)

## References

- Feature Spec: `specs/010-ceo-briefing-odoo-gold/spec.md` (FR-009–FR-012)
- Implementation Plan: `specs/010-ceo-briefing-odoo-gold/plan.md` (Phase B, T007–T018)
- Related ADRs: ADR-0002 (async integration), ADR-0005 (FastMCP framework), ADR-0006 (auth singleton), ADR-0008 (typed MCP error contract), ADR-0014 (LinkedIn OAuth2 pattern mirrored here)
- Evaluator Evidence: `history/prompts/ceo-briefing-odoo-gold/002-phase6-gold-clarify-social-ralph.clarify.prompt.md`
