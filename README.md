# A.I.D plugin

**A.I.D** (Agent Intake & Design) is a Cursor plugin that turns a plain-words need into a traced V-model / MBSE design, SysML-aligned.

You type `/usr` with what you want. A team of helper agents writes the need (USR), the requirement (REQ), then functions, components, units and test **plans**, and publishes them into a Single Source of Truth inside **your** project under `.vmodel/`. You get diagrams and a trace matrix you can open offline.

```text
   Requirements          Acceptance tests
        |                       ^
   Functions / APIs        System tests
        |                       ^
   Components / seams    Integration tests
        |                       ^
      Units  ---- Coding ----  Unit tests
```

## Install (your own GitHub repo)

This is a **Cursor Plugin** (manifest at `.cursor-plugin/plugin.json`).

### Local (try it tonight)

1. Copy this folder to `~/.cursor/plugins/local/aid-plugin`  
   (or clone your repo there). Symlinks that point outside that folder are skipped by Cursor.
2. Restart Cursor, or run **Developer: Reload Window**.
3. Open **Customize** and confirm skills, agents and commands appear.
4. In a project, run `/setup-aid` (this detects the stack and asks you to confirm it), then `/usr`.

Team admins may need **Allow Local Plugin Imports** on (Dashboard → Settings → Security & Identity).

### From your GitHub repo (team)

1. Push this repository to GitHub (public for the public marketplace, any visibility for a team marketplace).
2. **Teams / Enterprise:** Dashboard → Plugins & MCPs → Add Marketplace → Import from Repo → paste the URL. Set access, then teammates install from **Customize**.
3. **Public Cursor Marketplace:** submit at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Plugins are reviewed; there is no "paste a URL and install" path for personal use outside local / team marketplace.

