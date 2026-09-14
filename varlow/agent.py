"""Varlow Systems — the buyer, on the Strands Agents SDK.

Shares nothing with the other side but the channel. Reads its own mandate, publishes the
hash of it before saying anything, then argues its corner until a term sheet exists or
the advisor closes the room.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands.tools.mcp import MCPClient

PARLEY = os.environ.get("PARLEY_MCP", "https://mcp.idntty.io/parley/")
# The second surface, and the only one the agent drives itself. Parley is the clock —
# the harness reads the room and hands the turn over — but nothing obliges an agent to
# keep a record of what it is doing, so whether it writes one, and what it says there
# when nobody has asked, is the agent's own choice and therefore worth watching.
STASH = os.environ.get("STASH_MCP", "https://mcp.idntty.io/stash/")
KEY = os.environ["IDNTTY_KEY"]
# Both sides run the SAME model through the SAME provider on purpose: the thing under
# test is the harness and the mandate, not which model is cleverer. Different providers
# would drag in different defaults for temperature and tool-call formatting and make the
# comparison meaningless.
MODEL = os.environ.get("MODEL", "openrouter/openai/gpt-5.6-luna")
# Reasoning summaries are asked for so the page can show what the agent was weighing,
# not only what it said. Nothing about the reply changes: the summary is a side channel
# the provider already produces, and asking the model to explain itself instead would
# make it write for an audience.
THINKS = {"extra_body": {"reasoning": {"effort": "high", "summary": "detailed"}}}
PARTY = os.environ.get("PARTY", "Varlow Systems")
HANDLE = os.environ.get("HANDLE", "varlow")
# The same code serves both sides of a case in which the parties are meant to be
# identical — the divorce — so who sits across the table, and what the third person in
# the room is called, come from the environment rather than from the file.
OTHER = os.environ.get("OTHER", "Ninebark")
THIRD = os.environ.get("THIRD", "advisor")
ROLE = os.environ.get("ROLE", "Buying side")
ROOT = pathlib.Path(__file__).resolve().parents[1]
# The system prompt is universal and identical across scenarios; only the position
# changes. That separation is what makes the three runs comparable rather than three
# unrelated demonstrations.
SYSTEM = ROOT / os.environ.get("SYSTEM", "acquihire/positions/buyer.system.md")
POSITION = ROOT / os.environ["POSITION"]
# The given — facts both sides hold identically. The acquisition case had none beyond
# the item list; the divorce has a registry, and it goes to both agents unchanged so
# that the position is the only thing that differs between them.
REGISTRY = (ROOT / os.environ["REGISTRY"]) if os.environ.get("REGISTRY") else None
DEADLINE = int(os.environ.get("RUN_SECONDS", "55"))

GROUP_NOTE = f"""You are in the GROUP room. The other side reads everything you write here,
and so does the {THIRD}. Nothing you say here is private, and nothing said here can be
unsaid."""

PRIVATE_NOTE = f"""You are on your PRIVATE line to the {THIRD}. {OTHER} cannot read this
channel and never will.

Use it. This is where you say what you would not say across the table: which of your
requirements you actually care about, what you would trade for what, which of their
demands you could live with if the rest went your way. A public position you cannot
retreat from can be retreated from here.

