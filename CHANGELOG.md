# Changelog

## 0.6.1 — 2026-10-17

- Reuse first: before a common capability (calendar, auth, payments, maps, charts, rich text, upload, date/time, validation, UI kits, …) Adept asks Researcher for a reuse-scan (options as possible futures), Tools Manager records one `TOL` (`library` / `api`), then Adept integrates it. From-scratch needs a written `decision`. Last Boss flags a reinvented wheel.
- `library` and `api` TOL slots (many allowed); exclusive stack slots stay one-live-per-project. `/setup-aid` may propose common APIs up front after a reuse-scan.
- Kettle: `examples/electric-kettle/curiosity-imagination-reuse-datetime.md` (stdlib duration, not a calendar).

## 0.6.0 — 2026-10-17

- Lean SSOT slices: `scripts/vmodel_slice.py` plus skill `aid-ssot-slice` (`user-invocable: false`; no new slash command). Given a USR/REQ/FNC/CMP/UNT/TST id, writes a small offline JSON (2-hop neighborhood on `graph/edges.json`, registry entries, project TOL, lint for those ids only). `/usr` hands that slice to each stage. A role may ask `ssot-gate` for `--hops N` or the full graph.
- Publish lint stays full-graph. `/v-view` stays whole-project. Last Boss per-stage checks are light (slice only); full-graph challenge only at design-complete (after Gate 2) and Done.
- Core rule 15 (start from a slice); short notes on every `agents/*.md` and `aid-usr-flow`. README: "How A.I.D stays lean".
- Kettle example: `examples/electric-kettle/.vmodel/docs/KTL/slice-REQ-KTL-001.json` — 25 nodes / 20 409 bytes vs full registries 47 nodes / 25 859 bytes (24 vs 61 edges).

## 0.5.0 — 2026-10-17

- Curiosity → Imagination → Intelligence: every agent runs `aid-curiosity-imagination` before a decision. Curiosity lists unknowns and asks questions that would change the pick. Imagination names 2–4 possible futures (labelled as possibilities; no invented facts). Intelligence chooses the future most likely to be correct, with reason, predicted outcome, and a later check.
- Wired into `aid-vmodel-core` (rule 14), req-guardian (before minting), functional / system / unit designers, adept (before UI/code), test-master (before test design). Last Boss refuses missing curiosity and thin imagination (only one option). ssot-gate copies each proposal `decision` into the baseline.
- Kettle example: `examples/electric-kettle/curiosity-imagination-temperature.md` (no live °C display; three options; pick A).
- No new slash command (skill name `aid-curiosity-imagination`, `user-invocable: false`). No new agent.

## 0.4.4 — 2026-10-17

- World single click focuses a node only (highlight / peek, same as a Coding-cluster click): no new page tab, no detail view. Double click within 400ms opens a page tab (`openTab`). The peek is delayed until the double-click window closes so a double click does not flash a focus first.
- Connection lines and dimming of unconnected World nodes appear only after **See connection** (`linkId`), not on focus.
- Removed the dead origin circle (peek ring parked at 0,0) from World, Focus, and any view that showed it.

## 0.4.3 — 2026-10-16

- V debug view World and Focus fields apply `magScale` live: `MAG_PX = 56`, `MAG_MAX = 3`, screen-pixel distance `world dist * cursor.px`, smoothstep ease, dots swell to 3× at the centre; halo at `r+6` when `grow > 1.05`. Cursor is tracked on `pointermove` in world coordinates with the current zoom; radii mutate in place (no innerHTML on move).
- World dots and kind-list cards open a page tab on click or double-click (`openTab` / page tabs bar: switch, close, focus graph per tab). Focus field: single tap peeks, double tap within 400ms opens a tab. Lineage pills double-click open a tab. `DRAG_PX = 6`. Other pointer/hover/animation gaps vs the reference DebugPage/FocusSpace are listed on the PR.

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
