"""LinkedIn API v2 adapter. All API calls go through this module (ADR-0004/MCP-First)."""
import logging

import httpx

from mcp_servers.linkedin.auth import get_access_token, get_person_urn, reset_credentials_cache

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com"
UGC_POSTS_URL = f"{LINKEDIN_API_BASE}/v2/ugcPosts"
PROFILE_URL = f"{LINKEDIN_API_BASE}/v2/userinfo"  # OIDC userinfo — returns 'sub' as person ID


class LinkedInAPIError(Exception):
    """Non-2xx response from LinkedIn API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"LinkedIn API {status_code}: {detail}")


def _make_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


async def post_to_linkedin(text: str, visibility: str = "PUBLIC") -> dict:
    """
    POST to LinkedIn UGC Posts endpoint.
    Returns response JSON on success.
    Raises LinkedInAPIError on 4xx/5xx (except 401 which triggers refresh).
    Raises httpx.TimeoutException on network timeout.
    """
    person_urn = get_person_urn()
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        token = get_access_token()
        resp = await client.post(UGC_POSTS_URL, headers=_make_headers(token), json=payload)

        if resp.status_code == 401:
            # Token expired mid-request — force refresh and retry once
            logger.info("LinkedIn 401 — forcing token refresh and retrying.")
            reset_credentials_cache()
            token = get_access_token()
            resp = await client.post(UGC_POSTS_URL, headers=_make_headers(token), json=payload)

        if not resp.is_success:
            raise LinkedInAPIError(resp.status_code, resp.text[:500])

        # 201 Created — LinkedIn returns post ID in X-RestLi-Id header
        post_id = resp.headers.get("X-RestLi-Id", "")
        return {"post_id": post_id, "raw": resp.json() if resp.content else {}}


async def get_profile() -> dict:
    """GET /v2/userinfo — returns OIDC profile fields (sub, name, email)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        token = get_access_token()
        resp = await client.get(
            PROFILE_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 401:
            reset_credentials_cache()
            token = get_access_token()
            resp = await client.get(
                PROFILE_URL,
                headers={"Authorization": f"Bearer {token}"},
            )
        if not resp.is_success:
            raise LinkedInAPIError(resp.status_code, resp.text[:500])
        return resp.json()


async def health_check_api() -> bool:
    """Ping LinkedIn API. Returns True if reachable, False otherwise."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                timeout=5.0,
                headers={"Authorization": f"Bearer {get_access_token()}"},
            )
            return resp.status_code in (200, 401)  # 401 = reachable but expired (ok for health)
    except Exception:
        return False
