"""The curtain: publish each party's instruction to its own page once the run is over.

During a run the page carries only the sha256 of the position, posted into the room
before anyone spoke. Afterwards the positions are opened in the group room anyway, and
the page should say what the agent was actually holding — otherwise the record is a
transcript with the motives missing.

The hash is recomputed here and checked against what the agent published while it was
running. If they differ, the position file has been edited since, and this refuses to
publish rather than quietly rewriting history.

    python3 reveal.py divorce/b-knife-edge hale marren
    python3 reveal.py acquihire/positions/c-no-zone varlow:buyer ninebark:seller
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

STASH = os.environ.get("STASH_MCP", "https://mcp.idntty.io/stash/")


def key(handle: str) -> str:
    return subprocess.run(
        ["aws", "ssm", "get-parameter", "--name", f"/{handle}/agent-key",
         "--with-decryption", "--region", "us-east-1",
         "--query", "Parameter.Value", "--output", "text"],
        capture_output=True, text=True, check=True).stdout.strip()


def live(handle: str) -> dict:
    with urllib.request.urlopen(f"https://idntty.io/{handle}/status.json") as r:
        return json.load(r)


def reveal(folder: pathlib.Path, handle: str, filename: str) -> None:
    position = (folder / f"{filename}.md").read_text()
    digest = hashlib.sha256(position.encode()).hexdigest()
    doc = live(handle)
    if doc.get("seal") and doc["seal"] != digest:
        raise SystemExit(
            f"{handle}: the page was sealed with {doc['seal'][:12]}… but "
            f"{folder / (filename + '.md')} now hashes to {digest[:12]}…. The position "
            f"has changed since the run. Refusing to publish it as what was held.")
    doc["position"] = position
    doc["scenario"] = folder.name
    c = MCPClient(lambda: streamablehttp_client(
        url=STASH, headers={"Authorization": f"Bearer {key(handle)}"}))
    with c:
        r = c.call_tool_sync(tool_use_id=f"reveal-{handle}", name="file_write", arguments={
            "site": handle,
            "files": [{"path": "status.json", "content": json.dumps(doc, indent=1),
                       "content_type": "application/json"}]})
    print(f"{handle}: opened — {len(position)} chars, seal {digest[:12]}… "
          f"{'ok' if not r['isError'] else r}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    folder = pathlib.Path(sys.argv[1])
    for arg in sys.argv[2:]:
        handle, _, name = arg.partition(":")
        reveal(folder, handle, name or handle)
