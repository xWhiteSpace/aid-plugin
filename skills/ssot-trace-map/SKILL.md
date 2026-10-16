---
name: ssot-trace-map
description: Build the standing SSOT map for one project: one static HTML page in the V debug shape (landing rails, one-node focus, World) and one JSON or SQLite variable file. Reads only published .vmodel/ data. Use after a publish or with /docs.
---
# SSOT trace map

Build the standing map beside the docs site. Two files:

1. One self-contained static HTML page in the V debug shape below. Inline CSS and script, no network, no build step. File: `.vmodel/docs/v-view.html` (built by `scripts/vmodel_vview.py` / the `v-view` skill). The older `neighborhood.html` name is the same contract.
2. One variable file: `.vmodel/docs/<PROJECT>/variables.json` (and, if the sqlite3 Python module is available, `.vmodel/docs/<PROJECT>/variables.sqlite`).

Prefer running `scripts/vmodel_docs.py`, which already produces both. This skill is the layout and content contract for that page.

Stack-agnostic and project-scoped. `PROJECT` is an input. Do not hardcode one product, language or framework. Do not publish or amend SSOT nodes. Do not invent a node, edge, title, statement, status, source path or snippet. Published lineage is not proof. Never mark a check passed, failed or skipped unless that result is already stored on the published node. With no run result, the status is `not_run`.

## Inputs
- `PROJECT`: the short code in ids (`KIND-PROJECT-NNN`).
- SSOT root: `.vmodel/` (registries, graph, lint).
- Output: `.vmodel/docs/<PROJECT>/`, replaced only when the caller asks for a build.

## Landing
The first view is a V. Two rails meet at one Coding point at the bottom.

Left rail, top to bottom: Requirements (`USR`, `REQ`) · Functional (`FNC`, `API`) · System (`INT`, `CMP`) · Unit (`UNT`).
Right rail, top to bottom into the same Coding point: Acceptance test · System test · Integration · Unit test.

A check belongs on the right level named by its published `level`. If the node has no level, put it on unit test. Opening a right level lists that level's checks with status (`passed`, `failed`, `skipped`, `not_run`), cases and a domain filter, plus a donut of those four counts. Opening a left level lists that level's spec items. Empty levels stay empty.

## Focus
Opening a node freezes that one node as the center. Rings, in order: `REQ`, `FNC`, `API`, `CMP`, `UNT`, `TST`. Tabs: Connections (default), REQ, FNC, API, CMP, UNT, Tests.

Walk published links only. A function's neighborhood is:
- Requirements it `implements`.
- Interface nodes (`API`) that `depends_on` it, and integration seams (`INT`) whose `implements_fnc` is it. `INT` is listed on the System landing level; it is not a focus ring and not a World hub.
- The component from `allocated_to`.
- Units with a `refines` edge to it.
- Tests with a published `verifies` edge to that function, to one of those units, or to one of those requirements.

Do not add a neighbor that has no published link.

## World
World clusters every node that has a hub onto the same V, and can pan and zoom. Hubs, left rail: REQ, FNC, API, CMP, UNT. Right rail, tests only, split by level. `USR` and `INT` stay on their landing lists; they are not World hubs.

## Side panel
- A need (`REQ` or `USR`): Satisfied by (functions that implement it).
- A function: Allocated to, Refined by, Satisfies.
- A component: Functions, Ports, Parts.
- A contract (`API`): Connects, Used by.
- A unit: its `source_files` chain and a snippet only when the published node names a real file that can be read. Never invent a snippet.

## Variables
One row per named field. Walk `request.headers`, `request.query`, `request.body` and `response.success.body` on each `API` for this project. Nested objects use a dotted path. Columns: `id`, `name`, `type`, `definition`, `parent_interface`, `traced_requirement`.

## Done
Report both file paths, that the landing view is the V, that World is a control and not the first view, the node count and the variable row count. Footer: plan lineage, not proof. Do not claim the system is verified.
