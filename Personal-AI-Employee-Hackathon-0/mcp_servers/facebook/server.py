"""Facebook/Instagram MCP Server -- FastMCP tools for Meta platforms."""
from __future__ import annotations

import os as _os, sys as _sys
_PROJECT_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _PROJECT_ROOT not in _sys.path:
    _sys.path.insert(0, _PROJECT_ROOT)

import json
import logging

from mcp.server.fastmcp import FastMCP

from mcp_servers.facebook.client import (
    post_to_facebook,
    post_to_instagram,
    get_recent_facebook_posts,
    health_check_meta,
)
from mcp_servers.facebook.models import (
    FacebookPostInput,
    InstagramMediaInput,
    PostResult,
    RecentPostsResult,
    FacebookHealthResult,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("facebook")


def _error(msg: str) -> dict:
    return {"isError": True, "content": json.dumps({"error": msg})}


from mcp_servers.hitl_utils import check_hitl_approval as _check_hitl_approval


@mcp.tool()
async def post_update(text: str, visibility: str = "EVERYONE") -> dict:
    """Post to both Facebook and Instagram.

    Args:
        text: Post content (Facebook <=63206 chars, auto-truncated for Instagram <=2200)
        visibility: EVERYONE or FRIENDS (Facebook only)
    """
    hitl_check = _check_hitl_approval()
    if hitl_check:
        return hitl_check
    try:
        try:
            FacebookPostInput(text=text, visibility=visibility)  # type: ignore
        except Exception as e:
            return _error(f"Validation error: {e}")

        fb_result = await post_to_facebook(text)

        ig_caption = text[:2200] if len(text) > 2200 else text
        ig_result = await post_to_instagram(ig_caption)

        return {"content": json.dumps({"facebook": fb_result, "instagram": ig_result})}
    except Exception as e:
        logger.error(f"post_update error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def post_facebook_only(text: str) -> dict:
    """Post to Facebook Page only.

    Args:
        text: Post content (<=63206 chars)
    """
    hitl_check = _check_hitl_approval()
    if hitl_check:
        return hitl_check
    try:
        try:
            FacebookPostInput(text=text)
        except Exception as e:
            return _error(f"Validation error: {e}")
        result = await post_to_facebook(text)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"post_facebook_only error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def post_instagram_only(caption: str, image_url: str | None = None) -> dict:
    """Post to Instagram only (requires INSTAGRAM_BUSINESS_ACCOUNT_ID).

    Args:
        caption: Post caption (<=2200 chars)
        image_url: Optional image URL for media posts
    """
    hitl_check = _check_hitl_approval()
    if hitl_check:
        return hitl_check
    try:
        try:
            InstagramMediaInput(caption=caption, image_url=image_url)
        except Exception as e:
            return _error(f"Validation error: {e}")
        result = await post_to_instagram(caption, image_url)
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"post_instagram_only error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def get_recent_posts(limit: int = 10) -> dict:
    """Get recent posts from the Facebook Page.

    Args:
        limit: Number of posts to return (default: 10)
    """
    try:
        posts = await get_recent_facebook_posts(limit)
        result = RecentPostsResult(success=True, posts=posts)  # type: ignore
        return {"content": json.dumps(result.model_dump())}
    except Exception as e:
        logger.error(f"get_recent_posts error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


@mcp.tool()
async def health_check() -> dict:
    """Check Facebook/Instagram MCP connectivity and token validity."""
    try:
        result = await health_check_meta()
        return {"content": json.dumps(result)}
    except Exception as e:
        logger.error(f"health_check error: {e}", exc_info=True)
        return _error(f"Unexpected error: {e}")


if __name__ == "__main__":
    mcp.run()
