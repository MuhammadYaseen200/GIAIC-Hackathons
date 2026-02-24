"""Integration tests for all 5 Obsidian MCP tools.

Uses tmp_path pytest fixture as vault root. Tests real filesystem operations.
No mocking — direct ObsidianTools calls against a real tmp directory.
"""
import pytest
from pathlib import Path


@pytest.fixture
def vault(tmp_path):
    """Create a complete vault directory structure."""
    for d in ["Needs_Action", "Done", "Drafts", "Approved", "Logs"]:
        (tmp_path / d).mkdir()
    return tmp_path


# ── write_note ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_write_note_creates_file(vault):
    """write_note creates a .md file at the vault-relative path."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    result = await tools.write_note(
        "Needs_Action/email-001.md",
        {"status": "pending", "from": "boss@corp.com"},
        "Please review the attached proposal.",
    )
    assert "error" not in result
    file_path = vault / "Needs_Action" / "email-001.md"
    assert file_path.exists(), "File must be created on disk"
    content = file_path.read_text(encoding="utf-8")
    assert "status" in content
    assert "Please review the attached proposal." in content


@pytest.mark.asyncio
async def test_write_note_overwrites_existing(vault):
    """write_note is idempotent — overwrites existing file."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/note.md", {"v": 1}, "Version 1")
    await tools.write_note("Needs_Action/note.md", {"v": 2}, "Version 2")

    result = await tools.read_note("Needs_Action/note.md")
    assert result["frontmatter"]["v"] == 2
    assert result["body"] == "Version 2"


# ── read_note ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_read_note_returns_correct_frontmatter_and_body(vault):
    """read_note returns exactly the frontmatter and body written."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    fm = {"status": "pending", "priority": "urgent", "email_id": "abc-123"}
    body = "This is the full email body.\n\nWith multiple paragraphs."

    await tools.write_note("Needs_Action/complete.md", fm, body)
    result = await tools.read_note("Needs_Action/complete.md")

    assert result["frontmatter"]["status"] == "pending"
    assert result["frontmatter"]["priority"] == "urgent"
    assert result["frontmatter"]["email_id"] == "abc-123"
    assert result["body"] == body


@pytest.mark.asyncio
async def test_read_note_not_found(vault):
    """read_note returns not_found for nonexistent file."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).read_note("Needs_Action/ghost.md")
    assert result["error"] == "not_found"


# ── list_notes ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_notes_returns_all_files(vault):
    """list_notes returns all .md files in the directory."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/a.md", {"status": "pending"}, "")
    await tools.write_note("Needs_Action/b.md", {"status": "done"}, "")
    await tools.write_note("Needs_Action/c.md", {"status": "pending"}, "")

    result = await tools.list_notes("Needs_Action")
    assert result["count"] == 3
    paths = [n["path"] for n in result["notes"]]
    assert "Needs_Action/a.md" in paths
    assert "Needs_Action/b.md" in paths
    assert "Needs_Action/c.md" in paths


@pytest.mark.asyncio
async def test_list_notes_filter_returns_matching_only(vault):
    """list_notes with filter only returns notes matching frontmatter field:value."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/pending1.md", {"status": "pending"}, "")
    await tools.write_note("Needs_Action/pending2.md", {"status": "pending"}, "")
    await tools.write_note("Needs_Action/done1.md", {"status": "done"}, "")

    result = await tools.list_notes("Needs_Action", filter="status:pending")
    assert result["count"] == 2
    paths = [n["path"] for n in result["notes"]]
    assert all("pending" in p for p in paths)
    assert not any("done" in p for p in paths)


# ── move_note ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_note_moves_file_and_source_gone(vault):
    """move_note: source no longer exists, destination exists."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/to-archive.md", {"status": "done"}, "Email body.")

    result = await tools.move_note("Needs_Action/to-archive.md", "Done/to-archive.md")
    assert result["moved"] is True
    assert not (vault / "Needs_Action" / "to-archive.md").exists(), "Source must be gone"
    assert (vault / "Done" / "to-archive.md").exists(), "Destination must exist"


@pytest.mark.asyncio
async def test_move_note_preserves_content(vault):
    """move_note: content is identical after move."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    fm = {"status": "done", "message_id": "msg-999"}
    body = "Body preserved after move."
    await tools.write_note("Needs_Action/preserve.md", fm, body)

    await tools.move_note("Needs_Action/preserve.md", "Done/preserve.md")
    result = await tools.read_note("Done/preserve.md")
    assert result["frontmatter"]["message_id"] == "msg-999"
    assert result["body"] == body


# ── search_notes ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_notes_finds_text_in_body(vault):
    """search_notes finds query text in note body."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/searchme.md", {}, "The quick brown fox jumps")
    await tools.write_note("Needs_Action/other.md", {}, "Nothing relevant here")

    result = await tools.search_notes("quick brown fox")
    assert result["count"] >= 1
    paths = [n["path"] for n in result["notes"]]
    assert any("searchme" in p for p in paths)


@pytest.mark.asyncio
async def test_search_notes_searches_across_subdirs(vault):
    """search_notes searches recursively across vault subdirectories."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/na.md", {}, "FINDME in needs_action")
    await tools.write_note("Done/done.md", {}, "FINDME in done")

    result = await tools.search_notes("FINDME")
    assert result["count"] == 2


@pytest.mark.asyncio
async def test_search_notes_returns_empty_on_no_match(vault):
    """search_notes returns count=0 and empty list when nothing matches."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/note.md", {}, "Nothing here")

    result = await tools.search_notes("zzzznotfound99999")
    assert result["count"] == 0
    assert result["notes"] == []
