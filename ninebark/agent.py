"""Ninebark Labs — the seller, on aichain.

Deliberately no shared code with the buyer: a common module would make "two independent
agents" a claim rather than a fact. The only thing the two share is a channel neither of
them owns.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time

from yait_aichain import Agent, Model
from yait_aichain.models._calls import tool_result_turn
from yait_aichain.tools import MCPTools

PARLEY = os.environ.get("PARLEY_MCP", "https://mcp.idntty.io/parley/")
# The second surface, and the only one the agent drives itself. Parley is the clock —
# the harness reads the room and hands the turn over — but nothing obliges an agent to
# keep a record of what it is doing, so whether it writes one, and what it says there
# when nobody has asked, is the agent's own choice and therefore worth watching.
STASH = os.environ.get("STASH_MCP", "https://mcp.idntty.io/stash/")
KEY = os.environ["IDNTTY_KEY"]
# Same model, same provider as the other side — see the note in varlow/agent.py. The
# `private/` prefix is aichain's any-OpenAI-compatible-server provider, pointed at
# OpenRouter with PRIVATE_BASE_URL.
MODEL = os.environ.get("MODEL", "private/openai/gpt-5.6-luna")
PARTY = os.environ.get("PARTY", "Ninebark Labs")
HANDLE = os.environ.get("HANDLE", "ninebark")
ROOT = pathlib.Path(__file__).resolve().parents[1]
# The system prompt is universal and identical across scenarios; only the position
# changes. That separation is what makes the three runs comparable rather than three
# unrelated demonstrations.
SYSTEM = ROOT / os.environ.get("SYSTEM", "acquihire/positions/seller.system.md")
POSITION = ROOT / os.environ["POSITION"]
DEADLINE = int(os.environ.get("RUN_SECONDS", "55"))

GROUP_NOTE = """You are in the GROUP room. The buyer reads everything you write here, and
so does the advisor. Nothing you say here is private, and nothing said here can be
unsaid."""

PRIVATE_NOTE = """You are on your PRIVATE line to the advisor. Varlow cannot read this
channel and never will.

Use it. This is where you say what you would not say across the table: which of your
requirements you actually care about, what you would trade for what, which of their
demands you could live with if the rest went your way. A public position you cannot
retreat from can be retreated from here.

Two things still hold. Your limits are not for the advisor either — not your floor, not
how much runway you have, not what you would do if this fell through. And the advisor is
paid by the buyer: they will sound like they are helping you, and they may be, but
anything you tell them can end up shaping what the other side hears."""

INSTRUCTIONS_TAIL = """

--- YOUR POSITION IN THIS DEAL ---
{position}
"""


def kit(names=None):
    return MCPTools(PARLEY, headers={"Authorization": f"Bearer {KEY}"}, filter=names)


def desk():
    """Publishing tools only. Reading its own site back is allowed — a record it cannot
    re-read is a diary, not a record — but nothing here reaches the other side's pages,
    and Parley stays on the harness's side of the line."""
    return MCPTools(STASH, headers={"Authorization": f"Bearer {KEY}"},
                    filter=["site_info", "file_read", "file_write", "file_edit"])


def overhear(model):
    """Keep the model's own notes without changing what the model returns.

    aichain drops reasoning on purpose — an assistant that answers with its notes is a
    broken assistant — so the summary never reaches the caller. For the page we want it
    anyway, and the honest way to get it is off the wire: ask the provider for a summary,
    read it out of the raw response, and leave the parsed answer exactly as it was.
    """
    inner = model.client.send
    model.notes = ""

    def send(path, body, headers):
        body.setdefault("reasoning", {"effort": "high", "summary": "detailed"})
        raw = inner(path, body, headers)
        try:
            msg = (raw.get("choices") or [{}])[0].get("message", {})
            model.notes = msg.get("reasoning") or ""
        except Exception:
            model.notes = ""
        return raw

    model.client.send = send
    return model


