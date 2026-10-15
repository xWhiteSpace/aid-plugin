---
name: setup-aid
description: Configure A.I.D for this project. Sets project labels, the strict isolation rule between them, and the model per role, then writes an always-applied rule file .cursor/rules/aid-config.mdc and the empty .vmodel/ layout. Use for /setup-aid, "configure aid", or adding a new project label.
disable-model-invocation: true
---

# /setup-aid

Write `.cursor/rules/aid-config.mdc` in the project repo: an always-applied rule every A.I.D skill and subagent reads.

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
| ssot-gate | `inherit-parent` |
| last-boss | `inherit-parent` |
| researcher | `inherit-parent` |

Use the exact detected slug for "grok-4.6 with fast on" (it may be spelled like `grok-4.6-fast`). If it is not available, mark the role as needing a choice and ask. Show the table and confirm before writing.

## 4. Write the rule (overwrite the whole file so re-runs are idempotent)

```
---
description: A.I.D project labels, isolation and per-role models (overrides plugin defaults)
alwaysApply: true
---
# A.I.D configuration. One line per item.
projects: ACME
scope ACME: <one line: product and users>
isolation: strict (no cross-project edges; counterpart ids as plain text only)
adept: grok-4.6-fast
req-guardian: inherit-parent
functional-specs: inherit-parent
system-designer: inherit-parent
unit-designer: inherit-parent
test-master: inherit-parent
ssot-gate: inherit-parent
last-boss: inherit-parent
researcher: inherit-parent
```

## 5. Create `.vmodel/`
If missing, create the layout in `references/vmodel-schema.md` with empty registries and `graph/meta.json` `{"graph_version": 0, "projects": [...]}`. Suggest committing `.vmodel/` (except `docs/`, which can be rebuilt) to git.
