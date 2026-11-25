# A.I.D plugin

**A.I.D** (Agent Intake & Design) is a Cursor plugin that turns a plain-words need into a traced V-model / MBSE design, SysML-aligned.

You type `/issue` with what you want. A team of helper agents writes the need (USR), the requirement (REQ), then functions, components, units and test **plans**, and publishes them into a Single Source of Truth inside **your** project under `.vmodel/`. You get diagrams and a trace matrix you can open offline.

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
4. In a product repo, run `/setup-aid` (stack, `.vmodel/`, issue form, gate Action, and the GitHub board), then `/issue`.

Team admins may need **Allow Local Plugin Imports** on (Dashboard → Settings → Security & Identity).

### From your GitHub repo (team)

1. Push this repository to GitHub (public for the public marketplace, any visibility for a team marketplace).
2. **Teams / Enterprise:** Dashboard → Plugins & MCPs → Add Marketplace → Import from Repo → paste the URL. Set access, then teammates install from **Customize**.
3. **Public Cursor Marketplace:** submit at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Plugins are reviewed; there is no "paste a URL and install" path for personal use outside local / team marketplace.

Verified from [cursor.com/docs/plugins](https://cursor.com/docs/plugins) and [Plugins reference](https://cursor.com/docs/plugins/building).

## Main command: `/issue`

1. Intake filter (project ask vs research vs junk).
2. **Imagine the use** (person, moment, smallest honest future, done-enough) then choose effort (`tiny` 2 / `small` 4 / `standard` 7 / `large` 11 gates). Run only the stages that lane earned.
3. **Stack gate:** confirmed `TOL` entries must exist (or `/issue` stops and runs stack-detect / asks).
4. req-guardian → USR + REQ (with `effort`) → ssot-gate → **Last Boss (REQ, slice)** when the lane earns it.
5. Later V layers and Last Boss checks run only when the imagined use earned them (see Imagine first).
6. ssot-gate publishes and **always** reports **full-graph** lint (or says there are none), including planned TST ids with no `@trace TST-…` in code.
7. When the lane includes them: **Last Boss (design-complete)** and **Last Boss (Done)** review the **full graph**. She never marks passed.
8. `/docs` builds the pictures and the V debug view. `/v-view` stays whole-project.

Other commands: `/setup-aid` (labels, models, **stack-detect → TOL**), `/catchup` (sync from your git diff), `/docs`, `/v-view`, `/issue-manager` (GitHub Project). Each of those is a command; matching skills use internal `aid-*` names (`aid-usr-flow`, `aid-setup`, `aid-catchup`, `aid-docs`, `aid-v-view`, `aid-board`) so the `/` menu lists every step once. `/issue` is the only start.

## Hard rules

- Only **ssot-gate** writes published registries.
- Nothing is marked passed without evidence (EVD).
- Projects are isolated (no cross-project edges).
- Ids: `USR|REQ|FNC|API|CMP|INT|UNT|TST|TOL|…-{PROJECT}-NNN`.
- **No guessed stack.** `/issue`, adept and test-master will not write code or tests until the user has confirmed TOL entries (language, test runner, and the other slots). Adept follows that language's comment syntax for `@trace UNT-…` on product code and `@trace TST-…` on tests.
- **UI is designed before it is coded.** Adept follows `ui-design`; Last Boss reviews the running screen against that record.
- **Last Boss:** light slice check for stages the lane earned; full-graph at design-complete and Done when those gates apply. Flags over-built for its future. Nothing is Done until proven.
- **Imagine first**, then Curiosity → Imagination → Intelligence (`aid-curiosity-imagination`). Effort must match the imagined use. Last Boss flags **over-built for its future**.
- **Lean slice first.** Agents start from `vmodel_slice.py` for their REQ; they may ask `ssot-gate` for a wider slice or the full graph. Publish lint and `/v-view` stay whole-project.
- **Reuse first.** Common capabilities go through a Researcher reuse-scan and a Tools Manager `TOL` (`library`/`api`) before Adept builds; from-scratch needs a recorded reason. Last Boss flags a reinvented wheel.
- **Coding vs tests in `/v-view`:** Coding is `@trace UNT-…` only; `@trace TST-…` sits on the TST (right rail). A new UNT is earned only if it can change, be reused, or be tested alone. Every TST has a V level; empty levels are stated, not collapsed into unit tests.
- **One `@trace` per unit** and a published `coded_in` edge (UNT→file). **See connections** walks 1-hop at a time (`uses`/TOL hidden unless shown).
- **Issue Manager** (gate-adjacent) runs the GitHub Project and empties Backlog. SSOT stays the source of truth. Only the Issue Manager moves Workflow Status.

Python 3.8+, no packages.

## Imagine first

The V is not a mandatory 11-gate march. At intake, picture the person and the moment, two or three futures of use (including the smallest honest one), and what "done and good enough" looks like from the user's side. **Then** choose effort. Lanes (`tiny` 2 / `small` 4 / `standard` 7 / `large` 11 gates) are the words for that judgement, not a keyword lookup. Default small; grow only for risk, money, safety, many users, or long life. A one-button light is tiny. Last Boss challenges a run heavier than that future.

## Board (`/issue-manager`)

The GitHub Project is a **view** of SSOT plus issues, not a second source of truth. `/issue-manager setup` creates a new Project with GraphQL and names the field Workflow Status. A parent is SYS.1 (requirement) or SUP.9 (fix). Sub-issues are the processes A.I.D names. The Issue Manager empties Backlog. Agents post signed notes. No proof, no move. A parent is Done when every opened sub-issue is Done. `/issue-manager trail USR-ID` walks parent then processes.

```bash
python3 scripts/vmodel_board.py .vmodel setup
python3 scripts/vmodel_board.py .vmodel status
python3 scripts/vmodel_board.py .vmodel attach 12 USR-APP-001 --kind Requirement --processes SWE.3,SWE.4 --what "Boil water"
python3 scripts/vmodel_board.py .vmodel gate --body "/gate-Parent-breakdown" --issue 12 --signer AID
python3 scripts/vmodel_board.py .vmodel note 12 "what I did, why, concern" --signer adept
python3 scripts/vmodel_board.py .vmodel trail USR-APP-001 --system
```

## How A.I.D stays lean

Agents do not ingest the whole SSOT on every stage. That is what kept a single REQ near half an hour and a large token bill.

- **`scripts/vmodel_slice.py`** (skill `aid-ssot-slice`, `user-invocable: false`; `/issue` calls it). Given a USR/REQ/FNC/CMP/UNT/TST id it writes a small offline JSON: that node, undirected neighbors within 2 edges on `graph/edges.json` (USR→REQ→FNC/API→CMP/INT→UNT→code `@trace`→TST), those registry entries, project TOL, and open lint flags for those ids only. No network.
- Each role **starts from the slice** for its REQ. If a decision needs a neighbor outside it, the role asks `ssot-gate` for `--hops N` or the full graph (`registries/` + `graph/edges.json`).
- **Global vision is kept:** publish lint is still full-graph; Last Boss reviews the full graph at design-complete and Done; `/v-view` is still the whole project. Per-stage Last Boss is a light slice check only. The slice stays a 2-hop neighborhood, so a large project stays small in the prompt.

## Layout

```text
.cursor-plugin/plugin.json   # Cursor Plugin manifest
plugin.json                  # Agent Plugins companion
agents/                      # req-guardian, ssot-gate, tools-manager, adept, last-boss, issue-manager, …
skills/                      # aid-usr-flow, aid-setup, aid-ssot-slice, aid-board, aid-curiosity-imagination, stack-detect, ui-design, aid-v-view, reverse-engineer-*, …
commands/                    # /issue /issue-manager /catchup /docs /setup-aid /v-view
rules/                       # always-on V-model core
scripts/                     # vmodel_docs.py, vmodel_lint.py, vmodel_vview.py, vmodel_slice.py, vmodel_board.py
references/vmodel-schema.md  # .vmodel/ schema
```
