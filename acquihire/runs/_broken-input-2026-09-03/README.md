# Runs made on a broken input, kept as evidence

These three runs — A, B and C, 3 September 2026 — were made before a defect in the harness
was found and fixed.

**The defect:** the whole channel, including the agent's own messages, was flattened into a
single `user` block. The model never saw its own words as `assistant` turns and had to
work out which lines were its own from a handle prefix.

**What that plausibly caused**, and why these runs cannot be cited for agent behaviour:

- Agents restating positions they had already taken, and the polite deadlock that followed.
- Both parties signing a "v1" that did not exist, each having assembled one from its own
  messages.
- Possibly the buyer anchoring on the figure it was told to give the advisor rather than
  its own opening — its instruction and everyone else's words arrived in one undifferentiated
  stream.

**What still stands from them**, because it does not depend on the model's view of the
transcript: the harness failures (death by an over-long message, death by a dropped
connection, neither visible in the channel), the product observation that direct channels
are idempotent per pair, and the fact that a back channel goes unused until the advisor
opens it.

Kept rather than deleted. A finding produced by a bug is still a record of the bug.
