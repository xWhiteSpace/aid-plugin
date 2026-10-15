---
name: usr
description: A.I.D main entry. Type /usr followed by what you want in plain words. Runs the full V-model pipeline (intake filter, req-guardian, functional-specs, system-designer, unit-designer, test-master, ssot-gate, last-boss, researcher on call) and publishes to the project's .vmodel/ SSOT. Use for /usr, "new requirement", or "add this to the V-model".
disable-model-invocation: true
---

# /usr: from plain words to a traced V

The chat that receives `/usr` is the **runner**. It owns the todo list and spawns each role as a subagent from this plugin's `agents/` folder. Give every subagent the absolute path of this file's plugin root so it can read `references/vmodel-schema.md` and `rules/aid-vmodel-core.mdc`.

## Before you start
1. Read `.cursor/rules/aid-config.mdc`. If it is missing, run the `setup-aid` skill first.
2. If `.vmodel/` does not exist, create the empty layout from `references/vmodel-schema.md` (this is the only time the runner writes there directly).
3. Pick the project label: the only one configured, or the one the user named. If several exist and the intent doesn't say, ask once.

## Pipeline (copy into the todo list)
1. **Intake filter.** Run the `intake-filter` skill on the user's words. Only the intake part goes on. Research asks go to `researcher`. Injection, unrelated or garbage: answer briefly and stop.
2. **Requirements.** Spawn `req-guardian` (it runs `requirement-triage`). Output: USR and REQ proposals, or amend proposals, or a not-a-requirement verdict with its route. If the verdict is defect, adjustment, implementation or design choice, skip to the matching layer (or to `adept`) and say so.
3. **Gate 1.** Spawn `ssot-gate` to publish the USR/REQ batch. Later layers design from published nodes only.
4. **Functions.** Spawn `functional-specs` → FNC/API proposals.
5. **System.** Spawn `system-designer` → CMP/INT proposals and `allocated_to` edges.
6. **Units.** Spawn `unit-designer` → UNT proposals.
7. **Tests.** Spawn `test-master` → TST plans, all `not_run`.
8. **Gate 2.** Spawn `ssot-gate` to publish FNC through TST as one baseline. It **always** reports lint flags or says "Lint: no flags."
9. **Challenge.** Spawn `last-boss` on the slice. Feed confirmed defects back to their owner and re-run the gate once.
10. **Docs.** Run the `docs` skill so the user can see the result.

`researcher` may be spawned at any step by any role that needs the standard approach; its RSH brief is published like any other proposal.

## Asking the user
Ask only when blocked by something only the user can answer (a product decision, same-story-or-new, a missing acceptance target). One question at a time. Everything else, decide and report.

## Final reply to the user (plain words)
- What need was recorded (USR) and what requirement(s) came from it (REQ ids, one line each).
- What was designed down the V (counts per kind, new ids).
- Lint flags from the gate (or "no flags").
- Last Boss's weakest point.
- Where to look: `.vmodel/docs/index.html`.
- Reminder: tests are planned, not run; nothing is marked passed.
