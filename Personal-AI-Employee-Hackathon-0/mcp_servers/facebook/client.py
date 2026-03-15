"""Facebook/Instagram async client using Meta Graph API."""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")


async def post_to_facebook(text: str) -> dict:
    """Post to Facebook Page feed."""
    if not PAGE_ACCESS_TOKEN:
        return {"success": False, "error": "FACEBOOK_PAGE_ACCESS_TOKEN not set", "platform": "facebook"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GRAPH_API_BASE}/{PAGE_ID}/feed",
                json={"message": text, "access_token": PAGE_ACCESS_TOKEN},
            )
            response.raise_for_status()
            data = response.json()
            post_id = data.get("id", "")
            return {
                "success": True,
                "post_id": post_id,
                "url": f"https://www.facebook.com/{post_id.replace('_', '/posts/')}",
                "platform": "facebook",
                "error": None,
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (400, 401, 403):
            logger.error(f"Facebook auth/permission error: {e.response.text}")
            return {"success": False, "error": f"Auth error: {e.response.status_code}", "platform": "facebook"}
        return {"success": False, "error": str(e), "platform": "facebook"}
    except Exception as e:
        logger.error(f"post_to_facebook error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "platform": "facebook"}


async def post_to_instagram(caption: str, image_url: str | None = None) -> dict:
    """Post to Instagram via 2-step container publish."""
    if not IG_ACCOUNT_ID:
        return {"success": False, "skipped": True, "reason": "no_ig_account",
                "status": "skipped", "platform": "instagram"}
    if not PAGE_ACCESS_TOKEN:
        return {"success": False, "error": "FACEBOOK_PAGE_ACCESS_TOKEN not set", "platform": "instagram"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Create media container
            container_payload: dict = {
                "caption": caption,
                "access_token": PAGE_ACCESS_TOKEN,
            }
            if image_url:
                container_payload["image_url"] = image_url
                container_payload["media_type"] = "IMAGE"
            else:
                container_payload["media_type"] = "REELS"
                logger.warning("Instagram text-only posts require video/image -- skipping image")

            container_resp = await client.post(
                f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media",
                json=container_payload,
            )
            if container_resp.status_code != 200:
                return {"success": False,
                        "error": f"Container creation failed: {container_resp.text}",
                        "platform": "instagram"}

            container_id = container_resp.json().get("id")

            # Step 2: Publish container
            publish_resp = await client.post(
                f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media_publish",
                json={"creation_id": container_id, "access_token": PAGE_ACCESS_TOKEN},
            )
            if publish_resp.status_code != 200:
                return {"success": False,
                        "error": f"Publish failed: {publish_resp.text}",
                        "platform": "instagram"}

            media_id = publish_resp.json().get("id", "")
            return {
                "success": True,
                "post_id": media_id,
                "url": f"https://www.instagram.com/p/{media_id}/",
                "platform": "instagram",
                "error": None,
            }
    except Exception as e:
        logger.error(f"post_to_instagram error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "platform": "instagram"}


async def get_recent_facebook_posts(limit: int = 10) -> list:
    """Fetch recent posts from the Facebook Page."""
    if not PAGE_ACCESS_TOKEN:
        return []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/{PAGE_ID}/feed",
                params={
                    "fields": "id,message,created_time",
                    "limit": limit,
                    "access_token": PAGE_ACCESS_TOKEN,
                },
            )
            response.raise_for_status()
            data = response.json()
            posts = []
            for p in data.get("data", []):
                posts.append({
                    "post_id": p.get("id", ""),
                    "message": p.get("message", ""),
                    "created_time": p.get("created_time", ""),
                    "platform": "facebook",
                })
            return posts
    except Exception as e:
        logger.error(f"get_recent_facebook_posts error: {e}", exc_info=True)
        return []


async def health_check_meta() -> dict:
    """Check Meta Graph API connectivity and token validity."""
    if not PAGE_ACCESS_TOKEN:
        return {"healthy": False, "page_reachable": False, "token_valid": False,
                "error": "FACEBOOK_PAGE_ACCESS_TOKEN not set"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={"access_token": PAGE_ACCESS_TOKEN, "fields": "id,name"},
            )
            if response.status_code == 200:
                return {"healthy": True, "page_reachable": True, "token_valid": True, "error": None}
            return {"healthy": False, "page_reachable": True, "token_valid": False,
                    "error": f"Token invalid: {response.status_code}"}
    except httpx.ConnectError as e:
        return {"healthy": False, "page_reachable": False, "token_valid": False, "error": str(e)}
    except Exception as e:
        return {"healthy": False, "page_reachable": False, "token_valid": False, "error": str(e)}
