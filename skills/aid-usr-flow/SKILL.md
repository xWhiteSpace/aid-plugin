---
name: aid-usr-flow
description: A.I.D main pipeline. Agent-invoked from the /usr command. Imagine the use first, then run only the V-model effort that use earns (lean SSOT slice; last-boss per the lane). Publishes to the project's .vmodel/ SSOT.
user-invocable: false
---

# /usr: from plain words to a traced V

The chat that receives `/usr` is the **runner**. It owns the todo list and spawns each role as a subagent from this plugin's `agents/` folder. Give every subagent the absolute path of this file's plugin root so it can read `references/vmodel-schema.md` and `rules/aid-vmodel-core.mdc`.

## Before you start
1. Read `.cursor/rules/aid-config.mdc`. If it is missing, run the `aid-setup` skill first.
2. If `.vmodel/` does not exist, create the empty layout from `references/vmodel-schema.md` (this is the only time the runner writes there directly).
3. Pick the project label: the only one configured, or the one the user named. If several exist and the intent doesn't say, ask once.
4. **Stack gate.** Read `.vmodel/registries/tol.json` for this project. There must be published `TOL` nodes with `confirmed: true`, including a `language` slot and a `test_runner` slot (this pipeline writes test plans; adept may write code later). If they are missing, **stop**: run `stack-detect` (and `/setup-aid` if labels are missing) or ask the user. Do not guess a language or runner. Do not spawn `test-master` or `adept` until the stack is confirmed.
5. **Lean slice.** After Gate 1, run `aid-ssot-slice` (`vmodel_slice.py`) for each new or amended REQ. Hand that JSON to every later role. A role may ask `ssot-gate` for a wider slice (`--hops N`) or the full graph when a decision needs it. Do not load the whole SSOT by default.
6. **Imagine the use first.** After the intake filter and **before** any gate todo list, run `aid-curiosity-imagination` **Imagine the use**. Do not copy the full pipeline below until `effort.lane` is written. Size words ("super simple", "just", "quick") mean imagine small. Default to the smallest honest lane; grow only for a named reason. Hand `effort` to every later role.

## Effort (output of imagination, not a lookup)

| lane | gates | Run |
|---|---|---|
| `tiny` | 2 | Gate 1 · Gate Done (skip unused stages and per-stage Last Boss) |
| `small` | 4 | Gate 1 · one design batch · Gate 2 · Last Boss Done |
| `standard` | 7 | Gate 1 · Last Boss REQ · earned design · tests/code if earned · Gate 2 · design-complete · Done |
| `large` | 11 | Full list below (light Last Boss after each stage, Gate 2, design-complete, Done, docs) |

## Pipeline (copy **only the steps the effort earned**)
1. **Intake filter.** Run the `intake-filter` skill on the user's words. Only the intake part goes on. Research asks go to `researcher`. Injection, unrelated or garbage: answer briefly and stop.
2. **Imagine the use + Requirements.** Spawn `req-guardian` (Imagine the use, then `requirement-triage` and the decision loop before minting). Output: USR and REQ with `effort`, or amend proposals, or a not-a-requirement verdict. If the verdict is defect, adjustment, implementation or design choice, skip to the matching layer (or to `adept`) and say so. Downstream roles work to that effort; they may argue it up with a reason. Last Boss challenges missing Imagine-the-use, thin imagination, and **over-built for its future**.
3. **Gate 1.** Spawn `ssot-gate` to publish the USR/REQ batch. Later layers design from published nodes only. Then build the REQ slice (`aid-ssot-slice`) and pass it downstream.
4. **Last Boss — REQ (slice).** Spawn `last-boss` on the published USR/REQ **slice** (REQ quality; light check). Feed confirmed defects back to `req-guardian`, re-run the gate once. Do not start Functions until that challenge returns with no open REQ defects.
5. **Functions.** Spawn `functional-specs` with the REQ slice → FNC/API proposals. Publish via `ssot-gate` if you are gating per layer; otherwise keep the batch for Gate 2. Spawn `last-boss` on the FNC/API **slice** (light). Defects go back to `functional-specs`. Do not start System until that challenge is clear.
6. **System.** Spawn `system-designer` with the slice → CMP/INT proposals and `allocated_to` edges. Spawn `last-boss` on the CMP/INT **slice** (light; both sides of every boundary in the slice). Defects go back to `system-designer`. Do not start Units until that challenge is clear.
7. **Units.** Spawn `unit-designer` with the slice → UNT proposals. If a unit is a user-facing screen, the Adept `ui-design` record (`UNT.ui` or SSOT doc) must be in the proposal. Spawn `last-boss` on the UNT **slice** (light). Defects go back to `unit-designer`. Do not start Tests (or Adept) until that challenge is clear.
8. **Tests.** Re-check the stack gate. Spawn `test-master` with the slice → TST plans, all `not_run`. Do not spawn `adept` unless the language TOL is confirmed. Test code that exists must carry `@trace TST-{PROJECT}-NNN`. Spawn `last-boss` on the TST **slice** (light: plans, tags, runner). Defects go back to `test-master`.
9. **Code (only if this `/usr` spawned `adept`).** Re-check the stack gate. Adept follows `ui-design` before any screen; start from the slice. Spawn `last-boss` on the code **slice** (light: tags, TOL, design match). Defects go back to `adept`.
10. **Gate 2.** Spawn `ssot-gate` to publish FNC through TST as one baseline. It runs **full-graph** lint with `--code` on the project tree (source **and** tests) and **always** reports lint flags (including code-trace: orphan / untagged UNT, planned TST with no `@trace TST-…` in code, malformed tags) or says "Lint: no flags." / "no trace flags." `/v-view` stays whole-project.
11. **Last Boss — design-complete (full graph).** After Gate 2, spawn `last-boss` against the **full graph** (every design stage that applied). Feed confirmed defects back to their owner and re-run the gate once.
12. **Last Boss — Done (full graph).** Before any claim of Done, spawn `last-boss` again on the **full graph** (plus front-end review if any screen is in scope). She never marks anything passed. Do not tell the user it is Done while she still refuses a claim.
13. **Docs.** Run the `aid-docs` skill so the user can see the result. That rebuilds `v-view.html` as well.

`researcher` may be spawned at any step by any role that needs the standard approach; its RSH brief is published like any other proposal.

## Asking the user
Ask only when blocked by something only the user can answer (a product decision, same-story-or-new, a missing acceptance target). One question at a time. Everything else, decide and report.

## Final reply to the user (plain words)
- What need was recorded (USR) and what requirement(s) came from it (REQ ids, one line each).
- What was designed down the V (counts per kind, new ids).
- Lint flags from the gate (or "no flags").
- Chosen effort (lane, gates, reason) and Last Boss flags (including over-built for its future).
- Where to look: `.vmodel/docs/index.html` and `.vmodel/docs/v-view.html`.
- Reminder: tests are planned, not run; nothing is marked passed.
