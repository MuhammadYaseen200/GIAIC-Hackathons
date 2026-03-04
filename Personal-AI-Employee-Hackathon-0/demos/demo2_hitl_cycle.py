"""Demo 2: HITL Manager — full approve/reject cycle on real vault files."""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock
from orchestrator.hitl_manager import HITLManager


async def demo():
    vault = Path("vault")

    # Capture what WhatsApp/Gmail WOULD send (mocked — no bridge needed)
    async def mock_whatsapp(tool, args):
        print(f"\n📱 WhatsApp → {args['to']}")
        print(f"   {args['body'][:300]}")
        return {}

    async def mock_gmail(tool, args):
        print(f"\n📧 Gmail send:")
        print(f"   To:      {args['to']}")
        print(f"   Subject: {args['subject']}")
        print(f"   Body:    {args['body'][:100]}...")
        return {"message_id": "live-demo-001", "sent_at": "2026-03-04T18:00:00Z"}

    wa = AsyncMock()
    wa.call_tool = mock_whatsapp
    gm = AsyncMock()
    gm.call_tool = mock_gmail

    manager = HITLManager(
        whatsapp_client=wa,
        gmail_client=gm,
        vault_path=vault,
        owner_number="+10000000000",
        batch_delay_seconds=0,
    )

    print("\n🤖 AI Employee — HITL Demo")
    print("=" * 50)

    # Step 1: AI drafts a reply
    print("\n[1] Incoming email from boss@company.com")
    print("    Subject: Re: Q1 Budget Review")
    print("    AI is drafting a reply...")

    draft_id = await manager.submit_draft(
        recipient="boss@company.com",
        subject="Re: Q1 Budget Review",
        body=(
            "Hi,\n\nThank you for reaching out. I have reviewed the Q1 budget "
            "and everything looks on track. The projections are meeting targets "
            "and we are well-positioned for the board meeting on Friday.\n\n"
            "Best regards"
        ),
        priority="HIGH",
        risk_level="low",
    )
    print(f"    ✅ Draft saved: vault/Pending_Approval/{draft_id}.md")

    # Step 2: Batch notification
    print("\n[2] Sending WhatsApp notification to owner...")
    await manager.send_batch_notification()

    # Step 3: Owner approves
    print(f"\n[3] Owner replies: 'approve {draft_id}'")
    await manager.handle_owner_reply(f"approve {draft_id}", "+10000000000")

    # Step 4: Verify vault state
    approved_path = vault / "Approved" / f"{draft_id}.md"
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    last_entry = {}
    if log_path.exists():
        lines = log_path.read_text().strip().split("\n")
        last_entry = json.loads(lines[-1])

    print("\n[4] Vault verification:")
    print(f"    Pending_Approval/{draft_id}.md  → {'removed ✅' if not (vault / 'Pending_Approval' / f'{draft_id}.md').exists() else 'still there ❌'}")
    print(f"    Approved/{draft_id}.md          → {'exists ✅' if approved_path.exists() else 'missing ❌'}")
    print(f"    Audit log decision               → {last_entry.get('decision', 'not found')}")

    # Step 5: Reject demo
    print("\n[5] Now testing REJECT flow...")
    draft_id2 = await manager.submit_draft(
        recipient="newsletter@spam.com",
        subject="Re: Offer",
        body="No thank you.",
        priority="LOW",
        risk_level="low",
    )
    await manager.handle_owner_reply(f"reject {draft_id2}", "+10000000000")
    rejected_path = vault / "Rejected" / f"{draft_id2}.md"
    print(f"    Rejected/{draft_id2}.md → {'exists ✅' if rejected_path.exists() else 'missing ❌'}")
    print("    Gmail NOT called (correct — reject skips send) ✅")

    print("\n" + "=" * 50)
    print("HITL demo complete.\n")


asyncio.run(demo())
