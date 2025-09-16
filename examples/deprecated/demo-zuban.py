#!/usr/bin/env python3
"""
Minimal Python LSP client that talks to a (Zuban) Language Server over stdio
and asks for all usages ("references") of the symbol at a given file+line+col
within a workspace.

Usage:
  python minimal_lsp_references_client.py \
      --workspace /path/to/workspace \
      --file /path/to/workspace/pkg/module.py \
      --line 42 --col 7 \
      [--server-cmd zuban --server-args "server"] [--timeout 15]

Notes:
- LSP positions are 0-based; this script accepts *1-based* CLI line/col for
  human-friendliness and converts to 0-based for the protocol.
- The server is assumed to be an LSP-compatible executable speaking JSON-RPC
  2.0 over stdio. If your binary name differs, pass --server-cmd.
- We open the target file with didOpen; most servers will index the rest of the
  workspace from rootUri.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# --------------------------- JSON-RPC over stdio --------------------------- #

class JsonRpcIO:
    def __init__(self, proc: subprocess.Popen[bytes]):
        self.proc = proc
        self._id = 0
        self._lock = threading.Lock()
        self._responses: Dict[int, Any] = {}
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()

    def _reader(self) -> None:
        buf = b""
        while True:
            line = self.proc.stdout.readline()
            if not line:
                return  # server exited
            # Expect header(s) like: b"Content-Length: 123\r\n" ... then CRLF line
            if not line.lower().startswith(b"content-length:"):
                # Skip any stray lines
                continue
            try:
                length = int(line.split(b":", 1)[1].strip())
            except Exception:
                continue
            # Read trailing CRLF after headers
            crlf = self.proc.stdout.readline()
            if crlf.strip():
                # Some servers may send multiple headers; eat until empty line
                while crlf not in (b"\r\n", b"\n", b""):
                    crlf = self.proc.stdout.readline()
            # Now read body
            body = self._read_exact(length)
            if not body:
                return
            try:
                msg = json.loads(body.decode("utf-8"))
            except Exception:
                continue
            # Store responses by id; notifications have no id
            msg_id = msg.get("id")
            if isinstance(msg_id, int):
                with self._lock:
                    self._responses[msg_id] = msg
            # else: it's a notification or request from server; ignore

    def _read_exact(self, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = self.proc.stdout.read(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def _next_id(self) -> int:
        with self._lock:
            self._id += 1
            return self._id

    def send(self, method: str, params: Any = None, *, is_request: bool = True) -> Optional[int]:
        msg: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if is_request:
            msg_id = self._next_id()
            msg["id"] = msg_id
        else:
            msg_id = None
        data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        self.proc.stdin.write(header + data)
        self.proc.stdin.flush()
        return msg_id

    def request(self, method: str, params: Any = None, timeout: float = 15.0) -> Any:
        req_id = self.send(method, params, is_request=True)
        # Wait for matching response
        end = time.time() + timeout
        while time.time() < end:
            with self._lock:
                if req_id in self._responses:
                    return self._responses.pop(req_id)
            time.sleep(0.01)
        raise TimeoutError(f"Timed out waiting for response to {method}")

    def notify(self, method: str, params: Any = None) -> None:
        self.send(method, params, is_request=False)

# ------------------------------ LSP Utilities ----------------------------- #

def path_to_uri(p: Path) -> str:
    return p.resolve().as_uri()

# ------------------------------ Main routine ------------------------------ #

def main() -> int:
    ap = argparse.ArgumentParser(description="Minimal LSP references client")
    ap.add_argument("--workspace", required=True, help="Path to workspace root (folder)")
    ap.add_argument("--file", required=True, help="Path to the target Python file")
    ap.add_argument("--line", type=int, required=True, help="1-based line number")
    ap.add_argument("--col", type=int, required=True, help="1-based column (character)")
    ap.add_argument("--server-cmd", default="zuban", help="LSP server executable (Zuban uses 'zuban')")
    ap.add_argument("--server-args", default="server", help="Arguments to pass to the server executable (for Zuban, use 'server')")
    ap.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout (seconds)")
    ap.add_argument("--open-all", action="store_true", help="Send didOpen for all *.py files in the workspace (forces full inclusion)")
    args = ap.parse_args()

    workspace = Path(args.workspace)
    file_path = Path(args.file)
    if not workspace.is_dir():
        print(f"Workspace does not exist: {workspace}", file=sys.stderr)
        return 2
    if not file_path.is_file():
        print(f"File does not exist: {file_path}", file=sys.stderr)
        return 2

    # Start the server as a stdio JSON-RPC process
    try:
        proc = subprocess.Popen(
            [args.server_cmd, *args.server_args.split()],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except FileNotFoundError:
        print(
            f"Could not start server '{args.server_cmd}'. Ensure it's installed and on PATH.",
            file=sys.stderr,
        )
        return 3

    io = JsonRpcIO(proc)

    root_uri = path_to_uri(workspace)
    file_uri = path_to_uri(file_path)

    # 1) initialize
    init_params = {
        "processId": os.getpid(),
        "rootUri": root_uri,
        "capabilities": {
            "textDocument": {
                "synchronization": {"didSave": True},
            },
            "workspace": {},
        },
        "trace": "off",
        "workspaceFolders": [
            {"uri": root_uri, "name": workspace.name}
        ],
    }

    resp = io.request("initialize", init_params, timeout=args.timeout)
    if "error" in resp:
        print(f"initialize error: {resp['error']}", file=sys.stderr)
        return 4

    # 2) initialized notification
    io.notify("initialized", {})

    # 3) didOpen files
    if args.open_all:
        py_files = [p for p in workspace.rglob("*.py") if p.is_file()]
        for i, p in enumerate(py_files, 1):
            uri = path_to_uri(p)
            try:
                textp = p.read_text(encoding="utf-8")
            except Exception:
                continue
            io.notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": textp,
                    }
                },
            )
            # Tiny throttle to avoid overwhelming the server
            if i % 50 == 0:
                time.sleep(0.01)
    else:
        text = file_path.read_text(encoding="utf-8")
        io.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": file_uri,
                    "languageId": "python",
                    "version": 1,
                    "text": text,
                }
            },
        )

    # Give the server a brief moment (still minimal)
    time.sleep(0.05)

    # Convert CLI 1-based to LSP 0-based
    position = {"line": max(0, args.line - 1), "character": max(0, args.col - 1)}

    # 4) textDocument/references
    ref_params = {
        "textDocument": {"uri": file_uri},
        "position": position,
        "context": {"includeDeclaration": True},
    }

    ref_resp = io.request("textDocument/references", ref_params, timeout=args.timeout)
    if "error" in ref_resp:
        print(f"references error: {ref_resp['error']}", file=sys.stderr)
        return 5

    result = ref_resp.get("result")
    if not result:
        print("No references found.")
        return 0

    # Print result locations in a grep-friendly format
    for loc in result:
        uri = loc.get("uri") or loc.get("targetUri")
        rng = loc.get("range") or loc.get("targetSelectionRange") or {}
        start = rng.get("start", {})
        line = start.get("line", 0) + 1  # back to 1-based for humans
        char = start.get("character", 0) + 1
        # Convert uri -> path if it's a file:// URI
        if uri and uri.startswith("file://"):
            try:
                from urllib.parse import urlparse, unquote
                parsed = urlparse(uri)
                path = unquote(parsed.path)
                if os.name == "nt" and path.startswith("/") and ":" in path:
                    path = path.lstrip("/")
                uri_display = path
            except Exception:
                uri_display = uri
        else:
            uri_display = uri or "<unknown>"
        print(f"{uri_display}:{line}:{char}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
