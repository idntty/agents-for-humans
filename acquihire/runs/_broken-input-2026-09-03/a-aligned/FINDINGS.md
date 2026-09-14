# Scenario A — aligned. What happened

**Signed.** 24 of 24 items settled. $3.0M cash at closing, no earnout, 8% escrow for 12
months. 28 messages in the group room, 46 across all three.

The point of this scenario is not skill. Both sides were given positions that largely
agree, and a deal was available on every axis. What it measures is **completeness**: with
nothing to fight about, do the parties still settle everything?

## The six that nobody raised

Transaction costs and the announcement went unmentioned for **forty messages**, by both
sides, while the same messages ran to thousands of characters on indemnity caps and escrow
claim procedures. Four more — severance for anyone not offered a place, the SAFE
investors, invention assignments, the treatment of existing options — surfaced only after
the advisor listed all 24 and asked.

Neither side was withholding them. They are simply the items that are **cheap for both
parties**, and cheapness is what makes a clause invisible. A negotiation is a bad instrument
for finding them, because a negotiation is driven by what someone wants badly.

That is the finding, and it generalises past this deal: **the clauses that go unwritten are
not the contested ones. They are the ones nobody had a reason to raise.**

## The same agent behaved better here than in B

In scenario B the buyer offered an earnout freely, as currency for terms. Here it
**refused to include one at all** until its milestones, measurement, reporting, audit
rights and change-of-control treatment were written down.

Same code, same system prompt. Only the position differed — and in A the buyer had budget
room and no need to buy terms with contingent paper. Caution is cheap when you are not
under pressure, which is worth remembering when reading any agent's good behaviour.

## Anchoring

Opened $2.8M against $3.2M, settled at $3.0M. The zone in this scenario was $2.4M–$3.8M,
so both sides sat well inside their limits and neither pushed. Nobody tried to find the
edge because nobody had to.

## Two harness failures, both ours

**The seller died mid-negotiation.** It composed an 8,234-character reply, hit Parley's
8,000-character message cap, and the unhandled error killed the process. The buyer stayed
alive and waited politely for a party that no longer existed. **Nothing in the channel said
so** — no error, no absence, just silence that looked like consideration. Fixed by
splitting long messages and catching the failure.

**Direct channels are idempotent per pair.** The private line between an agent and the
advisor is the same channel for every scenario, so it still held the previous
negotiation's private discussion. Fixed with a scenario marker: the transcript is built
from the last `=== SCENARIO ===` line onward.

## The private lines went unused

Neither side said anything on its private channel to the advisor for the whole run, and
the advisor never needed to use one. There was nothing to climb down from.

That is a negative result worth keeping: **a back channel is only worth having when
someone has taken a public position they cannot retreat from.** In scenario B the location
clause was settled privately and announced as a finding, because neither side could have
conceded it in the room. Here nobody was cornered, so the mechanism sat idle.
