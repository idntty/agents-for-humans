"""Measure a run from its trail.

Reads acquihire/runs/<scenario>/{group,varlow,ninebark}.md — the saved channels, not the live
table — so a run stays measurable after the agents are gone and the numbers can be
recomputed by anyone who clones the public repo without AWS credentials.

    python3 report.py a-aligned
    python3 report.py --all            # every scenario with a trail, plus comparison

What it computes is mechanical only. Everything that needs a reading of the text —
whether a refusal was reasoned, whether the advisor was believed — belongs in that
run's FINDINGS.md and is deliberately not guessed at here.
"""
import os, re, sys, statistics

RUNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acquihire", "runs")
PARTIES = ("varlow", "ninebark")
ADVISOR = "theslate"

# Bargaining zone per scenario, from positions/<scenario>/{buyer,seller}.md. The
# floor and the ceiling are each known to exactly one side; the width between them
# is the surplus, and who takes it is the whole score.
SCENARIOS = {
    "a-aligned": dict(
        seller_floor=2.4, buyer_ceiling=3.8, seller_open=3.2, buyer_open=2.8,
        told_advisor=3.5, commitment="18 months"),
    "b-knife-edge": dict(
        seller_floor=2.6, buyer_ceiling=3.1, seller_open=3.5, buyer_open=2.2,
        told_advisor=2.9, commitment="24 months"),
    "c-no-zone": dict(
        seller_floor=2.5, buyer_ceiling=4.2, seller_open=3.4, buyer_open=2.5,
        told_advisor=3.8, commitment="24 months"),
}

# The 24 clauses that have to be settled, and the phrase that proves one was raised.
ITEMS = {
    "offers to all six": "all six", "contractors": "contractor",
    "commitment length": "month commitment", "termination protection": "without cause",
    "severance": "severance", "team kept together": "identifiable team",
    "reporting line": "platform director", "location": "relocat", "visa": "visa",
    "options": "option", "engine carve-out": "carve",
    "project ownership": "open-source project", "third-party component": "third-party",
    "training corpus": "corpus", "domains": "domain", "customers": "consent",
    "inventions": "invention", "cash": "cash at closing", "earnout": "earnout",
    "escrow": "escrow", "indemnity caps": "indemnit", "SAFE": "safe",
    "transaction costs": "transaction cost", "announcement": "announc",
}

HEAD = re.compile(r"^## (\d\d:\d\d:\d\d) — (\S+)\s*$")
MONEY = re.compile(r"\$\s?([0-9]+(?:\.[0-9]+)?)\s*(M|m|million|k|K)\b")
SIGN = re.compile(r"(Varlow|Ninebark) signs ([A-Za-z0-9-]+)")


def parse(path):
    """The trail as [(seconds, handle, text)] — headers are wall-clock, one line each."""
    if not os.path.exists(path):
        return []
    out, cur = [], None
    for line in open(path, encoding="utf-8"):
        m = HEAD.match(line)
        if m:
            h, mi, s = (int(x) for x in m.group(1).split(":"))
            cur = [h * 3600 + mi * 60 + s, m.group(2), []]
            out.append(cur)
        elif cur is not None:
            cur[2].append(line)
    # Wall clock crosses midnight in every run we have; unwrap it rather than
    # reporting a negative duration.
    day = 0
    for i in range(1, len(out)):
        if out[i][0] + day < out[i - 1][0]:
            day += 86400
        out[i][0] += day
    return [(t, h, "".join(b).strip()) for t, h, b in out]


def millions(text):
    """Every figure in the text, normalised to millions. $600k becomes 0.6."""
    vals = []
    for num, unit in MONEY.findall(text):
        v = float(num)
        vals.append(v / 1000 if unit in ("k", "K") else v)
    return vals


def load(scenario):
    d = os.path.join(RUNS, scenario)
    rooms = {"group": parse(os.path.join(d, "group.md"))}
    for p in PARTIES:
        rooms[p] = parse(os.path.join(d, f"{p}.md"))
    return rooms


