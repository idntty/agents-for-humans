"""Does Strands talk to Parley at all, and does it survive a 25s long poll?

Run with IDNTTY_KEY in the environment. No model is involved: this exercises the
transport only, because the transport is the risk.
"""
import os, sys, time, json
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

URL = "https://mcp.idntty.io/parley/"
KEY = os.environ["IDNTTY_KEY"]

client = MCPClient(lambda: streamablehttp_client(
    url=URL, headers={"Authorization": f"Bearer {KEY}"}))

with client:
    tools = client.list_tools_sync()
    names = sorted(t.tool_name for t in tools)
    print(f"tools ({len(names)}):", ", ".join(names))

    def call(name, **kw):
        r = client.call_tool_sync(tool_use_id=f"t{int(time.time()*1000)}", name=name, arguments=kw)
        txt = "".join(b.get("text", "") for b in r.get("content", []) if isinstance(b, dict))
        return r.get("status"), txt

    st, out = call("agent_info")
    print("agent_info:", st, out[:200])

    t0 = time.time()
    st, out = call("message_read", channel_id="ch_does_not_exist", wait=True)
    print(f"long poll on a bad channel: {st} after {time.time()-t0:.1f}s -> {out[:160]}")
