# ADR-0009: Vault Operations Reuse from watchers/utils.py

> **Scope**: Defines the code reuse strategy for vault file operations in the Obsidian MCP server — specifically whether to import from `watchers/utils.py` or reimplement.

- **Status:** Accepted
- **Date:** 2026-02-24
- **Feature:** mcp-integration (007)
- **Context:** The Obsidian MCP server needs atomic file writes, YAML frontmatter rendering, and UTF-8 sanitization to implement `write_note`, `read_note`, and related tools. These exact functions already exist in `watchers/utils.py` and are used by the orchestrator's `vault_ops.py`. The `atomic_write` function (lines 54–78 of utils.py) is POSIX-atomic via temp file + `os.replace()`, validated by 385 tests. Constitution Principle II mandates local-first filesystem operations. The spec explicitly states "Obsidian MCP MUST reuse `watchers/utils.py` `atomic_write`" (FR-010). The architectural question is whether `mcp-servers/` can import from `watchers/` without creating a problematic coupling.

## Decision

**Directly import** `atomic_write`, `render_yaml_frontmatter`, `sanitize_utf8`, and `sanitize_filename` from `watchers.utils` in `mcp-servers/obsidian/tools.py`. Resolve import path via `sys.path.insert(0, project_root)` at the top of `server.py`.

Components:
- **Import pattern**: `from watchers.utils import atomic_write, render_yaml_frontmatter, sanitize_utf8` in `mcp-servers/obsidian/tools.py`
- **Path setup**: `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` at top of server.py — adds project root to Python path before watchers imports
- **No wrapper**: Functions imported and called directly — no adapter layer between `mcp-servers/obsidian/tools.py` and `watchers/utils.py`
- **YAML parsing**: `yaml.safe_load()` from PyYAML (already a project dependency) for frontmatter parsing in `read_note` — not in utils.py, added inline in `_parse_note()`
- **Path traversal guard**: `ObsidianTools._resolve()` validates all vault-relative paths resolve within `VAULT_PATH` root — this is MCP-specific logic, not in utils.py
- **`shutil.move()` for move_note**: Standard library `shutil.move()` for `move_note` — not from utils.py (which handles atomic writes, not moves)

## Consequences

### Positive

- **Zero duplication**: `atomic_write` (47 lines, 385 tests validating correctness) used as-is — no risk of introducing new file corruption bugs
- **Spec compliance**: FR-010 explicitly mandates this reuse — no ambiguity
- **Single fix, everywhere fixed**: Any bug in `atomic_write` is fixed once in `watchers/utils.py` and both watcher and MCP server benefit
- **Consistent vault format**: YAML frontmatter rendered identically by orchestrator and Obsidian MCP server — no format drift between read and write paths
- **Minimal dependency**: `sys.path.insert` is a standard Python technique for monorepo internal imports — no `pip install`, no packaging overhead
- **Test reuse**: Existing `watchers/utils.py` tests cover `atomic_write` corner cases; MCP integration tests only test tool behavior, not atomic write correctness

### Negative

- **Implicit coupling**: `mcp-servers/obsidian/` has a runtime dependency on `watchers/utils.py` that is not declared in any package manifest — refactoring `watchers/utils.py` can break the MCP server silently
- **`sys.path` mutation**: Adding project root to `sys.path` at module import time is not idiomatic for packaged Python; can cause issues if the same Python process imports from multiple project roots
- **Not installable as a standalone package**: `mcp-servers/obsidian/` cannot be installed independently via `pip` without the full project — acceptable for local deployment, problematic if MCP servers are ever distributed separately
- **Import fragility in tests**: Tests that import `ObsidianTools` must also have `watchers/` importable — requires running tests from the project root (already the convention for `pytest tests/`)

## Alternatives Considered

**Alternative A: Reimplement atomic_write in mcp-servers/obsidian/**
- Components: Copy-paste or rewrite `atomic_write` in `mcp-servers/obsidian/utils.py`
- Pros: Complete independence of `mcp-servers/` from `watchers/`; standalone installable
- Cons: Duplicates 47 lines of battle-tested code; two places to fix atomic write bugs; violates spec FR-010 explicitly; violates DRY
- Rejected: Spec violation; duplication; maintenance burden

**Alternative B: Extract shared utilities to a top-level `shared/` package**
- Components: Create `shared/utils.py`; both `watchers/utils.py` and `mcp-servers/obsidian/tools.py` import from `shared/utils.py`
- Pros: Proper package boundary; explicit shared dependency; standalone installable
- Cons: Requires moving existing code (breaking change to Phase 2 import paths); adds a new top-level package to the directory structure (path-warden would flag as unplanned); all 385 existing tests reference `watchers.utils` imports
- Rejected: Too many files affected; existing tests import from `watchers.utils`; Phase 4 should not refactor Phase 2 code; YAGNI (no other consumer of shared utilities currently)

**Alternative C: Install `watchers` as a Python package with `pip install -e .`**
- Components: Add `pyproject.toml` + `setup.cfg`; `pip install -e .` makes `watchers` importable without path manipulation
- Pros: Idiomatic Python packaging; no `sys.path` mutation; MCP server becomes standalone-installable
- Cons: Adds `pyproject.toml` to the project (new file, scope beyond Phase 4); requires `pip install -e .` in CI/CD; adds packaging overhead for a monorepo-style project
- Rejected: Over-engineered for current phase; `sys.path.insert` achieves the same effect with zero additional files; can be done in Phase 7 (Polish) if needed

**Alternative D: Use `vault_ops.py` instead of `utils.py` directly**
- Components: Import `write_draft_reply`, `update_frontmatter` etc. from `orchestrator/vault_ops.py`
- Pros: Vault-aware operations already implemented
- Cons: `vault_ops.py` functions are orchestrator-specific (take orchestrator-internal types like `DraftReply`); Obsidian MCP needs raw `atomic_write` + frontmatter rendering, not orchestrator-semantic operations; importing from `orchestrator/` in `mcp-servers/` creates a cross-layer dependency (MCP should not depend on orchestrator)
- Rejected: Cross-layer dependency violation; wrong level of abstraction

## References

- Feature Spec: `specs/007-mcp-integration/spec.md` (FR-010, FR-012)
- Implementation Plan: `specs/007-mcp-integration/plan.md` (Phase B)
- Research: `specs/007-mcp-integration/research.md` (D3 — Vault Operations Reuse)
- Tasks: `specs/007-mcp-integration/tasks.md` (T021 — obsidian/tools.py full implementation)
- Source: `watchers/utils.py:54-78` (atomic_write), `watchers/utils.py:130-143` (render_yaml_frontmatter)
- Related ADRs: ADR-0003 (local file persistence — established atomic write as the vault write standard)
- Constitution: `.specify/memory/constitution.md` Principle II (Local-First Filesystem)
