# ADR-0017: Social Media MCP Architecture — Separate vs Unified Server

- **Status:** Accepted
- **Date:** 2026-03-11
- **Feature:** ceo-briefing-odoo-gold (Phase 6)
- **Context:** Phase 6 integrates three social platforms (Facebook Page, Instagram Business,
  Twitter/X) alongside the existing LinkedIn MCP server (Phase 5.5). Each platform has a
  distinct authentication mechanism, token lifecycle, rate limit regime, and API surface.
  A key architectural choice is whether to build one unified "social MCP" server or three
  separate servers. This decision determines failure isolation, deployment topology, token
  management, and test boundary design.

## Decision

Build **three separate FastMCP servers** — one per platform — following the existing
`mcp_servers/linkedin/` pattern:

- `mcp_servers/facebook/server.py` — Meta Graph API (Facebook Page + Instagram Business via shared Page Access Token)
- `mcp_servers/twitter/server.py` — Twitter API v2 via tweepy + OAuth 1.0a
- (Existing) `mcp_servers/linkedin/server.py` — LinkedIn UGC Posts API

Facebook and Instagram share one server because they share one credential (Page Access Token
from Meta Developer App) and one API endpoint domain (graph.facebook.com). Twitter/X is
separate because it uses a completely different auth stack (OAuth 1.0a via tweepy) and API
domain.

Each server exposes: `post_update`, `get_recent_posts`, `health_check` (minimal consistent interface).

## Consequences

### Positive

- **Independent failure domains**: Twitter rate-limit or outage does not affect Facebook/Instagram posting; each server crashes/restarts independently
- **Independent token lifecycle**: Each server manages its own credentials; a token revocation on one platform does not affect others
- **Granular `health_check` per platform**: Orchestrator can selectively degrade (skip Twitter, post to Facebook) rather than failing all social actions together
- **Independent test boundaries**: `tests/unit/test_facebook_mcp.py` and `tests/unit/test_twitter_mcp.py` mock only their own platform; no cross-platform test contamination
- **Mirrors existing pattern**: `mcp_servers/linkedin/` already established this architecture; four consistent MCP servers reinforce the pattern rather than introducing a new abstraction
- **Separate `~/.claude.json` entries**: Each server can be restarted independently without disrupting other platforms

### Negative

- Three codebases to maintain instead of one (mitigated: shared Pydantic v2 model patterns and httpx client pattern mean each server is ~150 lines)
- Three MCP server processes running concurrently (resource cost: minimal — each is a lightweight FastMCP process)
- Cross-platform summary (e.g., "post to all platforms at once") requires orchestrator-level fan-out rather than a single MCP tool call

## Alternatives Considered

**Alternative A: One unified `social_mcp` server with platform selector parameter**
```python
@mcp.tool()
async def post_update(text: str, platforms: list[str] = ["facebook", "twitter"]) -> dict: ...
```
- Rejected: A single auth failure (e.g., Twitter token expired) would return a mixed partial-success
  result that callers must parse carefully. Error handling complexity grows O(n) with platform count.
  One server crash = all platforms unreachable. Conflicts with ADR-0008 (typed error contract) since
  the error shape becomes ambiguous (which platform failed?).

**Alternative B: Two servers — Meta (Facebook+Instagram) + Twitter, separate from LinkedIn**
- Meta platforms sharing one server (✅ accepted — same credential/API domain)
- Twitter as separate server (✅ accepted)
- Difference from decision: this IS the decision; LinkedIn is the existing Phase 5.5 server not rebuilt

**Alternative C: Platform-agnostic base class + 3 subclass servers**
- Object-oriented inheritance in Python; share `BaseSocialMCP` with `post_update()` abstract method
- Rejected: FastMCP tool registration is function-level, not class-level; inheritance would require
  awkward registration workarounds. Adds complexity without structural benefit vs copy-paste + adjust.

## References

- Feature Spec: `specs/010-ceo-briefing-odoo-gold/spec.md` (FR-014–FR-021)
- Implementation Plan: `specs/010-ceo-briefing-odoo-gold/plan.md` (Phase C, D)
- Related ADRs: ADR-0005 (FastMCP framework stack), ADR-0007 (MCP fallback protocol), ADR-0008 (typed MCP error contract), ADR-0014 (LinkedIn OAuth2 pattern — template for social auth)
- Evaluator Evidence: `history/prompts/ceo-briefing-odoo-gold/002-phase6-gold-clarify-social-ralph.clarify.prompt.md` (Q1+Q2 answers: custom MCPs confirmed, Facebook Page + Instagram Business account type)
