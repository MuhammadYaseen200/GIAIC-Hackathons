"""Contract tests for all 6 Obsidian MCP tools.

Key contracts:
  - write_note → read_note round-trip: frontmatter and body identical
  - not_found when path missing
  - permission_denied when path traversal attempted
  - list_notes with filter only returns matching notes
  - search_notes returns notes list + snippet
  - move_note: moved=True, source no longer exists
"""
import pytest
from pathlib import Path


@pytest.fixture
def vault(tmp_path):
    """A temporary vault directory."""
    (tmp_path / "Needs_Action").mkdir()
    (tmp_path / "Done").mkdir()
    return tmp_path


# ── health_check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_ok(vault):
    """health_check returns status=ok when vault exists."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).health_check()
    assert result["status"] == "ok"
    assert "vault_path" in result
    assert "note_count" in result
    assert "error" not in result


@pytest.mark.asyncio
async def test_health_check_vault_missing(tmp_path):
    """health_check returns not_found when vault doesn't exist."""
    from mcp_servers.obsidian.tools import ObsidianTools
    missing = tmp_path / "nonexistent"
    result = await ObsidianTools(missing).health_check()
    assert result["error"] == "not_found"


# ── write_note + read_note round-trip ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_write_read_roundtrip(vault):
    """write_note → read_note: frontmatter and body are identical."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)

    fm = {"status": "pending", "priority": "high", "tags": ["test"]}
    body = "This is the note body with special chars: ñ, 中文."

    write_result = await tools.write_note("Needs_Action/test-note.md", fm, body)
    assert write_result["path"] == "Needs_Action/test-note.md"
    assert "error" not in write_result

    read_result = await tools.read_note("Needs_Action/test-note.md")
    assert "error" not in read_result
    assert read_result["frontmatter"]["status"] == "pending"
    assert read_result["frontmatter"]["priority"] == "high"
    assert read_result["body"] == body


@pytest.mark.asyncio
async def test_write_note_creates_parent_dirs(vault):
    """write_note creates intermediate directories automatically."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    result = await tools.write_note("deep/nested/dir/note.md", {"status": "ok"}, "body")
    assert "error" not in result
    assert (vault / "deep" / "nested" / "dir" / "note.md").exists()


# ── read_note ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_read_note_not_found(vault):
    """read_note returns not_found for missing file."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).read_note("nonexistent.md")
    assert result["error"] == "not_found"
    assert "message" in result


@pytest.mark.asyncio
async def test_read_note_permission_denied_path_traversal(vault):
    """read_note returns permission_denied for ../../../etc/passwd style paths."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).read_note("../../../etc/passwd")
    assert result["error"] == "permission_denied"


# ── list_notes ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_notes_returns_all(vault):
    """list_notes without filter returns all .md files in directory."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/a.md", {"status": "pending"}, "")
    await tools.write_note("Needs_Action/b.md", {"status": "done"}, "")

    result = await tools.list_notes("Needs_Action")
    assert result["count"] == 2
    paths = [n["path"] for n in result["notes"]]
    assert "Needs_Action/a.md" in paths
    assert "Needs_Action/b.md" in paths


@pytest.mark.asyncio
async def test_list_notes_with_filter(vault):
    """list_notes with filter only returns matching frontmatter notes."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/pending.md", {"status": "pending"}, "")
    await tools.write_note("Needs_Action/done.md", {"status": "done"}, "")
    await tools.write_note("Needs_Action/other.md", {"status": "pending"}, "")

    result = await tools.list_notes("Needs_Action", filter="status:pending")
    assert result["count"] == 2, f"Expected 2 pending notes, got {result['count']}"
    paths = [n["path"] for n in result["notes"]]
    assert all("pending" in p or "other" in p for p in paths)


@pytest.mark.asyncio
async def test_list_notes_not_found(vault):
    """list_notes returns not_found for missing directory."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).list_notes("NonExistentDir")
    assert result["error"] == "not_found"


# ── move_note ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_note_success(vault):
    """move_note: moved=True, source gone, destination exists."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/tomove.md", {"status": "done"}, "body")

    result = await tools.move_note("Needs_Action/tomove.md", "Done/tomove.md")
    assert result["moved"] is True
    assert result["source"] == "Needs_Action/tomove.md"
    assert result["destination"] == "Done/tomove.md"
    assert not (vault / "Needs_Action" / "tomove.md").exists()
    assert (vault / "Done" / "tomove.md").exists()


@pytest.mark.asyncio
async def test_move_note_source_not_found(vault):
    """move_note returns not_found when source doesn't exist."""
    from mcp_servers.obsidian.tools import ObsidianTools
    result = await ObsidianTools(vault).move_note("Needs_Action/ghost.md", "Done/ghost.md")
    assert result["error"] == "not_found"


# ── search_notes ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_notes_finds_in_body(vault):
    """search_notes finds query text in note body."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/searchable.md", {"status": "ok"}, "Unique phrase here")
    await tools.write_note("Needs_Action/other.md", {"status": "ok"}, "Different content")

    result = await tools.search_notes("Unique phrase")
    assert result["count"] >= 1
    paths = [n["path"] for n in result["notes"]]
    assert any("searchable" in p for p in paths)


@pytest.mark.asyncio
async def test_search_notes_case_insensitive(vault):
    """search_notes is case-insensitive."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/case.md", {}, "Hello World")

    result = await tools.search_notes("hello world")
    assert result["count"] >= 1


@pytest.mark.asyncio
async def test_search_notes_snippet_included(vault):
    """search_notes result includes snippet field."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/snip.md", {}, "Find this text in the body")

    result = await tools.search_notes("Find this text")
    assert result["count"] >= 1
    assert "snippet" in result["notes"][0]


@pytest.mark.asyncio
async def test_search_notes_no_results(vault):
    """search_notes returns empty list when nothing matches."""
    from mcp_servers.obsidian.tools import ObsidianTools
    tools = ObsidianTools(vault)
    await tools.write_note("Needs_Action/empty.md", {}, "Nothing here")

    result = await tools.search_notes("xyzzy_not_found_12345")
    assert result["count"] == 0
    assert result["notes"] == []
