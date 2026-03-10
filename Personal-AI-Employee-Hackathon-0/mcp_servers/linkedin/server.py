"""LinkedIn MCP server — FastMCP pattern (ADR-0005).

Tools:
  - post_update(text, visibility) → PostUpdateResult
  - get_profile() → ProfileResult
  - health_check() → HealthCheckResult
"""
import json
import logging
import time

from mcp.server.fastmcp import FastMCP

from mcp_servers.linkedin.auth import AuthRequiredError, get_linkedin_credentials
from mcp_servers.linkedin.client import (
    LinkedInAPIError,
    get_profile as client_get_profile,
    health_check_api,
    post_to_linkedin,
)
from mcp_servers.linkedin.models import (
    HealthCheckResult,
    PostUpdateInput,
    PostUpdateResult,
    ProfileResult,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("linkedin")


def _error(msg: str) -> dict:
    return {"isError": True, "content": json.dumps({"error": msg})}


@mcp.tool()
async def post_update(text: str, visibility: str = "PUBLIC") -> dict:
    """Post an update to LinkedIn. Requires HITL approval before calling (ADR-0011)."""
    try:
        validated = PostUpdateInput(text=text, visibility=visibility)
    except Exception as e:
        return _error(f"Validation error: {e}")

    try:
        result = await post_to_linkedin(validated.text, validated.visibility)
        return {
            "content": json.dumps(
                PostUpdateResult(
                    success=True,
                    post_id=result.get("post_id"),
                ).model_dump()
            )
        }
    except AuthRequiredError as e:
        return _error(f"Auth required: {e}")
    except LinkedInAPIError as e:
        return _error(f"LinkedIn API error {e.status_code}: {e.detail}")
    except Exception as e:
        logger.error(f"post_update unexpected error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def get_profile() -> dict:
    """Get LinkedIn profile info for the authenticated user."""
    try:
        data = await client_get_profile()
        person_id = data.get("sub", data.get("id", ""))  # OIDC uses 'sub'; legacy uses 'id'
        name_parts = [data.get("given_name", data.get("localizedFirstName", "")),
                      data.get("family_name", data.get("localizedLastName", ""))]
        return {
            "content": json.dumps(
                ProfileResult(
                    success=True,
                    person_urn=f"urn:li:person:{person_id}" if person_id else None,
                    display_name=" ".join(p for p in name_parts if p).strip() or None,
                ).model_dump()
            )
        }
    except AuthRequiredError as e:
        return _error(f"Auth required: {e}")
    except LinkedInAPIError as e:
        return _error(f"LinkedIn API error {e.status_code}: {e.detail}")
    except Exception as e:
        logger.error(f"get_profile unexpected error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def health_check() -> dict:
    """Check LinkedIn MCP server health: token validity + API reachability."""
    try:
        creds = get_linkedin_credentials()
        token_valid = True
        expires_in = max(0, int(creds.expires_at - time.time()))
    except AuthRequiredError:
        token_valid = False
        expires_in = None
    except Exception:
        token_valid = False
        expires_in = None

    try:
        api_reachable = await health_check_api()
    except Exception:
        api_reachable = False

    healthy = token_valid and api_reachable
    return {
        "content": json.dumps(
            HealthCheckResult(
                healthy=healthy,
                token_valid=token_valid,
                token_expires_in_seconds=expires_in,
                api_reachable=api_reachable,
            ).model_dump()
        )
    }


if __name__ == "__main__":
    mcp.run()