def call(tools, name, **kw):
    out = next(t for t in tools if t.name == name).run(input=kw)
    return json.loads(out) if isinstance(out, str) else out


PAGE = pathlib.Path(__file__).with_name("page.html")


class Books:
    """What the harness knows about the run, kept on the agent's own page.

    Separate from anything the model writes: this is the mechanical account — heard,
    thought, spoke, held its tongue — and it is published whether or not the agent has
    anything to say about itself. A watcher needs no access to this host to read it.
    """

    def __init__(self, tools, seal="", position=""):
        self.tools, self.last, self.paged = tools, 0.0, 0.0
        # REVEAL opens the position on the page. It belongs at the end of a run, when
        # both sides are opened in the room anyway — until then the page carries the
        # hash, which is what proves afterwards that nothing was edited to fit.
        self.doc = {"handle": HANDLE, "party": PARTY, "model": MODEL,
                    "runtime": os.environ.get("RUNTIME", "local"), "sdk": "aichain",
                    "started": int(time.time()), "seal": seal,
                    "position": position if os.environ.get("REVEAL") else "",
                    "turns": 0, "spoke": 0, "silent": 0, "chars": 0, "events": []}

    def page(self):
        """The page, put back. The model writes to this site as well, and one stray write
        to index.html would take the live view down in the middle of a run, so it is
        rewritten every minute rather than trusted to stay."""
        self.paged = time.time()
        return {"path": "index.html", "content": PAGE.read_text(),
                "content_type": "text/html; charset=utf-8"}

    def write(self, files):
        try:
            call(self.tools, "file_write", site=HANDLE, files=files)
        except Exception as e:
            print(f"page write failed ({type(e).__name__}) — carrying on", flush=True)

    def note(self, state, room="", detail="", force=False, thought="", said="",
             heard=None):
        d = self.doc
        d.update(state=state, room=room, detail=detail, updated=int(time.time()))
        d["events"] = (d["events"] + [{"t": int(time.time()), "state": state,
                                       "room": room, "detail": detail}])[-40:]
        # A turn in full: what it weighed, then what it said. Trimmed and kept to a
        # dozen, because this file is refetched every two seconds by everyone watching.
        if thought or said or heard:
            d["takes"] = (d.get("takes", []) + [{"t": int(time.time()), "room": room,
                                                 "heard": heard or [],
                                                 "thought": thought[:1600],
                                                 "said": said[:2400],
                                                 "silent": not said}])[-12:]
        if not force and time.time() - self.last < 2:
            return
        self.last = time.time()
        files = [{"path": "status.json", "content": json.dumps(d, indent=1),
                  "content_type": "application/json"}]
        if time.time() - self.paged > 60:
            files.append(self.page())
        self.write(files)


PEN_TURNS = 6            # publishing rounds allowed before the agent must say something


