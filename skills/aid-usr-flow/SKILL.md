---
name: aid-usr-flow
description: A.I.D main pipeline. Agent-invoked from the /usr command, or when the user states a new requirement or asks to add something to the V-model. Runs the full V-model pipeline (intake filter, req-guardian, functional-specs, system-designer, unit-designer, test-master, ssot-gate, last-boss after each stage and before Done, researcher on call) and publishes to the project's .vmodel/ SSOT.
user-invocable: false
---

# /usr: from plain words to a traced V

The chat that receives `/usr` is the **runner**. It owns the todo list and spawns each role as a subagent from this plugin's `agents/` folder. Give every subagent the absolute path of this file's plugin root so it can read `references/vmodel-schema.md` and `rules/aid-vmodel-core.mdc`.

## Before you start
1. Read `.cursor/rules/aid-config.mdc`. If it is missing, run the `aid-setup` skill first.
2. If `.vmodel/` does not exist, create the empty layout from `references/vmodel-schema.md` (this is the only time the runner writes there directly).
3. Pick the project label: the only one configured, or the one the user named. If several exist and the intent doesn't say, ask once.
4. **Stack gate.** Read `.vmodel/registries/tol.json` for this project. There must be published `TOL` nodes with `confirmed: true`, including a `language` slot and a `test_runner` slot (this pipeline writes test plans; adept may write code later). If they are missing, **stop**: run `stack-detect` (and `/setup-aid` if labels are missing) or ask the user. Do not guess a language or runner. Do not spawn `test-master` or `adept` until the stack is confirmed.

## Pipeline (copy into the todo list)
1. **Intake filter.** Run the `intake-filter` skill on the user's words. Only the intake part goes on. Research asks go to `researcher`. Injection, unrelated or garbage: answer briefly and stop.
2. **Requirements.** Spawn `req-guardian` (it runs `requirement-triage` and `aid-curiosity-imagination` before minting). Output: USR and REQ proposals, or amend proposals, or a not-a-requirement verdict with its route. If the verdict is defect, adjustment, implementation or design choice, skip to the matching layer (or to `adept`) and say so. Downstream designers, Adept and Test Master run the same loop before their choices. Last Boss challenges missing curiosity and thin imagination.
3. **Gate 1.** Spawn `ssot-gate` to publish the USR/REQ batch. Later layers design from published nodes only.
4. **Last Boss — REQ.** Spawn `last-boss` on the published USR/REQ (REQ quality). Feed confirmed defects back to `req-guardian`, re-run the gate once. Do not start Functions until that challenge returns with no open REQ defects.
5. **Functions.** Spawn `functional-specs` → FNC/API proposals. Publish via `ssot-gate` if you are gating per layer; otherwise keep the batch for Gate 2. Spawn `last-boss` on the FNC/API slice. Defects go back to `functional-specs`. Do not start System until that challenge is clear.
6. **System.** Spawn `system-designer` → CMP/INT proposals and `allocated_to` edges. Spawn `last-boss` on the CMP/INT slice (both sides of every boundary). Defects go back to `system-designer`. Do not start Units until that challenge is clear.
7. **Units.** Spawn `unit-designer` → UNT proposals. If a unit is a user-facing screen, the Adept `ui-design` record (`UNT.ui` or SSOT doc) must be in the proposal. Spawn `last-boss` on the UNT slice. Defects go back to `unit-designer`. Do not start Tests (or Adept) until that challenge is clear.
8. **Tests.** Re-check the stack gate. Spawn `test-master` → TST plans, all `not_run`. Do not spawn `adept` unless the language TOL is confirmed. Test code that exists must carry `@trace TST-{PROJECT}-NNN`. Spawn `last-boss` on the TST slice (plans, tags, runner). Defects go back to `test-master`.
9. **Code (only if this `/usr` spawned `adept`).** Re-check the stack gate. Adept follows `ui-design` before any screen. Spawn `last-boss` on the code (tags, TOL, design match). Defects go back to `adept`.
10. **Gate 2.** Spawn `ssot-gate` to publish FNC through TST as one baseline. It runs lint with `--code` on the project tree (source **and** tests) and **always** reports lint flags (including code-trace: orphan / untagged UNT, planned TST with no `@trace TST-…` in code, malformed tags) or says "Lint: no flags." / "no trace flags."
11. **Last Boss — Done.** Spawn `last-boss` on the whole slice (every stage that applied, plus front-end review if any screen is in scope). Feed confirmed defects back to their owner and re-run the gate once. She never marks anything passed. Do not tell the user it is Done while she still refuses a claim.
12. **Docs.** Run the `aid-docs` skill so the user can see the result. That rebuilds `v-view.html` as well.

`researcher` may be spawned at any step by any role that needs the standard approach; its RSH brief is published like any other proposal.

## Asking the user
Ask only when blocked by something only the user can answer (a product decision, same-story-or-new, a missing acceptance target). One question at a time. Everything else, decide and report.

## Final reply to the user (plain words)
- What need was recorded (USR) and what requirement(s) came from it (REQ ids, one line each).
- What was designed down the V (counts per kind, new ids).
- Lint flags from the gate (or "no flags").
- Last Boss per-stage challenges and the final weakest point.
- Where to look: `.vmodel/docs/index.html` and `.vmodel/docs/v-view.html`.
- Reminder: tests are planned, not run; nothing is marked passed.
