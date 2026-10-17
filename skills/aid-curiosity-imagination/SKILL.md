---
name: aid-curiosity-imagination
description: Short pre-decision loop every A.I.D agent runs before a choice. Curiosity lists unknowns and asks questions that would change the decision. Imagination names 2–4 possible futures (labelled as possibilities). Intelligence picks the future most likely to be correct, with a reason and a later check. Agent-invoked; not a slash command.
user-invocable: false
---

# Curiosity → Imagination → Intelligence

Run this loop **before a decision** (mint, amend, allocate, design, test shape, UI, or "skip"). Not on every token; on each choice that would change the SSOT or the product. Follow `aid-vmodel-core`. No new agent.

**Curiosity** asks and shows interest. **Imagination** takes a question into possible futures. **Intelligence** chooses the future most likely to be correct (one answer in a multiple-choice set).

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