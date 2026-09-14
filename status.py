"""Where the negotiation stands. One shot: rooms, coverage, numbers, signatures."""
import json, subprocess, datetime, sys, re, os

rooms = json.load(open(os.environ.get("ROOMS", "/tmp/rooms.json")))
v = lambda i, k: list(i[k].values())[0] if k in i else ""

def read(cid):
    out = subprocess.run(["aws","dynamodb","query","--table-name","idntty-channels",
        "--region","us-east-1","--key-condition-expression","pk = :p",
        "--expression-attribute-values", json.dumps({":p":{"S":f"CH#{cid}"}}),
        "--output","json"], capture_output=True, text=True).stdout
    ms = sorted([i for i in json.loads(out)["Items"] if v(i,"sk").startswith("MSG#")],
                key=lambda x: v(x,"sk"))
    cut = max((n for n,m in enumerate(ms) if v(m,"text").lstrip().startswith("=== SCENARIO")),
              default=0)
    return ms[cut:]

alive = subprocess.run("ps aux | grep -c '[a]gent.py'", shell=True,
                       capture_output=True, text=True).stdout.strip()
print(f"agents alive: {alive}")

allm = []
for label, cid in rooms.items():
    ms = read(cid); allm += ms
    by = {}
    for i in ms:
        h = v(i,"senderHandle") or v(i,"handle"); by[h] = by.get(h,0)+1
    last = ms[-1] if ms else None
    when = datetime.datetime.fromtimestamp(int(v(last,'sk').split('#')[1][:13])/1000).strftime('%H:%M:%S') if last else '—'
    who = (v(last,'senderHandle') or v(last,'handle')) if last else '—'
    print(f"{label:9} {len(ms):3}  last {when} {who:10} {by}")
print(f"{'TOTAL':9} {len(allm):3}")

body = " ".join(v(i,"text") for i in allm)
low = body.lower()
ITEMS = {"offers to all six":"all six", "contractors":"contractor", "commitment length":"month commitment",
 "termination protection":"without cause", "severance":"severance", "team kept together":"identifiable team",
 "reporting line":"platform director", "location":"relocat", "visa":"visa", "options":"option",
 "engine carve-out":"carve", "project ownership":"open-source project", "third-party component":"third-party",
 "training corpus":"corpus", "domains":"domain", "customers":"consent", "inventions":"invention",
 "cash":"cash at closing", "earnout":"earnout", "escrow":"escrow", "indemnity caps":"indemnit",
 "SAFE":"safe", "transaction costs":"transaction cost", "announcement":"announc"}
miss = [k for k,p in ITEMS.items() if p not in low]
print(f"\nitems raised: {len(ITEMS)-len(miss)}/24" + ("   MISSING: " + ", ".join(miss) if miss else ""))
print("figures:", " ".join(sorted(set(re.findall(r'\$[0-9.]+\s*(?:million|M|m|k|K)\b', body)))) or "none")
sigs = re.findall(r'(?:Varlow|Ninebark) signs [A-Za-z0-9-]+', body)
print("signatures:", " | ".join(sorted(set(s for s in sigs if '"' not in s))) or "none")

if "-v" in sys.argv:
    for label, cid in rooms.items():
        ms = read(cid)
        if not ms: continue
        print(f"\n═══ {label} ═══")
        for i in ms[-2:]:
            print(f"— {v(i,'senderHandle') or v(i,'handle')}: {v(i,'text')[:600]}\n")
