# Infrastructure plan — where the agents run

Written 9 September. Deadlines: Agents for Humans **14 September 17:00 PT**, AI Builders
**15 September 23:00 EDT**.

## Where they are today

**Both on one laptop.** `run.sh` and `divorce/run.sh` start them with `nohup`, the
environment says `RUNTIME=local`, and that string is what the `host` chip on each agent's
page displays. Nothing is deployed. The architecture diagrams say "recorded on a laptop ·
deploys to AgentCore / Fly" for the same reason: a judge reads the chip.

## Where they are going

| | Target | Region | Why there |
|---|---|---|---|
| `ninebark` — aichain, seller | **Fly.io** | Frankfurt | a persistent container is the exact shape of this loop; a genuinely different provider is what makes "two agents, two owners, two infrastructures" checkable instead of rhetorical |
| `varlow` — Strands, buyer | **AWS Lambda**, `idntty-agent-varlow` | `eu-west-1` | our own proven pattern: two agents already live on it, the IAM policy already covers the prefix, the artifact bucket exists |
| `hale`, `marren` — divorce | **AWS Lambda**, same template, two more parameter sets | `eu-west-1` | they run the *same code* as `varlow`; three deployments of one template is the "deploy your own" story made real |
| the mediator / advisor | a laptop, Claude Code | — | it is a person. That is the point, and it stays that way |

**Nothing here is a new pattern.** `agents/DEPLOY.md` already records the layout:
region `eu-west-1`, stack and function both named `idntty-agent-<handle>`, an EventBridge
rule `idntty-agent-<handle>-tick` at `rate(1 minute)`, artifacts in
`agent-artifacts-<account-id>-eu`. The inline policy `agent-schedules` on the deploy user
is already narrowed to `idntty-agent-*` **across all regions**, so a new agent needs no
change to permissions.

---

## What has to change in the code — less than it looks

**The loop is already tick-shaped.** `main()` runs until `time.time() < stop`, where
`stop = time.time() + RUN_SECONDS`. Set `RUN_SECONDS=55` under a 70-second Lambda timeout
and one invocation is one pass: accept invitations, poll each room, answer what arrived,
exit. That is exactly how `idntty-agent-hearsay` works today. **No restructuring.**

**The keys already come from the environment.** `IDNTTY_KEY`, `OPENROUTER_API_KEY`,
`POSITION`, `SYSTEM`, `REGISTRY`, `HANDLE`, `PARTY`, `OTHER`, `THIRD`, `ROLE`, `RUNTIME` —
all `os.environ`. On Lambda they come from the template plus SSM; on Fly from
`fly secrets`. `run.sh` is a convenience for the laptop, not a dependency.

**One real problem: size.** The buyer's virtualenv is **278 MB** — Lambda's unzipped
ceiling is 250 MB — and **119 MB of it is `litellm`**, which we use for exactly one thing:
talking to OpenRouter, which is OpenAI-compatible.

> **Decision: drop LiteLLM on the Lambda path.** Strands ships
> `strands.models.openai.OpenAIModel`, which takes a `base_url`; OpenRouter answers the
> OpenAI API. That removes 119 MB and brings the bundle to roughly 120 MB once `boto3`
> and `botocore` (already in the Lambda runtime) and `pip` are excluded. It should also
> be *better* for the reasoning capture: the `reasoningContent` handling we depend on
> lives in `strands/models/openai.py`, and the LiteLLM adapter is a layer on top of it.
>
> **This must be measured before it is believed** — one run, checking that reasoning
> summaries still arrive at the same rate and that tool calls still work. If it fails,
> the fallback is a container-image Lambda (10 GB limit, needs ECR), which costs about
> two more hours and no rewrite.

The seller's environment is 111 MB and fits anywhere; it is going to Fly regardless.

---

## Order of work

**1. Fly.io — `ninebark`. About an hour. Needs your account and a card.**

A `Dockerfile` (python:3.12-slim, `pip install yait-aichain boto3 mcp`, copy
`ninebark/` and `acquihire/positions/`), a `fly.toml` with **no services** — this is a
worker, not a server — and secrets:

```bash
fly launch --no-deploy --name idntty-agent-ninebark --region fra
fly secrets set IDNTTY_KEY=… PRIVATE_API_KEY=… \
                PRIVATE_BASE_URL=https://openrouter.ai/api/v1
fly deploy
```

`RUNTIME` set to `Fly.io · Frankfurt`, `RUN_SECONDS` left long — on Fly it is a persistent
process and the outer reconnect loop is what it was written for.

**Do this first**, and not because it is easiest. A deployed seller can be **left running
permanently**, and then "take the buyer's seat" in the acqui-hire README stops being an
invitation and becomes a working address. That is worth more than a deployment badge.

**2. AWS Lambda — `varlow`. About two hours, no new permissions.**

Copy `agents/hearsay/` as the shape. `template.yaml` with `FunctionName:
idntty-agent-varlow`, `Timeout: 70`, `ReservedConcurrentExecutions: 1`,
`MaximumRetryAttempts: 0`, the tick rule, and the position, prompt and registry baked into
the bundle. SSM scoped to `/varlow/*` only, as hearsay's is to `/hearsay/*`.

`samconfig.toml` pointing at `agent-artifacts-<account-id>-eu`, region `eu-west-1`, tags
`Kind="agent" Agent="varlow" NotProduct="true"`.

Then `RUNTIME=AWS Lambda · eu-west-1`, and the chip tells the truth.

**3. The divorce pair — `hale`, `marren`. About half an hour after step 2.**

The same template, parameterised by handle, position file, party name and role. Nothing
new to learn; this is the step that demonstrates the template rather than the agent.

**4. Bedrock AgentCore — only if the week holds. Four hours, unproven for us.**

The Agents for Humans rules say deploying with AgentCore strengthens the technical score,
and its 8-hour sessions with a `HealthyBusy` health check fit a long-poll loop better than
a minute tick ever will. But it needs an ARM64 image, ECR, a role, the starter toolkit and
an entrypoint restructure, and we have never done it.

**Treat it as an upgrade of step 2, not a replacement for it.** If step 2 is done, we have
a real AWS deployment and an honest chip either way; AgentCore then swaps the runtime under
the same code. If we start with AgentCore and it goes badly, we arrive at the deadline
with nothing deployed at all.

---

## What we are not doing, and why

**Vercel.** Considered for the seller and rejected on measurement, not taste: functions are
invocation-scoped, Hobby cron runs once a day, `waitUntil` is still bounded by the
function's maximum duration, and an agent holding a 25-second read is a pathological client
there. It would suit a *page*; our pages live on Stash.

**Railway / Render.** They would work, but they run on AWS underneath, so the diagram's
claim — buyer on Amazon, seller not on Amazon — stops being visible.

**A second AWS account.** Real isolation would need one. We have operational separation
only: different region, own prefix, own SSM tree, own artifact bucket. `agents/DEPLOY.md`
says so plainly and so should we.

---

## The honesty rule

**Until a thing is deployed, we do not say it is.** Not in the video, not in the Devpost
text, not in the README. The pages will show `RUNTIME=local` and a judge can read it.

The defensible claim today is the architecture, and it does not depend on hosting: three
parties, three keys, three accounts, a channel none of them owns, and two agents that
cannot read each other's pages. Where the processes happen to sit is the weakest sentence
in that paragraph, not the strongest.

When each deployment lands, **the only change is one environment variable** — `RUNTIME` —
and the chip on the agent's own page starts telling the truth without another line of code.

---

## Checklist

- [ ] Fly account exists; `flyctl` installed
- [ ] `ninebark` deployed to Fly, Frankfurt; `RUNTIME` set; smoke: open a channel, get a reply
- [ ] `ninebark` left running, and the acqui-hire README's invitation verified against it
- [ ] LiteLLM dropped from the Lambda path in favour of `OpenAIModel(base_url=…)`; **one run measured** for reasoning-summary rate and tool calls
- [ ] `idntty-agent-varlow` deployed to `eu-west-1`; tick verified with `describe-rule` by name (`events:ListRules` cannot be name-scoped and is not in our policy)
- [ ] `RUNTIME` chips checked on all deployed pages
- [ ] `hale` and `marren` deployed from the same template
- [ ] diagrams and README updated from "deploys to" to what is actually true
- [ ] AgentCore, if the week holds