Verified from [cursor.com/docs/plugins](https://cursor.com/docs/plugins) and [Plugins reference](https://cursor.com/docs/plugins/building).

## Main command: `/usr`

1. Intake filter (project ask vs research vs junk).
2. **Imagine the use** (person, moment, smallest honest future, done-enough) then choose effort (`tiny` 2 / `small` 4 / `standard` 7 / `large` 11 gates). Run only the stages that lane earned.
3. **Stack gate:** confirmed `TOL` entries must exist (or `/usr` stops and runs stack-detect / asks).
4. req-guardian → USR + REQ (with `effort`) → ssot-gate → **Last Boss (REQ, slice)** when the lane earns it.
5. Later V layers and Last Boss checks run only when the imagined use earned them (see Imagine first).
6. ssot-gate publishes and **always** reports **full-graph** lint (or says there are none), including planned TST ids with no `@trace TST-…` in code.
7. When the lane includes them: **Last Boss (design-complete)** and **Last Boss (Done)** review the **full graph**. She never marks passed.
8. `/docs` builds the pictures and the V debug view. `/v-view` stays whole-project.

Other commands: `/setup-aid` (labels, models, **stack-detect → TOL**), `/catchup` (sync from your git diff), `/docs`, `/v-view`. Each of those is a command; matching skills use internal `aid-*` names (`aid-usr-flow`, `aid-setup`, `aid-catchup`, `aid-docs`, `aid-v-view`) so the `/` menu lists every step once.

## Hard rules

- Only **ssot-gate** writes published registries.
- Nothing is marked passed without evidence (EVD).
- Projects are isolated (no cross-project edges).
- Ids: `USR|REQ|FNC|API|CMP|INT|UNT|TST|TOL|…-{PROJECT}-NNN`.
- **No guessed stack.** `/usr`, adept and test-master will not write code or tests until the user has confirmed TOL entries (language, test runner, and the other slots). Adept follows that language's comment syntax for `@trace UNT-…` on product code and `@trace TST-…` on tests.
- **UI is designed before it is coded.** Adept follows `ui-design`; Last Boss reviews the running screen against that record.
- **Last Boss:** light slice check for stages the lane earned; full-graph at design-complete and Done when those gates apply. Flags over-built for its future. Nothing is Done until proven.
- **Imagine first**, then Curiosity → Imagination → Intelligence (`aid-curiosity-imagination`). Effort must match the imagined use. Last Boss flags **over-built for its future**.
- **Lean slice first.** Agents start from `vmodel_slice.py` for their REQ; they may ask `ssot-gate` for a wider slice or the full graph. Publish lint and `/v-view` stay whole-project.
- **Reuse first.** Common capabilities go through a Researcher reuse-scan and a Tools Manager `TOL` (`library`/`api`) before Adept builds; from-scratch needs a recorded reason. Last Boss flags a reinvented wheel.
- **Coding vs tests in `/v-view`:** Coding is `@trace UNT-…` only; `@trace TST-…` sits on the TST (right rail). A new UNT is earned only if it can change, be reused, or be tested alone. Every TST has a V level; empty levels are stated, not collapsed into unit tests.
- **One `@trace` per unit** and a published `coded_in` edge (UNT→file). **See connections** walks 1-hop at a time (`uses`/TOL hidden unless shown).

## Example

`examples/electric-kettle/` is a full worked V for a smart kettle, project code **KTL**. Open `examples/electric-kettle/.vmodel/docs/index.html` or `examples/electric-kettle/.vmodel/docs/v-view.html` in a browser. Rebuild with:

```bash
python3 scripts/vmodel_lint.py examples/electric-kettle/.vmodel --write --code examples/electric-kettle
python3 scripts/vmodel_docs.py examples/electric-kettle/.vmodel --code examples/electric-kettle
```

Python 3.8+, no packages. The example stack is recorded as `TOL-KTL-001..006` (Python, pytest, no framework / package manager / linter / deploy target). A worked Curiosity → Imagination → Intelligence loop on the temperature-display choice is in `curiosity-imagination-temperature.md`. Keep-warm duration reuse-scan (stdlib, not a calendar) is in `curiosity-imagination-reuse-datetime.md`. Imagine-the-use for a one-button kettle light (`tiny`, 2 gates) is in `imagine-the-use-kettle-light.md`. A lean slice of `REQ-KTL-001` is in `.vmodel/docs/KTL/slice-REQ-KTL-001.json`.

## Imagine first

The V is not a mandatory 11-gate march. At intake, picture the person and the moment, two or three futures of use (including the smallest honest one), and what "done and good enough" looks like from the user's side. **Then** choose effort. Lanes (`tiny` 2 / `small` 4 / `standard` 7 / `large` 11 gates) are the words for that judgement, not a keyword lookup. Default small; grow only for risk, money, safety, many users, or long life. A one-button light is tiny. Last Boss challenges a run heavier than that future.

## How A.I.D stays lean

Agents do not ingest the whole SSOT on every stage. That is what kept a single REQ near half an hour and a large token bill.

- **`scripts/vmodel_slice.py`** (skill `aid-ssot-slice`, `user-invocable: false`; `/usr` calls it). Given a USR/REQ/FNC/CMP/UNT/TST id it writes a small offline JSON: that node, undirected neighbors within 2 edges on `graph/edges.json` (USR→REQ→FNC/API→CMP/INT→UNT→code `@trace`→TST), those registry entries, project TOL, and open lint flags for those ids only. No network.
- Each role **starts from the slice** for its REQ. If a decision needs a neighbor outside it, the role asks `ssot-gate` for `--hops N` or the full graph (`registries/` + `graph/edges.json`).
- **Global vision is kept:** publish lint is still full-graph; Last Boss reviews the full graph at design-complete and Done; `/v-view` is still the whole project. Per-stage Last Boss is a light slice check only.
- Kettle example: `examples/electric-kettle/.vmodel/docs/KTL/slice-REQ-KTL-001.json` is **25 nodes / 20 409 bytes** vs the full `registries/*.json` at **47 nodes / 25 859 bytes** (also 24 vs 61 edges). Larger projects shrink much more; the slice stays a 2-hop neighborhood.

## Layout

```text
.cursor-plugin/plugin.json   # Cursor Plugin manifest
plugin.json                  # Agent Plugins companion
agents/                      # req-guardian, ssot-gate, tools-manager, adept, last-boss, …
skills/                      # aid-usr-flow, aid-setup, aid-ssot-slice, aid-curiosity-imagination, stack-detect, ui-design, aid-v-view, reverse-engineer-*, …
commands/                    # /usr /catchup /docs /setup-aid /v-view
rules/                       # always-on V-model core
scripts/                     # vmodel_docs.py, vmodel_lint.py, vmodel_vview.py, vmodel_slice.py
references/vmodel-schema.md  # .vmodel/ schema
examples/electric-kettle/    # KTL sample SSOT + docs
```
