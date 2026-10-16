# Changelog

## 0.1.1 — 2026-10-16

- Code traceability: no explanatory comments; each implementing function/module carries `@trace UNT-{PROJECT}-NNN` only.
- `vmodel_lint.py --code <dir>` flags orphan tags, untagged published units and malformed tags.
- ssot-gate /usr /catchup run lint with `--code` on publish.
- Kettle example: `examples/electric-kettle/src/` tagged for UNT-KTL-001..005.

## 0.1.0 — 2026-10-16

- First release: Cursor Plugin packaging of the A.I.D V-model / MBSE team.
- Commands: `/usr`, `/catchup`, `/docs`, `/setup-aid`.
- Agents: req-guardian, functional-specs, system-designer, unit-designer, test-master, ssot-gate, last-boss, researcher, adept.
- Project-local SSOT under `.vmodel/` with lint, baselines and offline docs (Mermaid SysML views + trace matrix).
- Worked example: smart electric kettle (`KTL`).
