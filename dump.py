"""Save a run's rooms as the markdown trail report.py reads.

    ROOMS=/tmp/rooms-divorce.json python3 dump.py divorce/runs/a-aligned "scenario A (aligned)"

Reads the channels table directly, as status.py does, so it works after the agents are
gone and does not depend on any account still being a participant. One file per room,
each message under a `## HH:MM:SS — handle` heading, sliced from the last scenario marker.
"""
import datetime, json, os, pathlib, subprocess, sys

rooms = json.load(open(os.environ.get("ROOMS", "/tmp/rooms.json")))
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
title = sys.argv[2] if len(sys.argv) > 2 else ""
v = lambda i, k: list(i[k].values())[0] if k in i else ""


def read(cid):
    raw = subprocess.run(["aws", "dynamodb", "query", "--table-name", "idntty-channels",
        "--region", "us-east-1", "--key-condition-expression", "pk = :p",
        "--expression-attribute-values", json.dumps({":p": {"S": f"CH#{cid}"}}),
        "--output", "json"], capture_output=True, text=True).stdout
    ms = sorted([i for i in json.loads(raw)["Items"] if v(i, "sk").startswith("MSG#")],
                key=lambda x: v(x, "sk"))
    cut = max((n for n, m in enumerate(ms)
               if v(m, "text").lstrip().startswith("=== SCENARIO")), default=0)
    return ms[cut:]


for label, cid in rooms.items():
    ms = read(cid)
    lines = [f"# {label} — {title}".rstrip(" —"), ""]
    for m in ms:
        ts = int(v(m, "sk").split("#")[1][:13]) / 1000
        when = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        who = v(m, "senderHandle") or v(m, "handle") or "?"
        lines += [f"## {when} — {who}", "", v(m, "text").strip(), ""]
    (out / f"{label}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{label:8} {len(ms):3} messages → {out / (label + '.md')}")
