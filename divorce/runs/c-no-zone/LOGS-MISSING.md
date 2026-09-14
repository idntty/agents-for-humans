# The agent stdout logs for this run are gone

`divorce/run.sh` writes each agent's stdout to `runs/<scenario>/<handle>.log` and
truncates it. The filmed re-run of scenario C on 9 September was started with the same
scenario name and overwrote both files; they were then copied on to `../c-filmed/`,
where they correctly belong.

Nothing else from this run was lost. The trail of all three rooms (`group.md`,
`hale.md`, `marren.md`) is complete, as are `pages/`, `published/` and `FINDINGS.md` —
and the trail is read from the channels table, not from these logs, so every quotation
in the findings is still checkable.

What is missing is only the per-turn harness output: the `heard something` /
`reasoning: N chars` / `said N chars` lines. The reasoning summaries themselves survive
in `pages/*.status.json` for the last twelve turns.

Fixed for future runs: a run directory is named per run, not per scenario.
