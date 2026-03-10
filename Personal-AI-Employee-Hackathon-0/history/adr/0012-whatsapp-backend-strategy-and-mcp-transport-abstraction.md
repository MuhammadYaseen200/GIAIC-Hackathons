# ADR-0012: WhatsApp Backend Strategy and MCP Transport Abstraction

> **Scope**: Defines the WhatsApp messaging backend selection (Go bridge vs. pywa Cloud API), the env-driven switching mechanism, and the abstraction layer that insulates the WhatsApp MCP server from backend implementation details.

- **Status:** Accepted
- **Date:** 2026-03-02
- **Feature:** hitl-whatsapp-silver (008)
- **Context:** The AI Employee needs to send and receive WhatsApp messages for two purposes: (1) ingesting incoming messages into `vault/Needs_Action/`, and (2) sending HITL approval notifications + confirmations to the owner. Two viable backends exist. The Go bridge (WhatsApp Web protocol) is already authenticated and operational (HT-004 DONE) as `XXXXXXXXXXXX:4@s.whatsapp.net`. The pywa Cloud API (Meta official WhatsApp Business API) is the production-grade solution but blocked by HT-012 (Meta developer account, phone verification, webhook hosting not set up). The architecture must support both without major refactoring.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? ✅ YES — determines Meta API dependency, session management, webhook requirements for all WhatsApp features
     2) Alternatives: Multiple viable options considered with tradeoffs? ✅ YES — see Alternatives section
     3) Scope: Cross-cutting concern (not an isolated detail)? ✅ YES — affects WhatsApp watcher + WhatsApp MCP server + orchestrator config -->

## Decision

Implement a **Go bridge primary + pywa secondary fallback** strategy with a backend abstraction layer:

### Backend Selection
- **Primary (Phase 5)**: Go bridge REST API at `http://localhost:8080`
  - WhatsApp Web protocol; session already authenticated (HT-004 DONE)
  - Send: `POST http://localhost:8080/send` with `{"to": "<JID>", "body": "<text>"}`
  - Receive: `GET http://localhost:8080/messages?since=<last_id>` for polling
  - No Meta developer account, no webhook hosting, no phone number registration required
- **Secondary (fallback, Phase 5+ if bridge issues)**: pywa Cloud API
  - Meta official WhatsApp Business API via `@wa.on_message` webhook + `wa.send_message()`
  - Requires HT-012 completion (Meta developer account, verified phone number, ngrok/VPS for webhook, WHATSAPP_VERIFY_TOKEN)
  - Deferred — HT-012 remains PENDING

### Backend Switching
- `WHATSAPP_BACKEND=go_bridge` (default) or `WHATSAPP_BACKEND=pywa` in `.env`
- Switch is transparent to all callers (orchestrator, HITL Manager) — they only call WhatsApp MCP tools

### MCP Abstraction Layer
- `mcp_servers/whatsapp/bridge.py` provides `GoBridge.send(to, body)` and `GoBridge.receive()` classes
- `mcp_servers/whatsapp/server.py` reads `WHATSAPP_BACKEND` env var at startup; imports correct backend class
- WhatsApp watcher reads `WHATSAPP_BACKEND` to select polling vs webhook ingestion mode
- `PywaStub` class in `bridge.py` serves as placeholder for future pywa implementation

### Phone Number Format
- External input: E.164 format (`+15550001234`)
- Go bridge expects WhatsApp JID: `15550001234@s.whatsapp.net` (strip `+`, append `@s.whatsapp.net`)
- Normalization: handled in `GoBridge.send()` — callers always use E.164

### httpx for Go Bridge
- `httpx.AsyncClient` for non-blocking HTTP calls from async WhatsApp MCP server
- Timeout: 10s for send, 3s for health_check
- No retry in MCP layer — MCPClient's `_retry_with_backoff()` handles retries

## Consequences

### Positive

