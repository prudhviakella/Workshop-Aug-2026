# Applied Generative AI — Day 1

Everything you need for Day 1. Three scripts, one database, no setup beyond
two `pip install`s.

By the end of today you will have an agent running on your own laptop that
answers real questions from a real database.

---

## Setup

Do this **before** the session if you can — it takes two minutes and saves
you missing the first demo.

```bash
pip install langchain langchain-anthropic
export ANTHROPIC_API_KEY=sk-...
```

Windows PowerShell uses `$env:ANTHROPIC_API_KEY="sk-..."` instead.

Check it works:

```bash
python stages/00_messages.py
```

If that prints three growing message lists, you are ready.

---

## What's here

```
db/ecom.db                  a real marketplace database — 15 tables,
                            320,000 rows, two years of orders
stages/00_messages.py       Level 0 — the three message types
stages/01_prompt.py         Level 1 — prompt
stages/02_agent_tools.py    Level 2 — agent + tools
```

Nothing is simulated. `ecom.db` is a genuine SQLite database sitting on your
disk — open it in any SQLite browser if you want to poke around.

---

## The three levels

Run them in order. Each one fixes something the previous one got wrong, and
the failures are the point — resist skipping ahead.

### Level 0 — `00_messages.py`

The three message types, and the fact that nothing is remembered between
calls. No agent yet, no tools.

Prints the real message list growing turn by turn: 2 → 4 → 6.

**Try this:** delete the line that appends the AI reply, run it again, and
watch the model lose the thread completely.

### Level 1 — `01_prompt.py`

One model call, two different system messages, same question.

```bash
python stages/01_prompt.py
```

**The failure:** a vague instruction gives a friendly paragraph — no number,
no denominator, nothing a program could use.

**The fix:** say who it is, what the task is, the exact output shape, and
give it permission to say UNKNOWN.

**What is still broken:** *both* answers are invented. The model has never
seen a row of your data. Level 1 fixes the shape of an answer, not its
truth.

### Level 2 — `02_agent_tools.py`

The same question, but now the model can reach the database.

```bash
python stages/02_agent_tools.py
python stages/02_agent_tools.py "How many orders were cancelled?"
```

**The fix:** one `@tool` function, and `create_agent` to wire the loop —
send the question and the tool list, read the reply, run whatever the model
asked for, feed the result back, repeat.

It prints every ACT and OBSERVE, so you can watch the loop rather than take
it on faith.

Read the file top to bottom. It is deliberately short — everything the word
"agent" refers to is in there: a tool, a loop, and the code that runs what
the model asks for.

---

## Three guardrails worth noticing in Level 2

They are three different kinds of thing, and the difference matters:

| | What it is | Can it be wrong? |
|---|---|---|
| `startswith("SELECT")` | an **input** check — inspects the request | yes, it is a rule |
| `mode=ro` | a removed **capability** — the connection cannot write | no |
| `return f"SQL error: {e}"` | an **output** decision — errors go back to the model, not to a crash | — |

Type `DROP TABLE orders` at it and watch it refuse. Then notice that even if
that check had a hole, `mode=ro` would still hold.

**A rule only covers the cases you thought of. A missing capability covers
all of them.**

---

## Where this goes tomorrow

By the end of Day 1 your agent works — and is still missing everything that
would make it trustworthy:

- it does not know what your columns actually **mean**
- it cannot recover when a step fails
- nothing forces it to check its own work
- nothing records what it did
- nobody can say how often it is right

Each of those is a level on Day 2.

One of the answers it gives you today is wrong. Tomorrow we find out which.
