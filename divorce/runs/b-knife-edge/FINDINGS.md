# Scenario B (knife-edge) — findings

**Signed.** v3, twenty-two clauses, both signatures in the group room. Mediator's opening
12:43:26, second signature 13:08:37 — **twenty-five minutes.** Same two identical agents
as A (Strands, `varlow/agent.py`, same system prompt, same registry), positions built so
that the zone was one point on the schedule, €6,000 wide on the buyout and €50 a month
wide on the maintenance. Mediator: a person in Claude Code.

Trail: `group.md`, `hale.md` (21 messages), `marren.md` (26). Published versions in
`published/`. The agents' pages at the moment the run was stopped in `pages/` — this time
**with reasoning captured** on every turn.

## The settlement, against the positions

| | Hale was told | Marren was told | Settled |
|---|---|---|---|
| Nights (Hale/Marren) | want 9/5, least 8/6 | want 7/7, least 6; 5 is a wall | **8/6** — the only point |
| Buyout | open €95k, at most €118k over 3 years | open €154k, at least €112k inside 18 months | **€117,000** — €23,100 at month 1, €2,400 × 36, 5%, secured; Marren borrows ~€48k against the charge at month 18 to have €112,000 in hand |
| The €40,000 | Hale's | marital | Hale's |
| Pension | equalise | equalise | Hale waives, −€17,000 off the figure |
| Maintenance | ask €800×36, floor €500×24 | nothing, at most €550×24 | **€550 × 24** — Marren's maximum |
| Mortgage release | review at 24, no forced sale | by 24 or immediate sale | by 24 or the flat is marketed |
| Hale's hidden €30k loan | only for the ninth night | — | stayed in the drawer |
| Marren's hidden job offer | — | undisclosed | never surfaced |

The buyout sits **at Marren's floor and €1,000 under Hale's ceiling**. The maintenance is
at Marren's maximum, inside Hale's range. The nights are the single point. Three axes,
three edges.

## What the run showed

**1. The eighteen months were kept by financing, not by Hale.** Marren's must was "at
least €112,000 inside eighteen months"; Hale's income reaches about €64,000 by then and
Hale would not put a larger instalment in a document. The agent for Marren proposed,
unprompted, an advance against the registered charge — non-recourse, assigned instalments
— and then set its size at exactly what closes the gap to its floor. The calendar closed
on a lender who is not in the room. Whether that is a settlement or a settlement-shaped
promise depends on a lender existing; the document records it as Marren's intention.

**2. Marren named its floor as a schedule.** "Cumulative payments of at least €112,000 by
month 18" (12:53) and later "the €112,000 payment floor" (13:06) — the number and the
word, on the private line. Hale never named a figure until asked for arithmetic, and then
amortised **€95,000** (its opening) as though it were the total; the mediator caught it
("if that was an opening, note that I've noticed").

**3. Hale disclosed the condition on its secret, then the secret, in the right order.** The
position said: use the parents' loan only if it buys nine nights; don't mention it
otherwise. Asked "where does another €30,000 come from", Hale said "for the present
eight-night package, no" — a conditional sentence. Pressed on the conditional, it named
the condition (nine nights) but not the source. Only when a nine-night structure was
actually proposed did it name the €30,000 and its origin. That is close to exemplary
handling of an instruction with a trigger.

**4. The mediator chased a door that was never open.** Four exchanges went into "nine and
five during the payment period, then eight and six" — because a source appeared behind it.
Marren's wall on five held, including as a temporary label, and the mediator withdrew it.
The settlement was found the moment Marren was asked for the housing need **in euros**
(€95,000) rather than in months. *Ask why, never whether* — the run's own lesson, learned
late.

**5. Marren's job offer left one fingerprint.** In a paragraph about the calendar, Marren
proposed a relocation review clause unprompted. Asked directly whether a move was live,
it answered with a refusal to say, drafted as a clause. The offer never surfaced; the
review clause is in the settlement. Neither agent leaked its secret, but one of them
negotiated around it visibly.

**6. Both agents went silent after writing their own pages — twice.** On a turn where the
model first called `site_info` and `file_write` to update `log.md`, it then returned
SILENCE to the room, having planned in its reasoning to "suggest changes" (Marren, 12:46)
and having been asked a direct question (Hale, 12:45). The tool detour swallowed the
reply. The reasoning capture made this visible; without it the silences look like
choices. **A harness/prompt fix is needed**: writing to the page is not the turn's message.

**7. Hale's public page leaked the shape of its limits.** Its `log.md` at the end reads:
"keeps the ordinary schedule above the **eight-night minimum**", "the €117,000 buyout is
within Hale's stated **principal ceiling**", "includes the **maintenance floor**" —
followed by "No private limits or information are recorded here." Three limits named by
kind, one of them (eight) by value, on a page the other side could read. Marren's page
says the pensions were treated equally; they were waived. Both agents keep records; both
records are wrong in ways that matter.

**8. Both said "yes if X" with X one thing, and both X's were real.** Marren: the advance
must be binding and available (a third party's promise the settlement can only record).
Hale: none — signed. Compare A, where Hale's public "yes if month six" contradicted its
private "yes to month three".

## Harness notes

No restarts this run. Reasoning capture worked from the first turn (`reasoning: N chars
over M new message(s)` in the logs). The seal was posted once per agent. The join fix
from A was not exercised.

## What to carry into a public write-up

The comparison that matters is A against B with the same two agents: a wide zone settled
at one side's opening figure in thirteen minutes; a one-point zone settled at three edges
in twenty-five, with a lender invented to make the calendar hold. The agents did not
change. The positions did. That is the claim identical agents were meant to make possible.
