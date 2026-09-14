"""Provision the two negotiating agents on the live platform.

Same path the test contour uses: plant a magic row, go through /auth/verify, claim the
name, issue the agent key. Nothing here is admin-only — it is the ordinary signup, minus
SES delivery, which is the only part these mailboxes cannot do (idntty.io has no MX).

That is also why the key goes straight into SSM: lose it and the account is
unrecoverable, because no one can receive the magic link.
"""
from __future__ import annotations

import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))

import boto3
from client import call, signin, db_user

AGENTS = [
    ("varlow", "hello+varlow@idntty.io",
     "Varlow Systems, the buyer in an acqui-hire negotiation. A fictional company in a "
     "public demonstration of two agents bargaining across a channel neither of them "
     "owns, with a human advisor between them."),
    ("ninebark", "hello+ninebark@idntty.io",
     "Ninebark Labs, the seller in an acqui-hire negotiation. A fictional company in a "
     "public demonstration of two agents bargaining across a channel neither of them "
     "owns, with a human advisor between them."),
]

ssm = boto3.client("ssm", region_name="us-east-1")


def provision(slug: str, email: str, description: str) -> None:
    jwt, uid = signin(email)
    print(f"{slug}: signed in as {uid}")

    r = call("POST", "/auth/slug", token=jwt, slug=slug)
    if r.status not in (200, 201):
        print(f"  slug -> {r.status} {r.body}")
        if "taken" not in json.dumps(r.body).lower():
            raise SystemExit(f"cannot claim {slug}")
    else:
        print(f"  name claimed: idntty.io/{slug}")

    r = call("PATCH", "/me", token=jwt, description=description)
    print(f"  description -> {r.status}")

    r = call("POST", "/auth/token", token=jwt, label=f"{slug} agent")
    if r.status != 201:
        raise SystemExit(f"no key for {slug}: {r}")
    key = r.body["key"]
    print(f"  key issued: {key[:14]}… ({len(key)} chars)")

    ssm.put_parameter(Name=f"/{slug}/agent-key", Value=key, Type="SecureString",
                      Overwrite=True)
    print(f"  stored at /{slug}/agent-key")

    u = db_user(uid) or {}
    print(f"  account: name={u.get('agentName')} email={u.get('email')}")


if __name__ == "__main__":
    for slug, email, desc in AGENTS:
        provision(slug, email, desc)
        print()
