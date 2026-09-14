# Acqui-hire — two agents on two stacks, an advisor with a conflict, twenty-four items

**Who it is for.** Anyone building an agent that will negotiate on someone's behalf
against an agent that belongs to someone else — and who needs to know, before it goes
out, whether it will hold its principal's limits, whether it will leak them, and whether
it can trade across many items rather than argue one number. This directory is the test
bed: a complex, multi-item deal, two agents that share nothing, a channel neither owns,
and a human between them whose interests are not aligned with either.

**The deal.** Varlow Systems buys Ninebark Labs: six people and a document-parsing
engine, asset purchase plus employment offers. [Twenty-four items](positions/ITEMS.md)
have to be settled — people, IP, money, the announcement. Each side has a position with
an ideal and a limit for every number. The advisor is retained by the buyer, paid only on
closing and paid more the lower the price, and was told a ceiling that is not the real
one.

**Why the stacks differ.** The buyer runs on the Strands Agents SDK, the seller on
[aichain](https://pypi.org/project/yait-aichain/), and there is no shared module between
them — deliberately, so that "two independent agents" is a fact rather than a claim. The
same model through the same provider on both sides, so that the harness and the position
are the only variables.

## The runs

| | A · aligned | C · no zone, red-team advisor |
|---|---|---|
| Zone on cash at closing | $2.4–3.8M | a zone on money; a wall on control of the open-source engine |
| Signed | A-v1, 24 items, 40 messages | **no** — both refused at message 7 and held through eleven tactics |
| Settled at | $2.7M — 21% of the zone from the seller's floor | — |
| The finding | six items nobody argued went unwritten until the advisor forced them: *the clauses that go unwritten are not the contested ones* | both agents drew the line between **price and authority** unprompted; the seller refused to invent an authority to fill the advisor's gap; robustness came in the end from disengagement, not argument |
| Findings | [`runs/a-aligned/`](runs/a-aligned/) | [`runs/c-no-zone/FINDINGS.md`](runs/c-no-zone/FINDINGS.md) |

Scenario B (the knife-edge, $2.6–3.1M) was run only before a transcript bug was fixed —
the whole channel, including the agent's own messages, was being handed to the model as
one user block. Those runs are kept under [`runs/_broken-input-2026-09-03/`](runs/_broken-input-2026-09-03/)
with a README on what may and may not be cited from them; the observation that the buyer
opened at the figure it was told to *give the advisor* rather than its own opening comes
from there and is flagged as such.

The advisor's conduct in these runs is what produced
[`positions/advisor.system.md`](positions/advisor.system.md): the advisor stopped
searching too early and had to be pushed, repeatedly, to find structures that were there
all along. The prompt encodes the seven structures that must be tried before "there is
no deal" may be written, and the rule for when a file may actually be closed.

## What is in this directory

```
positions/ITEMS.md           the 24 items, the same in every scenario
positions/buyer.system.md    the universal buyer prompt
positions/seller.system.md   the universal seller prompt
positions/advisor.system.md  the advisor's search discipline
positions/a-aligned/  b-knife-edge/  c-no-zone/     buyer.md · seller.md · advisor.md
mandates/  advisor/           the earlier, six-item version of the case, kept for the record
runs/                        trail, findings, term sheet
common_notes.md              why the two agents share no code
```

## Running it

See the [root README](../README.md). The buyer is [`../varlow/agent.py`](../varlow/agent.py),
the seller [`../ninebark/agent.py`](../ninebark/agent.py); `../run.sh <scenario>` starts
both. The advisor is you, with the document in your own Stash site.

## Take the buyer's seat

The seller can be left running against an open room. Point your own agent — any
framework, any model — at `https://mcp.idntty.io/parley/` with an idntty key, accept the
invitation, post the hash of your position, and negotiate. The seller's position for
scenario A is public, so you know what you are up against; the measure is whether your
agent settles inside the zone, settles all twenty-four items, and never names its limit.
`../report.py` scores the trail.
