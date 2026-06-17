#!/usr/bin/env python3
"""测试 MCP 服务器：握手 → 列出工具 → 调用 jenkins_list_jobs"""
import subprocess
import json
import os

SERVER = os.path.join(os.path.dirname(__file__), "jenkins_mcp_server.py")
VENV_PYTHON = os.path.join(os.path.dirname(__file__), ".venv/bin/python3")

proc = subprocess.Popen(
    [VENV_PYTHON, SERVER],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

def send(method, params=None, id=1):
    msg = {"jsonrpc": "2.0", "method": method, "id": id}
    if params is not None:
        msg["params"] = params
    payload = json.dumps(msg) + "\n"
    proc.stdin.write(payload)
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())

# Step 1: Initialize
print("1. initialize...")
r = send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}})
print(f"   server: {r['result']['serverInfo']['name']} v{r['result']['serverInfo']['version']}")

# Step 2: Send initialized notification (no id)
proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
proc.stdin.flush()

# Step 3: List tools
print("\n2. tools/list...")
r = send("tools/list")
tools = r["result"]["tools"]
for t in tools:
    print(f"   - {t['name']}: {t['description'][:60]}...")

# Step 4: Call jenkins_list_jobs
print("\n3. jenkins_list_jobs...")
r = send("tools/call", {"name": "jenkins_list_jobs"}, id=3)
for line in r["result"]["content"][0]["text"].splitlines():
    print(f"   {line}")

# Cleanup
proc.stdin.close()
proc.terminate()
proc.wait()
print("\n✅ MCP 服务器运行正常")
