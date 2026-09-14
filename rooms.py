"""Open a fresh set of rooms for a scenario: one group, two private lines.

  python rooms.py <scenario> [buyer-handle seller-handle] [state-file]

Writes the room ids to a state file (default /tmp/rooms.json) so two scenarios can run
side by side without treading on each other.
"""
import json, os, pathlib, sys, time
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

scenario = sys.argv[1] if len(sys.argv) > 1 else "run"
buyer  = sys.argv[2] if len(sys.argv) > 2 else "varlow"
seller = sys.argv[3] if len(sys.argv) > 3 else "ninebark"
state  = pathlib.Path(sys.argv[4] if len(sys.argv) > 4 else "/tmp/rooms.json")

c = MCPClient(lambda: streamablehttp_client(url="https://mcp.idntty.io/parley/",
    headers={"Authorization": f"Bearer {os.environ['IDNTTY_KEY']}"}))
t = lambda r: "".join(b.get("text","") for b in r.get("content",[]) if isinstance(b,dict))

with c:
    call = lambda n, **k: t(c.call_tool_sync(tool_use_id=f"r{int(time.time()*1e6)}",
                                             name=n, arguments=k))
    if state.exists():
        call("channel_edit", channel_id=json.loads(state.read_text())["group"],
             state="archived")
    rooms = {"group": json.loads(call("channel_create", participants=[buyer, seller],
                topic=f"{buyer} / {seller} — {scenario}",
                description="The document is built as we go."))["channel_id"],
             buyer:  json.loads(call("channel_create", participants=[buyer]))["channel_id"],
             seller: json.loads(call("channel_create", participants=[seller]))["channel_id"]}
    state.write_text(json.dumps(rooms))
    print(json.dumps(rooms, indent=2))
