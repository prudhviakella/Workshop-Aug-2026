#!/usr/bin/env python3
"""
LEVEL 0.5 — The three message types.

Not a build. There is no failure to fix here and nothing new the agent can
do afterwards. This exists because the message list is the object every
level after this one manipulates, and it is much easier to reason about
once you have watched it print.

    export ANTHROPIC_API_KEY=sk-...
    python stages/00_messages.py

Runs three turns of an ordinary conversation and prints the exact list
sent to the model each time. Watch the list grow.

The one thing worth noticing: on turn 3, turns 1 and 2 are sent again, in
full. The model did not remember them — your code re-sent them. That is
the whole of what "conversation memory" is at this layer.
"""

import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

MODEL = "claude-sonnet-4-6"

SYSTEM = (
    "You are a concise assistant for an e-commerce team. "
    "Answer in one short sentence. Never invent numbers."
)

TURNS = [
    "What does 'on-time delivery rate' usually mean?",
    "Why might that number be misleading?",
    "What was the first thing I asked you?",
]


def show(messages, turn):
    """Print the message list exactly as it will be sent."""
    print(f"\n{'=' * 70}")
    print(f"TURN {turn} — sending {len(messages)} messages")
    print("=" * 70)
    for m in messages:
        role = type(m).__name__.replace("Message", "").upper()
        text = m.content if isinstance(m.content, str) else str(m.content)
        if len(text) > 90:
            text = text[:87] + "..."
        print(f"  [{role:<6}] {text}")


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")

    model = ChatAnthropic(model=MODEL, max_tokens=300)

    # The system message is created ONCE and never changes. It gets sent
    # again on every single call — it is not "remembered" from before.
    messages = [SystemMessage(content=SYSTEM)]

    for i, question in enumerate(TURNS, start=1):
        messages.append(HumanMessage(content=question))
        show(messages, i)

        reply = model.invoke(messages)
        print(f"\n  -> model replied: {reply.content.strip()[:120]}")

        # The reply must be appended by YOUR code. If you skip this line,
        # the model has no idea what it said a moment ago.
        messages.append(AIMessage(content=reply.content))

    print(f"\n{'=' * 70}")
    print(f"Final list: {len(messages)} messages")
    print("=" * 70)
    print("""
Turn 3 answered a question about turn 1 — but not from memory. Turn 1 was
physically in the list that got sent. Delete that line where the AI reply
is appended, run it again, and watch the model lose the thread completely.

Three roles, one job each:
  SYSTEM  who it is, and the rules. Written once, sent every time.
  HUMAN   what you asked.
  AI      what it said back.

There is a fourth role for tool results. It does not exist yet, because
there are no tools yet. That is Level 2.
""")


if __name__ == "__main__":
    main()
