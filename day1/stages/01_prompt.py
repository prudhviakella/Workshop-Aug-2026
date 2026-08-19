#!/usr/bin/env python3
"""
LEVEL 1 — PROMPT.

One model call. Two different system messages. Same question both times.

    export ANTHROPIC_API_KEY=sk-...
    python stages/01_prompt.py

What this level fixes: the model answers, but not in a shape anyone can
use. A vague instruction gives a vague answer — a friendly paragraph with
no number, no denominator, and nothing a program could parse.

What this level does NOT fix, and be honest about it on stage: BOTH
answers here are invented. The model still has no access to the database.
It has never seen a single row. All we are changing is the SHAPE of the
answer, not its truth.

That is deliberate. Truth is Level 2's problem (give it tools) and Level 3's
problem (give it the schema). If you fix everything at once, nobody learns
which fix did what.
"""

import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

MODEL = "claude-sonnet-4-6"

QUESTION = "What is our on-time delivery rate?"

# ── Version A ────────────────────────────────────────────────────────────
# What most people write the first time. Not wrong, just unspecific.
VAGUE = "You are a helpful assistant."

# ── Version B ────────────────────────────────────────────────────────────
# The same request, with the four things that were missing:
#   who it is, what the task is, the exact output shape, and permission
#   to admit it does not know.
STRUCTURED = """You are a data analyst for an e-commerce marketplace.

Your job is to answer questions about delivery, orders and revenue with
numbers a manager can act on.

Answer in exactly this shape:

  FIGURE:      the number, with its unit
  DENOMINATOR: what it is a percentage OF, stated explicitly
  SOURCE:      where the number came from
  CAVEAT:      anything that would make it misleading

If you do not have access to the data needed, write UNKNOWN in FIGURE and
say plainly what you would need. Do not estimate. Do not guess a plausible
number — a wrong number that looks right is worse than no number."""


def ask(system: str, label: str):
    model = ChatAnthropic(model=MODEL, max_tokens=400)
    reply = model.invoke([
        SystemMessage(content=system),
        HumanMessage(content=QUESTION),
    ])
    print(f"\n{'=' * 68}")
    print(label)
    print("=" * 68)
    print(f"\nSYSTEM MESSAGE:\n{system.strip()[:300]}"
          + ("..." if len(system) > 300 else ""))
    print(f"\nQUESTION:  {QUESTION}")
    print(f"\nANSWER:\n{reply.content.strip()}")
    return reply.content


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")

    ask(VAGUE, "VERSION A  —  vague instruction")
    ask(STRUCTURED, "VERSION B  —  structured instruction")

    print(f"\n{'=' * 68}")
    print("""
Same model. Same question. The only thing that changed is the system
message.

Version A gives you prose. Version B gives you a shape you could parse,
log, or put in a dashboard — and a slot for the model to admit it does
not know.

But look closely at BOTH answers. Neither one is true. The model has
never seen your database. If it produced a number at all, it invented it.

Version B is more likely to say UNKNOWN, because we gave it permission to.
That is the most valuable line in the whole prompt — and it is still not
a fix for the real problem.

Next: Level 2 gives it a way to actually look.
""")


if __name__ == "__main__":
    main()
