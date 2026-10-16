# Changelog

## 0.4.2 — 2026-10-16

- Offline V debug view reaches feature parity with the reference debug page structure (generic V-model only; no branded lockup or product names). One self-contained file, inline CSS/JS/SVG, no CDN.
- Landing camera: `measurePose` fly-in/out (translate3d + scale, 600ms), reduced-motion skip, CODING at `z: -120`, perspective floor grid (`FLOOR` / `floorGridPath`) with near/far masks and horizon, rail polylines (`railPoints`) plus pulse, hot/hover halos, status donut and pills.
- Globe icon (inline SVG) opens World. Focus graph: Connections rings and published edges, kind tabs, pan/zoom, See connection, lineage panel. Spec **Review** opens a ReviewQueue of published items (Keep/Rewrite/Reject in local storage, not SSOT); auto flags include lineage gaps and lint for that id.

## 0.4.1 — 2026-10-16

- Slash menu showed each step twice (`commands/<name>.md` and `skills/<name>/SKILL.md` shared `usr`, `docs`, `catchup`, `setup-aid`, `v-view`). Commands stay the user `/` entries. Colliding skills renamed so they no longer share those names:
  - `skills/usr` → `skills/aid-usr-flow`
  - `skills/docs` → `skills/aid-docs`
  - `skills/catchup` → `skills/aid-catchup`
  - `skills/setup-aid` → `skills/aid-setup` (`/setup-aid` unchanged)
  - `skills/v-view` → `skills/aid-v-view`
- Those five skills drop `disable-model-invocation: true` (Cursor's public skill docs: that flag makes a skill slash-only; the agent will not auto-apply it) and set `user-invocable: false`. Cursor CLI honours `user-invocable: false` (hide from `/`, agent still loads). Cursor's public skill/plugin docs do not list `user-invocable`; the IDE `/` menu still lists skills by name, so the rename is what stops the duplicate.

## 0.4.0 — 2026-10-16

- V debug view: `scripts/vmodel_vview.py` + `v-view` skill (renamed `aid-v-view` in 0.4.1), owned by ssot-gate and run on every publish. Writes `.vmodel/docs/v-view.html` (one self-contained offline HTML file, inline JS/CSS, no CDN) from registries, `graph/edges.json`, `@trace` hits and lint flags.
- Landing is a V (left: USR / Requirements / Functional / System / Unit; Coding; right: test levels) with a donut and status pills. Per-level spec and test lists. Focus walks USR↔REQ↔FNC/API↔CMP/INT↔UNT↔code `@trace`↔TST. World pans the whole graph. Review queue lists lint flags (broken `@trace`, orphan UNT, planned TST with no code, missing links).
- `/v-view` rebuilds and opens the page. `/docs` and kettle example regenerate it. Generic V-model only.

## 0.3.0 — 2026-10-16

- Adept designs every user-facing screen before coding (`skills/ui-design/SKILL.md`): layout, visual hierarchy, spacing and type scale, colour and contrast (WCAG AA), every state (empty, loading, error, hover, focus, disabled), keyboard/accessibility, responsive breakpoints. Design is recorded in `UNT.ui` or an SSOT doc; code must follow it. Language/framework-agnostic except the confirmed TOL. No new agent.
- Last Boss is a stage-by-stage checklist (REQ quality, FNC, CMP/INT, UNT, code, tests) plus a strict front-end review against that UI design using screenshots or the running app. Done means proven; she never marks anything passed.
- `/usr` spawns Last Boss after each stage before moving on, and again before Done.
- Lint `--code` and ssot-gate publish: flag a planned TST that has no test in code carrying `@trace TST-{PROJECT}-NNN`, alongside the existing UNT `@trace` checks. Kettle example tests under `examples/electric-kettle/tests/` tag `TST-KTL-001..012`.

## 0.2.0 — 2026-10-16

- Stack/setup check: agents never guess language or tooling.
- New `tools-manager` agent owns `TOL-{PROJECT}-NNN` (language, framework, package manager, test runner, linter, deploy target, versions). Proposes only; does not code or set style.
- New `stack-detect` skill reads repo manifests and lock/CI files, shows evidence, and asks the user to confirm or change. Empty or unclear repos are questions, not defaults.
- `/setup-aid` runs stack-detect, publishes confirmed TOL via ssot-gate, and writes a stack summary into `.cursor/rules/aid-config.mdc`.
- Hard gate: `/usr`, adept and test-master stop if there is no confirmed TOL; they ask or run stack-detect.
- Adept is language-agnostic: follows the TOL stack, uses that language's `comment_syntax` for `@trace`, and runs the TOL test runner.
- Schema, lint and kettle example: TOL kind and `uses` edges; lint flags a project with code but no TOL. `TOL-KTL-001..006` (Python, pytest, matching `src/*.py`).

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