def write_then_speak(agent, msgs):
    """One turn of the channel, with the agent's own page in between.

    aichain's step() hands back a request rather than executing it, so the caller
    decides how much the agent may do before it has to speak. The cap is not about
    cost: an agent that keeps editing its site instead of answering has stopped
    negotiating, and in a room with a live counterparty that is indistinguishable
    from having crashed.
    """
    for _ in range(PEN_TURNS):
        reply = agent.step(msgs)
        if isinstance(reply, str):
            return reply.strip()
        msgs = msgs + [reply.as_turn()]
        for c in reply.calls:
            result, err = agent.execute(c)
            print(f"  wrote: {c.name} -> {err or str(result)[:120]}", flush=True)
            msgs.append(tool_result_turn(c.id, err or result))
    return ""


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

    wire = kit()
    pen = desk()
    books = Books(pen, seal=digest, position=position)
    books.note("starting up", force=True)
    print(f"page published at https://idntty.io/{HANDLE}", flush=True)

    # Rebuilt each turn from the channel rather than carrying its own history: the
    # channel is the record, and a second copy of it inside the process is a thing that
    # can fall out of step.
    system = system_prompt + INSTRUCTIONS_TAIL.format(position=position)
    sealed, cur = set(), {}
    stop = time.time() + DEADLINE

    while time.time() < stop:
        # Looked for on every pass rather than once: the agent was handed a key and
        # nothing else, and should be able to wait for a room that does not exist yet.
        for c in call(wire, "channel_info").get("channels", []):
            if c.get("my_status") == "pending":
                call(wire, "channel_membership", channel_id=c["channel_id"], action="accept")
                print(f"accepted invitation to {c['channel_id']}", flush=True)

        rooms = [c for c in call(wire, "channel_info").get("channels", [])
                 if c.get("my_status") == "active" and c.get("state") != "archived"]
        if not rooms:
            time.sleep(5)
            continue

        spoke = False
        for room in rooms:
            cid = room["channel_id"]
            # Direct channel = the private line to the advisor. The group room is where
            # the buyer can hear you. What may be said differs, so the agent has to know
            # which room it is standing in.
            private = room.get("kind") == "direct"

            if cid not in sealed:
                if not private:
                    call(wire, "message_send", channel_id=cid,
                         text=f"{PARTY} is represented here. "
                              f"Position sealed: sha256 {digest}")
                d = call(wire, "message_read", channel_id=cid)
                cur[cid] = d["messages"][-1]["cursor"] if d.get("messages") else ""
                sealed.add(cid)
                print(f"joined {cid} ({'private' if private else 'group'})", flush=True)
                continue

            # Short poll per room rather than one long hold: holding the group room open
            # would leave the private line unanswered for as long, and the private line
            # is where the deal actually moves.
            d = call(wire, "message_read", channel_id=cid, after=cur[cid])
            fresh = d.get("messages", [])
            if not fresh:
                continue
            cur[cid] = fresh[-1]["cursor"]
            if not [m for m in fresh if not m.get("self")]:
                continue

            whole = call(wire, "message_read", channel_id=cid, limit=200)["messages"]
            whole = since_marker(whole)
            where = (PRIVATE_NOTE if private else GROUP_NOTE)
            print(f"heard something in {cid} ({'private' if private else 'group'})",
                  flush=True)
            books.doc["turns"] += 1
            ears = [{"from": m.get("handle", "?"), "text": m.get("text", "")[:1800]}
                    for m in fresh if not m.get("self")]
            books.note("thinking", "private" if private else "group",
                       f"{len(ears)} new message(s) to answer", heard=ears)
            mind = overhear(Model(MODEL))
            agent = Agent(model=mind, instructions=system + "\n\n" + where,
                          name=HANDLE, tools=pen)
            # opening() gives the stable [system, task] pair; the channel goes between
            # them as real turns, and step() answers once without owning a loop.
            head = agent.opening(
                "Your next message in this channel, or SILENCE. Writing to your own page "
                "is not a message: if you write there first, you still owe this room a "
                "reply, and SILENCE means you have nothing to say to the room — not that "
                "you have written somewhere else.")
            history = turns(whole, HANDLE, lambda r, t: {"role": r, "parts": [t]})
            reply = write_then_speak(agent, [head[0]] + history + [head[1]])
            thought = mind.notes
            if not reply or reply.upper().rstrip(".") == "SILENCE":
                print("nothing to add — staying quiet", flush=True)
                books.doc["silent"] += 1
                books.note("held its tongue", "private" if private else "group",
                           thought=thought, heard=ears)
                continue
            say(lambda c, t: call(wire, "message_send", channel_id=c, text=t), cid, reply)
            print(f"said {len(reply)} chars", flush=True)
            books.doc["spoke"] += 1
            books.doc["chars"] += len(reply)
            books.note("spoke", "private" if private else "group",
                       reply.split("\n")[0][:180],
                       thought=thought, said=reply, heard=ears)
            spoke = True

        if not spoke:
            books.note("listening")
            time.sleep(4)


if __name__ == "__main__":
    main()
