#!/usr/bin/env python3
"""
LEVEL 2 — AGENT + TOOLS.

The model still cannot reach your data. So we build the thing that can.

    export ANTHROPIC_API_KEY=sk-...
    python stages/02_agent_tools.py
    python stages/02_agent_tools.py "How many orders were cancelled?"

What this level fixes: Level 1 got the SHAPE right and the truth wrong.
Both answers were invented, because the model had never seen a row. Here
it gets a tool — and produces a number that came out of the database.

What this level does NOT fix: it still knows nothing about what the
columns MEAN. Ask it the on-time rate and watch what it does. That is
Level 3's problem, and it is the most expensive one in the whole course.

Read this file top to bottom — it is deliberately short. Everything the
word "agent" refers to is here: a tool, a loop, and the code that runs
what the model asks for.
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain.agents import create_agent

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "db" / "ecom.db"
MODEL = "claude-sonnet-4-6"


# ── THE TOOL ─────────────────────────────────────────────────────────────
# A plain Python function. The @tool decorator does one thing: it makes
# the function's NAME and DOCSTRING visible to the model, so the model can
# ask for it by name. The model never runs this. Your code does.

@tool
def run_query(sql: str) -> str:
    """Run a read-only SQL query against the marketplace database and
    return the rows. Use this for any question about orders, deliveries,
    revenue, customers or products."""

    # ── GUARDRAIL 1 — an INPUT check ─────────────────────────────────────
    # Inspects what the model asked for and refuses before anything runs.
    # Cheap, readable, and the one most people stop at.
    if not sql.strip().upper().startswith("SELECT"):
        return "REFUSED: only SELECT queries are allowed."

    # ── GUARDRAIL 2 — a removed CAPABILITY ───────────────────────────────
    # mode=ro opens the connection read-only at the SQLite level. This is
    # not a check that could be wrong — writing is simply not something
    # this connection can do.
    #
    # The distinction matters more than it looks:
    #   guardrail 1 is a rule, and rules only cover the cases you thought
    #   of. Guardrail 2 removes the ability entirely. If you only get one,
    #   take the second.
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        cur = con.execute(sql)
        rows = cur.fetchall()[:50]
        cols = [d[0] for d in cur.description]
    except sqlite3.Error as e:
        # ── GUARDRAIL 3 — an OUTPUT decision ─────────────────────────────
        # What leaves the tool is a choice too. This returns the error to
        # the MODEL rather than crashing the program, so the model can read
        # it, work out what it got wrong, and try again. That is why it is
        # phrased for a reader instead of a stack trace.
        return f"SQL error: {e}"
    finally:
        con.close()

    # ── AND WHAT NONE OF THEM CATCH ──────────────────────────────────────
    # Try this against the tool and watch it hang:
    #
    #     SELECT COUNT(*) FROM orders o1, orders o2
    #
    # It starts with SELECT, so guardrail 1 passes it. It writes nothing,
    # so guardrail 2 is irrelevant. It is valid SQL, so there is no error
    # for guardrail 3 to return. And it is a 2.5-billion-row cartesian
    # join that will sit there until something kills it.
    #
    # Every guardrail defends against a threat you named in advance. This
    # tool has no timeout and no row cap — both of which it needs. Day 2
    # is where guardrails get systematic.

    if not rows:
        return "0 rows."
    header = " | ".join(cols)
    body = "\n".join(" | ".join(str(v) for v in r) for r in rows)
    return f"{header}\n{body}"


# ── THE SYSTEM MESSAGE ───────────────────────────────────────────────────
# Carried over from Level 1, plus one line about the tool. Note what is
# still missing: nothing here explains what any column MEANS.

SYSTEM = """You are a data analyst for an e-commerce marketplace.

You have one tool: run_query, which runs SQL against the database.

The database has these tables: orders, order_items, products, customers,
shipments, payment_transactions, reviews, suppliers, warehouses,
inventory, promotions, categories, customer_addresses, product_suppliers.

Answer in exactly this shape:

  FIGURE:      the number, with its unit
  DENOMINATOR: what it is a percentage OF, stated explicitly
  SOURCE:      the SQL you ran
  CAVEAT:      anything that would make it misleading

If the data cannot answer the question, write UNKNOWN in FIGURE and say
what you would need. Never estimate."""


def main():
    ap = argparse.ArgumentParser(description="Level 2 — an agent with one tool")
    ap.add_argument("question", nargs="?",
                    default="What is our on-time delivery rate?")
    a = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    if not DB.exists():
        sys.exit(f"No database at {DB}")

    # ── THE AGENT ────────────────────────────────────────────────────────
    # This one call is the whole thing. create_agent wires the loop:
    # send the question and the tool list, read the reply, run any tool the
    # model asked for, feed the result back, repeat until it stops asking.
    agent = create_agent(
        model=ChatAnthropic(model=MODEL, max_tokens=1500),
        tools=[run_query],
        system_prompt=SYSTEM,
    )

    print(f"\nQUESTION:  {a.question}\n")
    result = agent.invoke({"messages": [{"role": "user", "content": a.question}]})

    # Walk the message list and show every turn — this is the loop, visible.
    for m in result["messages"]:
        kind = type(m).__name__
        if kind == "AIMessage" and getattr(m, "tool_calls", None):
            for call in m.tool_calls:
                print(f"  [ACT]      {call['name']}({str(call['args'])[:90]})")
        elif kind == "ToolMessage":
            first = str(m.content).split("\n")[0][:90]
            print(f"  [OBSERVE]  {first}")

    print(f"\nANSWER:\n{result['messages'][-1].content}\n")
    print("""Notice what just happened: nobody wrote the SQL. The model read the
question, decided it needed the database, wrote a query, and read the
result back. That decision is what the word "agent" refers to.

Now the harder question — is that number RIGHT? It came out of the
database, so it is real. But the model still has no idea what any of
these columns actually mean. That is Level 3.
""")


if __name__ == "__main__":
    main()
