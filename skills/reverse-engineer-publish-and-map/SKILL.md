---
name: reverse-engineer-publish-and-map
description: "Use when reverse-engineering, as ssot-gate: publish accepted design only, then rebuild the docs (Mermaid views, trace matrix, variables) and the trace map from the published graph."
---
# Reverse engineer: publish and map

Run as the `ssot-gate` subagent.

Use when design bots propose a catch-up slice. You are the only publisher. You do not invent product facts.

## Accept
1. Accept a proposal only from the bot who owns that kind: requirements, functions, components, units.
2. Refuse a link the proposal does not justify. Do not fill gaps yourself.
3. Return the ids and what you refused.

## Map
After the slice is accepted, rebuild the viewable pack from the published graph only:
- Run the `docs` skill: Mermaid SysML views, the trace matrix and the static site under `.vmodel/docs/`, plus `v-view.html` (`v-view` / `ssot-trace-map`).
- `.vmodel/docs/variables.json` of interface variables: id, name, type, definition, parent interface, traced requirement.

Do not add a node because it appears in source code and not in the graph. The map shows what was published.

## Not your job
Deciding features, writing functions, or reading the repo to discover behavior.
