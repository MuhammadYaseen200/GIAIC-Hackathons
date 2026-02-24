"""Async MCP tool caller with fallback protocol (ai-control/MCP.md).

Fallback protocol:
  1. Attempt MCP tool call via subprocess stdin/stdout JSON-RPC
  2. On MCPError / timeout / subprocess failure: log mcp_fallback + execute fallback callable
  3. If fallback also fails: log mcp_escalation + raise MCPUnavailableError

Usage:
    client = MCPClient("obsidian", ["python3", "mcp-servers/obsidian/server.py"], vault_path)
    result = await client.call_tool("read_note", {"path": "test.md"})
    # With fallback:
    result = await client.call_tool("move_note", args, fallback=lambda: vault_ops.move(...))
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class MCPUnavailableError(Exception):
    """Raised when MCP server cannot be reached and fallback is unavailable or failed."""


class MCPClient:
    """Wraps MCP subprocess tool calls with the fallback protocol from ai-control/MCP.md.

    Each call_tool() invocation spawns a subprocess, sends JSON-RPC init + tool call,
    parses the response, and terminates. On any failure, the fallback callable is run
    and the failure is logged to vault/Logs/mcp_fallback_{date}.jsonl.
    """

    def __init__(self, server_name: str, command: list[str], vault_path: Path) -> None:
        self.server_name = server_name
        self.command = command
        self.vault_path = Path(vault_path)
        self._log_dir = self.vault_path / "Logs"

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        fallback: Optional[Callable] = None,
        timeout: float = 30.0,
    ) -> dict:
        """Call MCP tool with fallback protocol.

        Args:
            tool_name: Name of the MCP tool to call.
            arguments: Dict of tool arguments matching the tool's inputSchema.
            fallback: Optional callable (sync or async) to run if MCP call fails.
                      Should return a dict or a value that will be wrapped in {"result": ...}.
            timeout: Seconds to wait for subprocess response.

        Returns:
            Tool result dict on success, or fallback result dict.

        Raises:
            MCPUnavailableError: If MCP call failed AND (no fallback OR fallback also failed).
        """
        try:
            return await asyncio.wait_for(
                self._invoke_tool(tool_name, arguments),
                timeout=timeout,
            )
        except Exception as e:
            self._log_fallback(tool_name, arguments, str(e))
            if fallback is not None:
                try:
                    result = fallback()
                    if asyncio.iscoroutine(result):
                        result = await result
                    # Normalize non-dict results
                    if isinstance(result, dict):
                        return result
                    return {"result": result}
                except Exception as fallback_err:
                    self._log_escalation(tool_name, str(fallback_err))
                    raise MCPUnavailableError(
                        f"MCP tool {self.server_name}.{tool_name} failed and "
                        f"fallback also failed: {fallback_err}"
                    ) from fallback_err
            raise MCPUnavailableError(
                f"MCP tool {self.server_name}.{tool_name} failed (no fallback): {e}"
            ) from e

    async def _invoke_tool(self, tool_name: str, arguments: dict) -> dict:
        """Invoke tool via subprocess stdin/stdout JSON-RPC.

        Sends MCP initialize handshake then tool call request.
        Parses the last JSON line from stdout as the tool response.
        """
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "orchestrator", "version": "1.0"},
            },
        }
        tool_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        payload = (
            json.dumps(init_request) + "\n" + json.dumps(tool_request) + "\n"
        ).encode()
        stdout, stderr = await proc.communicate(input=payload)

        lines = [line.strip() for line in stdout.decode().split("\n") if line.strip()]
        if len(lines) < 2:
            stderr_text = stderr.decode()[:200] if stderr else ""
            raise RuntimeError(
                f"MCP server {self.server_name} returned unexpected output "
                f"(expected ≥2 JSON lines). stderr: {stderr_text}"
            )

        # Last line is the tool call response
        try:
            response = json.loads(lines[-1])
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"MCP server {self.server_name} returned non-JSON: {lines[-1][:200]}"
            ) from e

        if "error" in response:
            raise RuntimeError(
                f"MCP JSON-RPC error from {self.server_name}: {response['error']}"
            )

        result = response.get("result", {})

        # Check FastMCP isError flag
        if isinstance(result, dict) and result.get("isError"):
            content = result.get("content", [{}])
            error_text = (
                content[0].get("text", "Unknown tool error") if content else "Unknown tool error"
            )
            raise RuntimeError(f"Tool {tool_name} returned error: {error_text}")

        # FastMCP wraps result in content[0].text as JSON string
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if content and isinstance(content[0], dict) and "text" in content[0]:
                try:
                    return json.loads(content[0]["text"])
                except (json.JSONDecodeError, TypeError):
                    return {"text": content[0]["text"]}

        return result if isinstance(result, dict) else {"result": result}

    def _log_fallback(self, tool_name: str, arguments: dict, error: str) -> None:
        """Log mcp_fallback event to vault/Logs/mcp_fallback_{date}.jsonl."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "mcp_fallback",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server": self.server_name,
            "tool": tool_name,
            "error": error,
            "severity": "WARNING",
        }
        log_path = self._log_dir / f"mcp_fallback_{datetime.now(timezone.utc).date()}.jsonl"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass  # best-effort logging; do not mask the original error
        logger.warning(
            "MCP fallback: %s.%s — %s", self.server_name, tool_name, error
        )

    def _log_escalation(self, tool_name: str, error: str) -> None:
        """Log mcp_escalation event when both MCP and fallback fail."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "mcp_escalation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server": self.server_name,
            "tool": tool_name,
            "error": error,
            "severity": "ERROR",
        }
        log_path = self._log_dir / f"mcp_fallback_{datetime.now(timezone.utc).date()}.jsonl"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass
        logger.error(
            "MCP escalation: %s.%s — %s", self.server_name, tool_name, error
        )
