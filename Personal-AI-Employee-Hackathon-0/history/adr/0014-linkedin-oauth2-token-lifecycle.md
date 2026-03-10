# ADR-0014: LinkedIn OAuth2 Token Lifecycle Strategy

> **Scope**: Defines how the LinkedIn MCP server authenticates with the LinkedIn API — OAuth2 scope selection, token storage, automatic refresh strategy, and credential security model.

- **Status:** Accepted
- **Date:** 2026-03-05
- **Feature:** linkedin-cron-silver (009)
- **Context:** The LinkedIn MCP server must post to LinkedIn on behalf of the owner without interactive prompts. LinkedIn's API v2 uses OAuth2 Authorization Code flow. Unlike Gmail (ADR-0006, using Google's library with built-in refresh), LinkedIn has its own token endpoint (`https://www.linkedin.com/oauth/v2/accessToken`) and requires explicit `offline_access` scope to obtain a refresh token. Without a refresh token, the 60-day access token eventually expires and requires manual re-authentication — violating SC-010 (95% auto-refresh success). The clarification session (2026-03-05) confirmed: auto-refresh is required; `offline_access` scope must be requested during initial auth.

## Decision

Implement LinkedIn OAuth2 using **Authorization Code flow with `offline_access` scope**, storing both access and refresh tokens in `linkedin_token.json`, with automatic silent refresh on 401 responses:

- **Scopes requested**: `r_liteprofile w_member_social offline_access` — minimum required for profile read + post creation + refresh token issuance
- **Initial auth**: `scripts/linkedin_auth.py` runs Authorization Code flow in browser (one-time human task HT-013); stores `linkedin_token.json` in project root (gitignored)
- **Token file format**: `{"access_token": "...", "refresh_token": "...", "expires_at": <unix_timestamp>, "token_type": "Bearer"}`
- **Singleton auth**: Module-level `_linkedin_credentials` cached after first load (same pattern as ADR-0006 Gmail singleton) — initialized at MCP server startup via FastMCP lifespan
- **Auto-refresh trigger**: On any `401 Unauthorized` or detected token expiry (compare `expires_at` to `now()`), call `POST https://www.linkedin.com/oauth/v2/accessToken` with `grant_type=refresh_token` before retrying
- **Atomic save**: Refreshed tokens written via `watchers/utils.atomic_write` to prevent corrupt `linkedin_token.json` on crash mid-refresh
- **Credential security**: `linkedin_token.json` is gitignored; `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` stored in `.env` only; tokens NEVER written to vault files or logs (enforces FR-009)
- **Refresh failure handling**: If refresh fails (revoked token, LinkedIn API down), raise `AuthRequiredError` with message directing owner to re-run `scripts/linkedin_auth.py`; notify via WhatsApp; no crash

## Consequences

### Positive

- **SC-010 satisfied**: Auto-refresh enables 95%+ token renewal without owner intervention — the invariant holds as long as the refresh token is not manually revoked
- **No daily interruption**: Owner never needs to re-auth for normal operation; only revocation or scope changes require manual re-auth
- **Consistent pattern**: Mirrors ADR-0006 (Gmail) singleton + atomic save — no new patterns introduced; existing test mocking strategies apply
- **Credential safety**: `offline_access` refresh tokens are long-lived (LinkedIn does not expire them on access token refresh) — one auth flow can last months
- **Testable**: Mock `get_linkedin_credentials()` + `reset_credentials_cache()` gives full test isolation; SC-008 (>80% coverage) achievable

### Negative

- **Refresh token revocation is fatal**: If the owner revokes LinkedIn app access (via linkedin.com settings), all auto-refresh attempts fail silently until WhatsApp notification fires — period between revocation and notification is a blind spot
- **`offline_access` scope requires LinkedIn app review for public apps**: For personal developer apps (which this is), `offline_access` is available without review — but if the app is ever promoted to production status, LinkedIn may require formal review
- **Singleton is global state**: Same concern as ADR-0006 — tests MUST call `reset_credentials_cache()` between runs; no multi-account support
- **WSL2 browser launch**: Initial `scripts/linkedin_auth.py` auth flow requires browser — on WSL2 this may need `BROWSER` env var or manual URL copy-paste (mitigated by HT-013 completion note)

## Alternatives Considered

**Alternative A: Access token only (no offline_access, no refresh)**
- Mechanism: Store only `LINKEDIN_ACCESS_TOKEN` in `.env`; manually rotate every 60 days
- Pros: Simpler auth.py; no refresh token stored on disk; no `offline_access` scope needed
- Cons: Violates SC-010 (requires manual intervention every 60 days); owner must remember to rotate or all LinkedIn posting silently fails; not autonomous
- Rejected: Directly violates SC-010 and the Silver tier "autonomous" requirement

**Alternative B: Use `python-linkedin-v2` or `linkedin-api` library**
- Mechanism: Third-party library handles token management
- Pros: Less auth boilerplate
- Cons: Third-party libraries for LinkedIn API are often unmaintained (LinkedIn deprecated v1 API, breaking most libraries); adds unaudited dependency; Constitution Principle IV requires MCP-first, not library-first; ADR-0005 established httpx as the HTTP client
- Rejected: Library maintenance risk; violates MCP-first principle; httpx + manual OAuth2 gives full control

**Alternative C: Long-lived token with proactive expiry warning (no auto-refresh)**
- Mechanism: Check `expires_at` daily; send WhatsApp warning 7 days before expiry; let owner manually refresh
- Pros: No refresh token on disk; simpler auth flow
- Cons: Still requires owner action; 7-day window is tight if owner is unavailable; post failures during expiry window violate SC-010
- Rejected: Does not satisfy SC-010; insufficient autonomy for Silver tier

**Alternative D: Store credentials in OS keychain**
- Mechanism: `keyring` library; tokens stored in system keychain not filesystem
- Pros: More secure than file-based token.json
- Cons: WSL2 keychain integration unreliable (same issue noted in ADR-0006 Alternative D); adds dependency; over-engineered for local single-user deployment
- Rejected: WSL2 reliability; over-engineering; consistent with ADR-0006 rejection of same approach

## References

- Feature Spec: `specs/009-linkedin-cron-silver/spec.md` (FR-009, SC-010, Clarifications 2026-03-05 Q1)
- Related ADRs: ADR-0006 (Gmail OAuth2 singleton pattern — identical approach adapted for LinkedIn), ADR-0005 (FastMCP + httpx stack)
- Human Tasks: `ai-control/HUMAN-TASKS.md` HT-013 (LinkedIn Developer App — DONE 2026-03-05)
- LinkedIn API Docs: OAuth2 Authorization Code flow, `offline_access` scope reference
