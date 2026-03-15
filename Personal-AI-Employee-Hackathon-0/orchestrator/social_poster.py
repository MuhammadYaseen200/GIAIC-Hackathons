"""Cross-platform social poster -- extends LinkedIn poster pattern for Facebook, Instagram, Twitter."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from orchestrator.run_until_complete import run_until_complete

logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "vault"))
SOCIAL_LOG = VAULT_PATH / "Logs" / "social_posts.jsonl"


def _log_social_event(platform: str, action: str, **kwargs) -> None:
    """Log social media action to JSONL."""
    SOCIAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "platform": platform,
        "action": action,
        **kwargs,
    }
    with SOCIAL_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


async def draft_and_notify(topic: str, platforms: list[str] | None = None) -> dict:
    """Draft a social post and send HITL notification for approval.

    Args:
        topic: Post topic/content
        platforms: List of platforms (default: ["facebook", "instagram"])

    Returns:
        dict with draft_path and status
    """
    if platforms is None:
        platforms = ["facebook", "instagram"]

    draft_dir = VAULT_PATH / "Pending_Approval"
    draft_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    draft_filename = f"social_post_{ts}.md"
    draft_path = draft_dir / draft_filename

    content = f"""---
type: social_post
platforms: {json.dumps(platforms)}
status: pending_approval
created_at: {datetime.utcnow().isoformat()}Z
topic: {topic}
---

# Draft Social Post

{topic}

---
*Awaiting HITL approval. Reply APPROVE or REJECT.*
"""
    draft_path.write_text(content)

    _log_social_event(
        platform=",".join(platforms),
        action="draft_created",
        draft_path=str(draft_path),
        topic=topic[:100],
    )

    # Send HITL notification via WhatsApp if available
    try:
        from mcp_servers.whatsapp.bridge import GoBridge
        bridge = GoBridge()
        msg = (
            f"Social post draft ready for approval:\n{topic[:200]}\n"
            f"Platforms: {', '.join(platforms)}\nReply APPROVE or REJECT."
        )
        await bridge.send(msg[:500])
    except Exception as e:
        logger.warning(f"WhatsApp HITL notification failed: {e}")

    return {"status": "pending_approval", "draft_path": str(draft_path)}


async def publish_approved(draft_path: Path, platform: str) -> dict:
    """Publish an approved draft to the specified platform."""
    try:
        content = draft_path.read_text()
        # Extract text from draft (between YAML frontmatter and end)
        lines = content.split("\n")
        text_lines: list[str] = []
        frontmatter_count = 0
        for line in lines:
            if line.strip() == "---":
                frontmatter_count += 1
                continue
            if frontmatter_count >= 2:
                text_lines.append(line)
        text = "\n".join(text_lines).strip()

        result: dict | None = None

        async def _do_post() -> None:
            nonlocal result
            if platform == "facebook":
                from mcp_servers.facebook.client import post_to_facebook
                result = await post_to_facebook(text)
            elif platform == "instagram":
                from mcp_servers.facebook.client import post_to_instagram
                result = await post_to_instagram(text)
            elif platform == "twitter":
                from mcp_servers.twitter.client import post_tweet
                result = await post_tweet(text[:280])
            elif platform == "linkedin":
                logger.info("LinkedIn posting via linkedin_poster.py")
                result = {"success": True, "platform": "linkedin", "note": "Use linkedin_poster.py"}
            if result and not result.get("success", True):
                raise RuntimeError(result.get("error", "Post failed"))

        ruc_result = await run_until_complete(
            workflow_name=f"social_poster.{platform}",
            steps=[(f"post_{platform}", _do_post)],
            max_retries=3,
        )
        if ruc_result["status"] == "failed":
            result = {"success": False, "error": ruc_result.get("error", "max retries exceeded")}

        if result:
            _log_social_event(
                platform=platform,
                action="published",
                success=result.get("success", False),
                post_id=result.get("post_id", ""),
            )

        # Move draft to Done
        done_dir = VAULT_PATH / "Done"
        done_dir.mkdir(parents=True, exist_ok=True)
        draft_path.rename(done_dir / draft_path.name)

        return result or {"success": False, "error": "Unknown platform"}

    except Exception as e:
        logger.error(f"publish_approved error: {e}", exc_info=True)
        _log_social_event(platform=platform, action="publish_error", error=str(e))
        return {"success": False, "error": str(e)}
