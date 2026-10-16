---
name: setup-aid
description: Configure A.I.D for this project. Sets project labels, isolation, per-role models, and a confirmed tool stack (never guessed). Writes .cursor/rules/aid-config.mdc, bootstraps .vmodel/, and publishes TOL entries via tools-manager + ssot-gate. Use for /setup-aid, "configure aid", or adding a new project label.
disable-model-invocation: true
---

# /setup-aid

Write `.cursor/rules/aid-config.mdc` in the project repo: an always-applied rule every A.I.D skill and subagent reads. Confirm the **tool stack** so later roles never guess a language or runner.

## 1. Project labels
Ask for one or more short labels (2 to 5 uppercase letters or digits, e.g. `ACME`). Each label is its own id space: `USR-ACME-001`. If a rule file exists, show its labels and ask what to add or retire. Never rename a label that already has published ids.

## 2. Isolation
Each label is isolated: no edge may join two labels, and a counterpart id from another label may appear only as plain text. Record, per label, a one-line scope brief (product, users) that the intake filter uses.

## 3. Models per role
Enumerate the model slugs you can pass to a `Task` subagent in this session. Never write a slug you have not confirmed is available. `inherit-parent` (the role runs on the parent chat model) is always valid. Defaults:

| Role | Default |
|---|---|
| adept (code delegate) | `grok-4.6` with fast on |
| req-guardian, functional-specs, system-designer, unit-designer, test-master | `inherit-parent` |
| tools-manager | `inherit-parent` |
| ssot-gate | `inherit-parent` |
| last-boss | `inherit-parent` |
| researcher | `inherit-parent` |

Use the exact detected slug for "grok-4.6 with fast on" (it may be spelled like `grok-4.6-fast`). If it is not available, mark the role as needing a choice and ask. Show the table and confirm before writing.

## 4. Stack detect (required)
Run the `stack-detect` skill. Show the detection table and wait until the user confirms or changes every slot: language, framework, package manager, test runner, linter, deploy target (or `none` / `unspecified` where they say so). If the repo is empty or unclear, ask those questions directly. **Never assume.**

## 5. Publish TOL
Spawn `tools-manager` with the confirmed table. It proposes `TOL-{PROJECT}-NNN` nodes (`confirmed: true`) into `.vmodel/proposals/`. Then spawn `ssot-gate` to publish them. If `.vmodel/` does not exist yet, create the empty layout from `references/vmodel-schema.md` first (this is the only time the runner writes there directly). Do not write `registries/tol.json` yourself.

## 6. Write the rule (overwrite the whole file so re-runs are idempotent)

Include a one-line stack summary per project from the published TOL records:

```
---
description: A.I.D project labels, isolation, per-role models and confirmed stack (overrides plugin defaults)
alwaysApply: true
---
# A.I.D configuration. One line per item.
projects: ACME
scope ACME: <one line: product and users>
isolation: strict (no cross-project edges; counterpart ids as plain text only)
stack ACME: language=<tool> <version>; framework=<tool>; package_manager=<tool>; test_runner=<tool>; linter=<tool>; deploy_target=<tool>
tol ACME: TOL-ACME-001, …
adept: grok-4.6-fast
req-guardian: inherit-parent
functional-specs: inherit-parent
system-designer: inherit-parent
unit-designer: inherit-parent
test-master: inherit-parent
tools-manager: inherit-parent
ssot-gate: inherit-parent
last-boss: inherit-parent
researcher: inherit-parent
```

The `stack` / `tol` lines are the confirmed catalog Adept and Test Master must follow. If a slot is `none`, write `none`.

## 7. Create `.vmodel/`
If missing, create the layout in `references/vmodel-schema.md` with empty registries and `graph/meta.json` `{"graph_version": 0, "projects": [...]}`. Suggest committing `.vmodel/` (except `docs/`, which can be rebuilt) to git.

## Reply
Labels, isolation, models, the confirmed stack table, published TOL ids, and the path of `aid-config.mdc`.
