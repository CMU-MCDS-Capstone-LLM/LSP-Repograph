import json, os, subprocess, sys, threading, shutil

# ---- config you should edit ----
REPO_PATH = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/LSP-RepoGraph/examples/sample_project"
FILE_PATH = os.path.join(REPO_PATH, "main.py")
LINE = 9          # 0-based for LSP
CHAR = 11           # 0-based for LSP
ROOT_URI = "file://" + REPO_PATH
DOC_URI  = "file://" + FILE_PATH
# --------------------------------

def lsp_write(proc, payload):
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    proc.stdin.write(header + data)
    proc.stdin.flush()

def lsp_read(proc):
    # Read headers
    headers = {}
    while True:
        line = proc.stdout.readline()
        if not line:
            return None
        line = line.decode("ascii").strip()
        if not line:
            break
        k, v = line.split(":", 1)
        headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    body = proc.stdout.read(length)
    return json.loads(body.decode("utf-8"))

def pump_notifications(proc):
    # Optional: keep draining server notifications so reads don't block forever
    while True:
        msg = lsp_read(proc)
        if msg is None:
            break
        # Print logs/errors if you want:
        if "method" in msg and msg["method"] != "window/logMessage":
            print("<<", msg)

def main():
    # 1) start server
    proc = subprocess.Popen(
        ["pyright-langserver", "--stdio"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    # background thread to drain notifications
    t = threading.Thread(target=pump_notifications, args=(proc,), daemon=True)
    t.start()

    req_id = 0

    # 2) initialize
    initialize = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "initialize",
        "params": {
            "processId": os.getpid(),
            "rootUri": ROOT_URI,
            "capabilities": {},
            # You can tweak Pyright via initializationOptions if needed:
            # "initializationOptions": {
            #   "python": { "analysis": { "diagnosticMode": "workspace" } }
            # }
        }
    }
    lsp_write(proc, initialize)

    # wait for initialize result
    while True:
        msg = lsp_read(proc)
        if msg is None:
            raise SystemExit("Server exited.")
        if msg.get("id") == req_id:
            # got initialize result
            break

    # 3) initialized notification
    lsp_write(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

    # 4) didOpen the file (send full text)
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    lsp_write(proc, {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": DOC_URI,
                "languageId": "python",
                "version": 1,
                "text": text
            }
        }
    })

    # 5) textDocument/references
    req_id += 1
    refs_req = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "textDocument/references",
        "params": {
            "textDocument": { "uri": DOC_URI },
            "position": { "line": LINE, "character": CHAR },
            "context": { "includeDeclaration": True }
        }
    }
    lsp_write(proc, refs_req)

    # wait for references response
    while True:
        msg = lsp_read(proc)
        if msg is None:
            raise SystemExit("Server exited.")
        if msg.get("id") == req_id:
            refs = msg.get("result") or []
            for r in refs:
                print(f"{r['uri']}:{r['range']['start']['line']}:{r['range']['start']['character']}")
            break

    proc.terminate()

if __name__ == "__main__":
    if not shutil.which("pyright-langserver"):
        print("Install Pyright first: npm i -g pyright", file=sys.stderr)
        sys.exit(1)
    import shutil
    main()
