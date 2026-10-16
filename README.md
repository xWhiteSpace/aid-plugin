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
2. **Stack gate:** confirmed `TOL` entries must exist (or `/usr` stops and runs stack-detect / asks).
3. req-guardian → USR + REQ.
4. ssot-gate publishes.
5. functional-specs → FNC / API.
6. system-designer → CMP / INT.
7. unit-designer → UNT.
8. test-master → TST plans (`not_run`) using the TOL test runner.
9. ssot-gate publishes again and **always** reports lint (or says there are none).
10. last-boss challenges claims.
11. `/docs` builds the pictures.

Other commands: `/setup-aid` (labels, models, **stack-detect → TOL**), `/catchup` (sync from your git diff), `/docs`.

## Hard rules

- Only **ssot-gate** writes published registries.
- Nothing is marked passed without evidence (EVD).
- Projects are isolated (no cross-project edges).
- Ids: `USR|REQ|FNC|API|CMP|INT|UNT|TST|TOL|…-{PROJECT}-NNN`.
- **No guessed stack.** `/usr`, adept and test-master will not write code or tests until the user has confirmed TOL entries (language, test runner, and the other slots). Adept follows that language's comment syntax for `@trace UNT-…` only.

## Example

`examples/electric-kettle/` is a full worked V for a smart kettle, project code **KTL**. Open `examples/electric-kettle/.vmodel/docs/index.html` in a browser. Rebuild with:

```bash
python3 scripts/vmodel_lint.py examples/electric-kettle/.vmodel --write --code examples/electric-kettle/src
python3 scripts/vmodel_docs.py examples/electric-kettle/.vmodel
```

Python 3.8+, no packages. The example stack is recorded as `TOL-KTL-001..006` (Python, pytest, no framework / package manager / linter / deploy target).

## Layout

```text
.cursor-plugin/plugin.json   # Cursor Plugin manifest
plugin.json                  # Agent Plugins companion
agents/                      # req-guardian, ssot-gate, tools-manager, adept, …
skills/                      # usr, setup-aid, stack-detect, reverse-engineer-*, …
commands/                    # /usr /catchup /docs /setup-aid
rules/                       # always-on V-model core
scripts/                     # vmodel_docs.py, vmodel_lint.py
references/vmodel-schema.md  # .vmodel/ schema
examples/electric-kettle/    # KTL sample SSOT + docs
```
