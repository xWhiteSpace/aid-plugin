---
name: aid-curiosity-imagination
description: Imagine the use at intake (person, moment, smallest honest future, done-enough, then effort lane). Then the short pre-decision loop every A.I.D agent runs before a choice. Agent-invoked; not a slash command.
user-invocable: false
---

# Curiosity → Imagination → Intelligence

Follow `aid-vmodel-core`. No new agent.

**Imagine the use** runs at **intake**, before any gate plan. Later choices still run Curiosity → Imagination → Intelligence. **Curiosity** asks. **Imagination** names possible futures. **Intelligence** picks the future most likely to be correct.

## Imagine the use (intake, before any gate)

`/usr` and `req-guardian` run this **before** minting or listing gates. Do not plan the V until this is written. Words like "super simple", "just", or "quick" mean imagine small — they are not flavour.

**(a) Person and moment.** Who is using it, where, for how long, how often. Picture that scene. Not a persona document; a few concrete lines.

**(b) Futures of use.** Picture **2–3** futures of this thing being used, including the **smallest honest** one. Label them as possibilities. No invented user quotes or numbers.

**(c) Done and good enough.** From the **user's** side: what they can do, see, or stop worrying about. Not "all V layers published".

**(d) Then effort.** Only now choose how many stages, gates, tests, and tools this job **earns**. Default to the **smallest honest** effort. Grow only for a named reason: risk, money, safety, many users, long life. Record the pick on the USR/REQ proposal (`decision` + `effort`).

Lanes are the **output words** of that judgement, not a keyword table. Pick the lane that matches the imagined use:

| lane | gates | What those gates are |
|---|---|---|
| `tiny` | **2** | Gate 1 (USR/REQ) · Gate Done (one publish of what the use earned + Last Boss once) |
| `small` | **4** | Gate 1 · one design batch · Gate 2 · Last Boss Done |
| `standard` | **7** | Gate 1 · Last Boss REQ · design the use earned · tests/code if earned · Gate 2 · Last Boss design-complete · Last Boss Done |
| `large` | **11** | Gate 1 · light Last Boss after REQ, FNC, CMP/INT, UNT, tests, code · Gate 2 · design-complete · Done · docs |

```text
effort:
  use: <who, where, how long, how often>
  done_enough: <from the user's side>
  futures: [<smallest honest>, ...]
  lane: tiny | small | standard | large
  gates: 2 | 4 | 7 | 11
  stages: [<only the V layers this use earned>]
  reason: <why this lane matches the use>
  grow_for: null | risk | money | safety | many_users | long_life
```

Later roles work to that effort. They may argue it **up** with a written reason. Last Boss flags **over-built for its future** when the run is heavier than the imagined use (alongside **reinvented wheel**). For a small imagined use, Adept uses `ui-design` and the **installed** TOL only — no tool/MCP hunt for elegance.

## (a) Curiosity

List what is unknown, ambiguous, or assumed. Ask only the questions that would **change the decision**. Look for edge cases and other stakeholder views (who uses it, who is harmed if it is wrong). If a question only the user can answer, return that one question (see core rule 10). Everything else, decide.

## (b) Imagination

Generate **2–4 concrete possible futures** (options). For each: what the world looks like if chosen, risks, and what would prove it wrong. Label them as **possibilities**. No made-up facts: if a number, file, or user quote is not in the SSOT or the intake, do not invent it.

## (c) Intelligence

Choose one option. Write: the pick, explicit reasons, the predicted outcome, and a **check** that can later confirm or refute the prediction. Put that block on the proposal (`decision`) so `ssot-gate` can copy it into the baseline.

```text
decision:
  question: <one line>
  options: [<id>, ...]          # 2–4 possibilities
  chosen: <id>
  reason: <why this is most likely correct>
  rejected: [{ id, why }]
  predicted: <what should be true if the pick is right>
  check: <observable later: test, review, or user fact>
```

Keep it short. One loop per decision, not a report.
