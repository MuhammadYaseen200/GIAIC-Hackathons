"""Obsidian vault MCP tool handlers. Direct filesystem access — no Obsidian app required."""
import json
import os
import re
import shutil
import sys
import yaml
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.utils import atomic_write, render_yaml_frontmatter, sanitize_utf8


class ObsidianTools:
    """Implements all Obsidian MCP tool handlers. All paths are vault-relative."""

    def __init__(self, vault_path: Path):
        self._vault = vault_path.resolve()

    def _resolve(self, relative_path: str) -> Path:
        """Resolve vault-relative path. Raises PermissionError if outside vault."""
        resolved = (self._vault / relative_path).resolve()
        if not str(resolved).startswith(str(self._vault)):
            raise PermissionError(f"Path '{relative_path}' is outside vault root")
        return resolved

    def _parse_note(self, content: str) -> tuple[dict, str]:
        """Parse markdown note into (frontmatter_dict, body_str)."""
        parts = content.split("---", 2)
        if len(parts) >= 3 and parts[0].strip() == "":
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                fm = {}
            body = parts[2].strip()
        else:
            fm = {}
            body = content.strip()
        return fm, body

    # ── health_check ──────────────────────────────────────────────────────────

    async def health_check(self) -> dict:
        """Verify vault is accessible and return note count."""
        try:
            if not self._vault.exists():
                return {"error": "not_found", "message": f"Vault not found: {self._vault}"}
            note_count = len(list(self._vault.rglob("*.md")))
            return {"status": "ok", "vault_path": str(self._vault), "note_count": note_count}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── read_note ─────────────────────────────────────────────────────────────

    async def read_note(self, path: str) -> dict:
        """Read vault note; return {path, frontmatter, body}."""
        try:
            abs_path = self._resolve(path)
            if not abs_path.exists():
                return {
                    "error": "not_found",
                    "message": f"Note not found: {path}",
                    "details": {"path": path},
                }
            content = sanitize_utf8(abs_path.read_text(encoding="utf-8", errors="replace"))
            fm, body = self._parse_note(content)
            return {"path": path, "frontmatter": fm, "body": body}
        except PermissionError as e:
            return {"error": "permission_denied", "message": str(e)}
        except yaml.YAMLError as e:
            return {
                "error": "parse_error",
                "message": f"Corrupt frontmatter: {e}",
                "details": {"path": path},
            }
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── write_note ────────────────────────────────────────────────────────────

    async def write_note(self, path: str, frontmatter: dict, body: str = "") -> dict:
        """Write note atomically; return written content for round-trip verification."""
        try:
            abs_path = self._resolve(path)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            content = render_yaml_frontmatter(frontmatter) + "\n" + body
            atomic_write(abs_path, content)
            return {"path": path, "frontmatter": frontmatter, "body": body}
        except PermissionError as e:
            return {"error": "permission_denied", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── list_notes ────────────────────────────────────────────────────────────

    async def list_notes(self, directory: str, filter: Optional[str] = None) -> dict:
        """List notes in directory, optionally filtered by frontmatter field:value."""
        try:
            abs_dir = self._resolve(directory)
            if not abs_dir.exists():
                return {"error": "not_found", "message": f"Directory not found: {directory}"}

            notes = []
            for md_file in sorted(abs_dir.glob("*.md")):
                rel_path = str(md_file.relative_to(self._vault))
                if filter:
                    field, _, value = filter.partition(":")
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="replace")
                        fm, _ = self._parse_note(content)
                        if str(fm.get(field.strip(), "")) != value.strip():
                            continue
                    except Exception:
                        continue
                notes.append({"path": rel_path})

            return {"notes": notes, "count": len(notes)}
        except PermissionError as e:
            return {"error": "permission_denied", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── move_note ─────────────────────────────────────────────────────────────

    async def move_note(self, source: str, destination: str) -> dict:
        """Move vault note atomically via shutil.move."""
        try:
            src = self._resolve(source)
            dst = self._resolve(destination)
            if not src.exists():
                return {
                    "error": "not_found",
                    "message": f"Source not found: {source}",
                    "details": {"path": source},
                }
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return {"moved": True, "source": source, "destination": destination}
        except PermissionError as e:
            return {"error": "permission_denied", "message": str(e)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}

    # ── search_notes ──────────────────────────────────────────────────────────

    async def search_notes(self, query: str) -> dict:
        """Full-text search across all vault notes (case-insensitive substring)."""
        try:
            query_lower = query.lower()
            matches = []
            for md_file in sorted(self._vault.rglob("*.md")):
                try:
                    content = md_file.read_text(encoding="utf-8", errors="replace")
                    if query_lower in content.lower():
                        idx = content.lower().index(query_lower)
                        start = max(0, idx - 80)
                        end = min(len(content), idx + len(query) + 80)
                        snippet = content[start:end].strip()
                        rel_path = str(md_file.relative_to(self._vault))
                        matches.append({"path": rel_path, "snippet": snippet[:200]})
                except Exception:
                    continue
            return {"notes": matches, "count": len(matches)}
        except Exception as e:
            return {"error": "internal_error", "message": str(e)}
