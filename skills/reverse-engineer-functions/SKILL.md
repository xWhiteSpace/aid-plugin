---
name: reverse-engineer-functions
description: "Use when reverse-engineering: turn a code trace and published requirements into functions."
---
# Reverse engineer: functions

Use when requirements exist and a code trace shows the behavior. You write functions. You do not read the repo as your source.

## Inputs
- Published requirements for this slice.
- A code trace: symbols, writers, readers, and not-seen items.

## You do
1. One function per observable behavior, tied to the requirement that owns it.
2. State inputs, the rule, and the output in product language.
3. If the trace shows a computed value and a stored snapshot, they are two functions or one function plus a stated store. Do not merge them.
4. Name the trace symbols only as evidence of the rule, not as the specification.
5. Drop anything marked not seen.
6. Propose functions and their implements links to ssot-gate (write to `.vmodel/proposals/`). Do not publish.

## You do not
- Mint requirements.
- Place functions in components. That is system design.
- Specify field-level interfaces. That is unit design.
- Invent a behavior the trace does not show.