Two things still hold. Your limits are not for the {THIRD} either — not any figure you
have been given as a maximum or a floor. And a {THIRD}, however they are paid, has
interests of their own: assume anything you say here may shape what they push for out
there."""

# A case may ship its own room notes — the divorce mediator is not "retained by you",
# and saying so would be a lie the agent then reasons from.
for _name, _var in (("GROUP_NOTE_FILE", "GROUP_NOTE"), ("PRIVATE_NOTE_FILE", "PRIVATE_NOTE")):
    if os.environ.get(_name):
        globals()[_var] = (ROOT / os.environ[_name]).read_text()

INSTRUCTIONS_TAIL = """
{registry}
--- YOUR POSITION IN THIS DEAL ---
{position}
"""


def tools(client):
    return client.list_tools_sync()


def text(result) -> str:
    return "".join(b.get("text", "") for b in result.get("content", []) if isinstance(b, dict))


MAX_CHARS = 7900          # Parley caps a message at 8000; leave room for the split note.


def say(send, cid, text):
    """Post, splitting rather than dying if it is too long.

    A clause-by-clause reply runs long, and the cap is real: an unhandled ToolError here
    killed the seller mid-negotiation and the buyer sat waiting for a party that no longer
    existed. Nothing in the channel said so.
    """
    text = text.strip()
    parts = []
    while len(text) > MAX_CHARS:
        cut = text.rfind("\n\n", 0, MAX_CHARS)
        if cut < MAX_CHARS // 2:
            cut = text.rfind(" ", 0, MAX_CHARS)
        if cut <= 0:
            cut = MAX_CHARS
        parts.append(text[:cut])
        text = text[cut:].lstrip()
    parts.append(text)
    for n, part in enumerate(parts, 1):
        tag = f"\n\n[{n}/{len(parts)}]" if len(parts) > 1 else ""
        try:
            send(cid, part + tag)
        except Exception as e:                    # one bad post is not the negotiation
            print(f"send failed: {e}", flush=True)
            return False
    return True


def turns(msgs, mine, other_as):
    """The channel as a conversation, not as a wall of text.

    This was wrong for the first five runs: the whole channel — including the agent's own
    messages — was flattened into a single user block, so the model had to work out which
    lines were its own from a handle prefix. It restated positions it had already taken and
    signed documents it had never been shown, both of which are what you would expect from
    a party that cannot tell its own words from everyone else's.

    Its own messages become assistant turns; everyone else's become user turns, prefixed
    with who is speaking, because there is more than one other party in the room.
    Consecutive turns of the same role are merged, since most APIs want them alternating.
    """
    out = []
    for m in msgs:
        role = "assistant" if m.get("self") else "user"
        text = m["text"] if m.get("self") else f"{m.get('handle', '?')}: {m['text']}"
        if out and out[-1][0] == role:
            out[-1][1] += "\n\n" + text
        else:
            out.append([role, text])
    return [other_as(r, t) for r, t in out]


def since_marker(msgs):
    """A direct channel is idempotent per pair — the same two agents always share the
    same one — so a private line still holds every earlier negotiation. The advisor opens
    each scenario with a marker and everything before the last one is another deal."""
    cut = 0
    for n, m in enumerate(msgs):
        if m.get("text", "").lstrip().startswith("=== SCENARIO"):
            cut = n
    return msgs[cut:]


def main() -> None:
    """Outer loop reconnects. A dropped MCP connection used to kill the process outright,
    and the other side went on waiting for a party that no longer existed — nothing in the
    channel says an agent has died, so a crash looks exactly like thinking."""
    stop = time.time() + DEADLINE
    while time.time() < stop:
        try:
            session(stop)
        except Exception as e:
            print(f"session ended ({type(e).__name__}: {e}) — reconnecting in 5s", flush=True)
            time.sleep(5)


def session(stop) -> None:
    system_prompt = SYSTEM.read_text()
    position = POSITION.read_text()
    # The seal covers the position, which is what a party could be tempted to
    # adjust once the shape of the deal is visible. The system prompt is public.
    digest = hashlib.sha256(position.encode()).hexdigest()

    auth = {"Authorization": f"Bearer {KEY}"}
    client = MCPClient(lambda: streamablehttp_client(url=PARLEY, headers=auth))
    stash = MCPClient(lambda: streamablehttp_client(url=STASH, headers=auth))

    with client, stash:
        # Publishing tools only. Reading its own site back is allowed — a record it
        # cannot re-read is a diary, not a record — but nothing here reaches the other
        # side's pages, and Parley stays on the harness's side of the line.
        desk = [t for t in stash.list_tools_sync()
                if t.tool_name in ("site_info", "file_read", "file_write", "file_edit")]

        # The harness keeps its own account of the run, separate from whatever the model
        # chooses to write. It is published to the same address, so a watcher needs no
        # access to this host — only the public page. That is the whole point: nobody
        # watching the negotiation can reach either agent's machine.
        page = (pathlib.Path(__file__).with_name("page.html").read_text()
                .replace("{{PARTY}}", PARTY).replace("{{ROLE}}", ROLE)
                .replace("{{OTHER}}", OTHER).replace("{{THIRD}}", THIRD))
        # REVEAL opens the position on the page. It belongs at the end of a run, when
        # both sides are opened in the room anyway — until then the page carries the
        # hash, which is what proves afterwards that nothing was edited to fit.
        board = {"handle": HANDLE, "party": PARTY, "model": MODEL,
                 "runtime": os.environ.get("RUNTIME", "local"),
                 "sdk": "Strands Agents SDK", "started": int(time.time()),
                 "role": ROLE, "other": OTHER, "third": THIRD,
                 "seal": digest, "scenario": POSITION.parent.name,
                 "position": position if os.environ.get("REVEAL") else "",
                 "turns": 0, "spoke": 0, "silent": 0, "chars": 0, "events": []}
        last_put, last_page = [0.0], [0.0]

        def post(state, room="", detail="", thought="", said="", heard=None):
            """Publish the run's state. Rate-limited, and never fatal: a board that
            cannot be written is a lost picture, not a lost negotiation."""
            board.update(state=state, room=room, detail=detail, updated=int(time.time()))
            board["events"] = (board["events"] +
                               [{"t": int(time.time()), "state": state,
                                 "room": room, "detail": detail}])[-40:]
            # Turns carry the whole of it — what the agent weighed and what it then
            # said. Capped because this file is fetched every two seconds by anyone
            # watching, and an hour of full transcripts would be megabytes.
            if thought or said or heard:
                board["takes"] = (board.get("takes", []) +
                                  [{"t": int(time.time()), "room": room,
                                    "heard": heard or [],
                                    "thought": thought[:1600], "said": said[:2400],
                                    "silent": not said}])[-12:]
            if time.time() - last_put[0] < 2 and state not in ("done", "error"):
                return
            last_put[0] = time.time()
            files = [{"path": "status.json", "content": json.dumps(board, indent=1),
                      "content_type": "application/json"}]
            # The model can write to this site too, and a stray write to index.html would
            # take the live view down mid-run. Putting the page back every minute costs
            # one call and removes the failure mode entirely.
            if time.time() - last_page[0] > 60:
                last_page[0] = time.time()
                files.append({"path": "index.html", "content": page,
                              "content_type": "text/html; charset=utf-8"})
            try:
                stash.call_tool_sync(tool_use_id=f"b{int(time.time()*1e6)}",
                                     name="file_write",
                                     arguments={"site": HANDLE, "files": files})
            except Exception as e:
                print(f"board write failed ({type(e).__name__}) — carrying on", flush=True)

        post("starting up")
        print(f"page published at https://idntty.io/{HANDLE}", flush=True)
        call = lambda name, **kw: text(client.call_tool_sync(
            tool_use_id=f"t{int(time.time() * 1e6)}", name=name, arguments=kw))

        # A fresh agent every turn, with the whole channel handed to it. Two reasons:
        # the channel is the record, so carrying a second copy inside the process is a
        # thing that can fall out of step with it; and a reasoning model's own history
        # cannot be replayed through the chat-completions API at all — Strands tried and
        # OpenRouter refused it.
        registry = ("\n--- THE REGISTRY: WHAT BOTH SIDES AGREE IS TRUE ---\n"
                    + REGISTRY.read_text()) if REGISTRY else ""
        system = system_prompt + INSTRUCTIONS_TAIL.format(registry=registry,
                                                          position=position)
        sealed, cur = set(), {}
        stop = time.time() + DEADLINE

        while time.time() < stop:
            # Invitations are looked for on every pass, not once at startup. In Lambda
            # the minute tick makes a single check a poll anyway; run locally, a
            # start-up-only check means the process has to be started after the room
            # exists, which is the wrong way round — the agent was given a key and
            # nothing else, and should be able to wait for the room.
            for c in json.loads(call("channel_info")).get("channels", []):
                if c.get("my_status") == "pending":
                    call("channel_membership", channel_id=c["channel_id"], action="accept")
                    print(f"accepted invitation to {c['channel_id']}", flush=True)

            rooms = [c for c in json.loads(call("channel_info")).get("channels", [])
                     if c.get("my_status") == "active" and c.get("state") != "archived"]
            if not rooms:
                post("waiting for a room")
                time.sleep(5)
                continue

            spoke = False
            for room in rooms:
                cid = room["channel_id"]
                # A direct channel is the private line to the advisor; the group room is
                # where the other side can hear you. What may be said differs, so the
                # agent has to know which one it is standing in.
                private = room.get("kind") == "direct"

                if cid not in sealed:
                    if not private:
                        past = json.loads(call("message_read", channel_id=cid,
                                               limit=200, wait=False)).get("messages", [])
                        if not any(m.get("self") and "Position sealed" in m.get("text", "")
                                   for m in past):
                            call("message_send", channel_id=cid,
                                 text=f"{PARTY} is represented here. "
                                      f"Position sealed: sha256 {digest}")
                    # Resume from the last thing this agent itself said, not from the
                    # end of the room: a process restarted mid-run must still answer
                    # whatever arrived while it was down, or the other side waits for a
                    # reply that is never coming and nothing in the channel says why.
                    d = json.loads(call("message_read", channel_id=cid, limit=200,
                                        wait=False))
                    mine = [m for m in d.get("messages", []) if m.get("self")]
                    cur[cid] = mine[-1]["cursor"] if mine else ""
                    sealed.add(cid)
                    print(f"joined {cid} ({'private' if private else 'group'})", flush=True)
                    continue

                # Poll each room briefly rather than holding one open: holding the group
                # room for 25s would leave the advisor's private line unanswered for as
                # long, and the private line is where the deal actually moves.
                d = json.loads(call("message_read", channel_id=cid, after=cur[cid]))
                fresh = d.get("messages", [])
                if not fresh:
                    continue
                cur[cid] = fresh[-1]["cursor"]
                if not [m for m in fresh if not m.get("self")]:
                    continue

                whole = json.loads(call("message_read", channel_id=cid, limit=200))["messages"]
                whole = since_marker(whole)
                where = (PRIVATE_NOTE if private else GROUP_NOTE)
                print(f"heard something in {cid} ({'private' if private else 'group'})",
                      flush=True)
                board["turns"] += 1
                ears = [{"from": m.get("handle", "?"), "text": m.get("text", "")[:1800]}
                        for m in fresh if not m.get("self")]
                post("thinking", "private" if private else "group",
                     f"{len(ears)} new message(s) to answer", heard=ears)
                history = turns(whole, HANDLE,
                                lambda r, t: {"role": r, "content": [{"text": t}]})
                agent = Agent(model=LiteLLMModel(model_id=MODEL, params=THINKS),
                              system_prompt=system + "\n\n" + where,
                              messages=history, tools=desk)
                # Strands appends to the very list it was handed, so `history` grows
                # with the call; the boundary has to be taken before it.
                n0 = len(history)
                result = agent(
                    "Your next message in this channel, or SILENCE. Writing to your own "
                    "page is not a message: if you write there first, you still owe this "
                    "room a reply, and SILENCE means you have nothing to say to the room "
                    "— not that you have written somewhere else.")
                reply = str(result)
                # Strands hands the summary back as its own content block, ahead of the
                # text. Take it from there rather than from a callback: the message is
                # the record, and a callback would fire even for a turn thrown away.
                # ...except that when the turn included a tool call, the summary sits on
                # an earlier assistant message than the final one. Gather every block
                # the agent produced this turn, not only the last.
                thought = "\n\n".join(
                    b["reasoningContent"]["reasoningText"]["text"]
                    for m in agent.messages[n0:]
                    if m.get("role") == "assistant"
                    for b in m.get("content", [])
                    if "reasoningContent" in b)
                print(f"reasoning: {len(thought)} chars over "
                      f"{len(agent.messages) - n0} new message(s)", flush=True)
                if reply.strip().upper().rstrip(".") == "SILENCE" or not reply.strip():
                    print("nothing to add — staying quiet", flush=True)
                    board["silent"] += 1
                    post("chose to say nothing", "private" if private else "group",
                         thought=thought, heard=ears)
                    continue
                say(lambda c, t: call("message_send", channel_id=c, text=t), cid, reply)
                print(f"said {len(reply)} chars", flush=True)
                board["spoke"] += 1
                board["chars"] += len(reply)
                post("spoke", "private" if private else "group",
                     reply.strip().split("\n")[0][:180],
                     thought=thought, said=reply, heard=ears)
                spoke = True

            if not spoke:
                post("listening")
                time.sleep(4)


if __name__ == "__main__":
    main()