- **Zero blocking on HT-012**: Phase 5 can be fully implemented and tested using the Go bridge that is already running and authenticated.
- **Clean migration path**: Adding pywa requires implementing `PywaStub` → `PywaClient` + setting `WHATSAPP_BACKEND=pywa`. No changes to MCP tools, HITL Manager, or orchestrator.
- **Local-first**: Go bridge runs locally at `:8080` — no cloud dependency for message sending in Phase 5. Consistent with Constitution Principle II.
- **Testable via mocking**: `httpx` can be mocked with `httpx.MockTransport` in tests — no live bridge required for unit or integration tests.
- **Abstraction future-proofs Phase 6+**: If Meta WhatsApp Business API changes or Go bridge becomes unmaintained, swapping backends only requires a new `BridgeClient` implementation.

### Negative

- **Go bridge session fragility**: WhatsApp Web sessions can expire or get logged out by Meta. If `XXXXXXXXXXXX` number's WhatsApp Web session drops, the entire ingestion and notification pipeline fails until re-authenticated. Mitigation: `health_check` tool monitors session; orchestrator alerts owner.
- **Go bridge not officially supported**: Uses reverse-engineered WhatsApp Web protocol. Risk of sudden API breakage from Meta's end. Mitigation: pywa fallback path designed but deferred.
- **pywa requires VPS/ngrok for webhook**: When HT-012 is completed, the owner needs a public URL for Meta's webhook delivery — requires either ngrok (dev) or a cloud VPS (prod). This is a Phase 6+ concern but should be planned.
- **Number format normalization complexity**: E.164 → JID conversion in `GoBridge` adds a small transformation step that must be correctly handled for group JIDs, broadcast, and international numbers.

## Alternatives Considered

### Alternative A: pywa only (Meta Cloud API) — rejected for Phase 5
Use only pywa Cloud API; defer Go bridge as legacy.
- **Pro**: Meta-supported; stable; standard business API; production-grade webhook delivery.
- **Con**: HT-012 blocked (Meta developer account approval process, phone number verification, webhook hosting not available); would delay Phase 5 by weeks. Rejected — Go bridge unblocks Phase 5 immediately.

### Alternative B: whatsapp-web.js (Node.js library) — rejected
Use the Node.js whatsapp-web.js library directly from Python via subprocess.
- **Pro**: More actively maintained than some Go bridges; same WhatsApp Web protocol.
- **Con**: Node.js subprocess from Python is fragile; inconsistent with Python stack; session management complex; Go bridge is already running and tested. Rejected.

### Alternative C: Twilio WhatsApp API — rejected
Use Twilio's WhatsApp sandbox/production API.
- **Pro**: Reliable cloud service; good documentation; no Meta developer account required separately.
- **Con**: Paid service (cost per message); requires Twilio account and API credentials; cloud dependency violates local-first preference; sandbox limitations for testing. Rejected.

### Alternative D: No abstraction layer (hardcode Go bridge) — rejected
Skip `bridge.py` and inline Go bridge HTTP calls directly in `server.py`.
- **Pro**: Simpler code, fewer files.
- **Con**: Switching to pywa would require rewriting `server.py`; no clean test mock point; makes WHATSAPP_BACKEND env switch impossible. Rejected — abstraction cost is minimal (one file) for significant future-proofing benefit.

## References

- Feature Spec: `specs/008-hitl-whatsapp-silver/spec.md` (FR-001 through FR-011; SC-001, SC-008)
- Implementation Plan: `specs/008-hitl-whatsapp-silver/plan.md` (Phase B — WhatsApp Watcher; Phase C — WhatsApp MCP Server)
- Research: `specs/008-hitl-whatsapp-silver/research.md` (Decision 1)
- Contracts: `specs/008-hitl-whatsapp-silver/contracts/whatsapp-tools.json`
- Related ADRs: ADR-0001 (BaseWatcher pattern; WhatsApp watcher inherits), ADR-0005 (FastMCP + Pydantic v2 + stdio; WhatsApp MCP follows), ADR-0007 (MCPClient fallback — orchestrator calls WhatsApp MCP), ADR-0008 (error codes: send_failed, auth_required, mcp_unavailable)
- Human Tasks: `ai-control/HUMAN-TASKS.md` (HT-004 DONE; HT-012 PENDING)
- Evaluator Evidence: `history/prompts/hitl-whatsapp-silver/003-phase5-hitl-plan.plan.prompt.md`
