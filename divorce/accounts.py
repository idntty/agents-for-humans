"""Provision the two parties on the live platform — same path as the acquisition pair."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from setup_accounts import provision

PARTIES = [
    ("hale", "hello+hale@idntty.io",
     "Ren Hale's side in a divorce settlement. A fictional person in a public "
     "demonstration of two identical agents, each holding one party's position, "
     "reaching a settlement through a neutral mediator over a channel neither owns."),
    ("marren", "hello+marren@idntty.io",
     "Dana Marren's side in a divorce settlement. A fictional person in a public "
     "demonstration of two identical agents, each holding one party's position, "
     "reaching a settlement through a neutral mediator over a channel neither owns."),
]

if __name__ == "__main__":
    for slug, email, desc in PARTIES:
        provision(slug, email, desc)
        print()
