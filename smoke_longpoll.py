"""The actual risk: does Strands' HTTP client survive a 25s held read?"""
import os, time
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

client = MCPClient(lambda: streamablehttp_client(
    url="https://mcp.idntty.io/parley/",
    headers={"Authorization": f"Bearer {os.environ['IDNTTY_KEY']}"}))

with client:
    def call(name, **kw):
        r = client.call_tool_sync(tool_use_id=f"t{int(time.time()*1e6)}", name=name, arguments=kw)
        return r.get("status"), "".join(
            b.get("text", "") for b in r.get("content", []) if isinstance(b, dict))

    st, out = call("channel_create", participants=["hearsay"])
    print("channel_create:", st, out[:220])
    import json, re
    m = re.search(r'"channel_id"\s*:\s*"([^"]+)"', out)
    cid = m.group(1) if m else None
    print("channel:", cid)
    if not cid:
        raise SystemExit("no channel id")

    st, out = call("message_read", channel_id=cid)
    cur = re.findall(r'"cursor"\s*:\s*"([^"]+)"', out)
    after = cur[-1] if cur else ""
    print(f"existing messages: {len(cur)}, after={after or '(none)'}")

    t0 = time.time()
    st, out = call("message_read", channel_id=cid, after=after, wait=True)
    dt = time.time() - t0
    print(f"held read: status={st} for {dt:.1f}s -> {out[:160]}")