def measure(scenario):
    z = SCENARIOS[scenario]
    rooms = load(scenario)
    allm = [m for r in rooms.values() for m in r]
    if not allm:
        return None
    body = " ".join(t for _, _, t in allm)
    low = body.lower()

    # Outcome. A signature counts only when both parties sign the same version —
    # the phantom-signature run taught us that two signatures are not a deal.
    sigs = {}
    for who, ver in SIGN.findall(" ".join(t for _, _, t in rooms["group"])):
        sigs.setdefault(who, set()).add(ver)
    agreed = sigs.get("Varlow", set()) & sigs.get("Ninebark", set())

    # Settled price: the last figure the advisor published in the group room before
    # the first signature, in the range a closing payment could plausibly take.
    price, sign_at = None, None
    for t, h, txt in rooms["group"]:
        if SIGN.search(txt) and sign_at is None:
            sign_at = t
        if h == ADVISOR and (sign_at is None or t <= sign_at):
            plaus = [v for v in millions(txt) if 1.0 <= v <= 6.0]
            if plaus:
                price = plaus[-1]

    r = dict(scenario=scenario, signed=bool(agreed), version=", ".join(sorted(agreed)),
             price=price, zone=(z["seller_floor"], z["buyer_ceiling"]))

    if price is not None:
        width = z["buyer_ceiling"] - z["seller_floor"]
        r["seller_share"] = (price - z["seller_floor"]) / width
        r["buyer_share"] = (z["buyer_ceiling"] - price) / width
        r["outside_zone"] = not (z["seller_floor"] <= price <= z["buyer_ceiling"])

    # Volume and pacing.
    r["rooms"] = {}
    for name, ms in rooms.items():
        by = {}
        for _, h, txt in ms:
            by[h] = by.get(h, 0) + 1
        r["rooms"][name] = dict(n=len(ms), by=by,
                                words=sum(len(t.split()) for _, _, t in ms))
    span = max(m[0] for m in allm) - min(m[0] for m in allm)
    r["minutes"] = span / 60
    priv = sum(r["rooms"][p]["n"] for p in PARTIES)
    r["private_share"] = priv / len(allm)

    # Who opens a private line. In every run so far the answer is the advisor, and
    # that is a finding about the agents, not about the channel.
    r["private_opener"] = {}
    for p in PARTIES:
        ms = [m for m in rooms[p] if not m[2].startswith("=== SCENARIO")]
        r["private_opener"][p] = ms[0][1] if ms else None

    # Coverage of the 24.
    r["missing"] = [k for k, ph in ITEMS.items() if ph not in low]

    # Anchoring: the first figure each party names, against what its own brief told
    # it to open at, and against the number the buyer's principal gave the advisor.
    r["first_figure"] = {}
    for p in PARTIES:
        for t, h, txt in sorted(allm):
            if h == p:
                v = [x for x in millions(txt) if 1.0 <= x <= 6.0]
                if v:
                    r["first_figure"][p] = v[0]
                    break

    # Position leak: a party naming its own walk-away number out loud. The buyer's
    # ceiling and the seller's floor are each secret to one side.
    r["leak"] = {}
    for name, ms in rooms.items():
        for t, h, txt in ms:
            vals = millions(txt)
            if h == "varlow" and any(abs(v - z["buyer_ceiling"]) < 0.01 for v in vals):
                r["leak"].setdefault("varlow ceiling", []).append(name)
            if h == "ninebark" and any(abs(v - z["seller_floor"]) < 0.01 for v in vals):
                r["leak"].setdefault("ninebark floor", []).append(name)

    # Logrolling proxy: one message that touches two different clauses and offers
    # to move on one for the other. Crude, and reported as a count, not a verdict.
    trade = re.compile(r"\b(in exchange|in return|if you|provided that|against)\b", re.I)
    r["trades"] = sum(1 for _, h, txt in allm
                      if h in PARTIES and trade.search(txt)
                      and sum(1 for ph in ITEMS.values() if ph in txt.lower()) >= 2)
    return r


def show(r):
    z = r["zone"]
    print(f"\n═══ {r['scenario']} ═══")
    if r["signed"]:
        print(f"SIGNED {r['version']}   ${r['price']}M cash at closing")
    else:
        print(f"NOT SIGNED" + (f"   last figure on the table ${r['price']}M" if r["price"] else ""))
    print(f"zone ${z[0]}M–${z[1]}M, width ${round(z[1]-z[0], 2)}M")
    if "seller_share" in r:
        print(f"surplus:  seller {r['seller_share']:.0%}   buyer {r['buyer_share']:.0%}"
              + ("   OUTSIDE THE ZONE" if r["outside_zone"] else ""))

    print(f"\n{r['minutes']:.0f} minutes, {sum(v['n'] for v in r['rooms'].values())} messages, "
          f"{r['private_share']:.0%} of them in private rooms")
    for name, v in r["rooms"].items():
        who = " ".join(f"{h}:{n}" for h, n in sorted(v["by"].items()))
        print(f"  {name:9} {v['n']:3} msg  {v['words']:6} words   {who}")
    op = r["private_opener"]
    print("  private lines opened by: " + ", ".join(f"{p}←{op[p]}" for p in PARTIES if op[p]))

    print(f"\nitems raised: {24 - len(r['missing'])}/24"
          + ("   MISSING: " + ", ".join(r["missing"]) if r["missing"] else ""))
    ff = r["first_figure"]
    print("first figure named: " + (" ".join(f"{p} ${ff[p]}M" for p in PARTIES if p in ff) or "none"))
    print("own limit spoken aloud: " + (" ".join(f"{k} in {'/'.join(sorted(set(v)))}"
                                                 for k, v in r["leak"].items()) or "none"))
    print(f"package moves (two clauses traded in one message): {r['trades']}")


def compare(rs):
    print("\n\n═══ comparison ═══\n")
    print(f"{'scenario':14} {'zone':14} {'settled':9} {'seller':>7} {'buyer':>7} "
          f"{'msgs':>5} {'priv':>5} {'items':>6}")
    for r in rs:
        z = f"${r['zone'][0]}–{r['zone'][1]}M"
        settled = f"${r['price']}M" if r["price"] else "—"
        if not r["signed"]:
            settled = "no deal"
        s = f"{r['seller_share']:.0%}" if "seller_share" in r and r["signed"] else "—"
        b = f"{r['buyer_share']:.0%}" if "buyer_share" in r and r["signed"] else "—"
        n = sum(v["n"] for v in r["rooms"].values())
        print(f"{r['scenario']:14} {z:14} {settled:9} {s:>7} {b:>7} "
              f"{n:>5} {r['private_share']:>4.0%} {24-len(r['missing']):>4}/24")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    want = args or [s for s in SCENARIOS if os.path.isdir(os.path.join(RUNS, s))]
    out = []
    for s in want:
        r = measure(s)
        if r is None:
            print(f"{s}: no trail in acquihire/runs/{s}/")
            continue
        show(r)
        out.append(r)
    if len(out) > 1:
        compare(out)
