---
name: aid-ssot-slice
description: Build a small offline JSON slice of the .vmodel/ SSOT around one USR/REQ/FNC/CMP/UNT/TST id (2-hop neighbors on graph/edges.json, registry entries, project TOL, lint for those ids). Agent-invoked from /usr; not a slash command.
user-invocable: false
---

# Lean SSOT slice

Each agent at each `/usr` stage starts from a **slice** for its REQ (or the id it was given). Do not load the full registries by default. Readable offline; no network.

## Build

From the project root (Python 3.8+, no packages):

```
python3 <plugin>/scripts/vmodel_slice.py .vmodel <ID> [--code <project-tree>] [--out path] [--hops 2]
```

`<ID>` is `USR|REQ|FNC|API|CMP|INT|UNT|TST-{PROJECT}-NNN`. Default `--hops 2` (undirected on `graph/edges.json`, following USR→REQ→FNC/API→CMP/INT→UNT→code `@trace`→TST). `--code` adds `@trace` hits for slice UNT/TST. Omit `--code` only when there is no source yet.

The JSON has that node, neighbors in range, chain-adjacent INT/TST, live project TOL, those registry entries, and open lint flags for those ids only.

## When

- `/usr` runner: after Gate 1, slice the new REQ(s) and hand the JSON to every downstream role (and to Last Boss for the light per-stage check).
- Any role that was given only an id: run this before designing.
- **Wider or full:** if a decision needs a neighbor outside the slice, ask `ssot-gate` for `--hops N` or the full graph (`registries/` + `graph/edges.json`). Do not guess missing nodes.

## Stays whole-project

- `ssot-gate` publish lint is still full-graph.
- Last Boss reviews the **full graph** at design-complete and Done (per-stage challenges are this slice only).
- `/v-view` is still the whole project.
