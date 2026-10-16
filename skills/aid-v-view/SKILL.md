---
name: aid-v-view
description: Rebuild the offline V-model debug view (.vmodel/docs/v-view.html) from published registries and graph/edges.json. V landing with fly-in camera, perspective floor, rails, donut and pills, Globe World entry, Focus graph (tabs and edges), and a ReviewQueue of published items. Owned by ssot-gate; agent-invoked on every publish and from the /v-view command. Inline JS/CSS/SVG, no CDN.
user-invocable: false
---

# V debug view

ssot-gate owns this file. Adept never writes it. The page is a **plan view**, not proof. Do not mark tests passed from it.

## When
- Every publish (after lint), as ssot-gate.
- `/v-view` (rebuild then open).
- `/docs` (same generator).

## Build
From the project root (Python 3.8+, no packages):

```
python3 <plugin>/scripts/vmodel_vview.py .vmodel --code <project-tree>
```

`--code` is the tree that contains product source **and** tests (same as lint). Omit it only when there is no source yet. Output: `.vmodel/docs/v-view.html` (self-contained, inline CSS/JS, no network, no CDN). Reads published registries, `graph/edges.json`, lint flags, and `@trace` tags from `--code`.

## Page contract
1. **Landing is a V.** Left rail, top to bottom: USR · Requirements (`REQ`) · Functional (`FNC`, `API`) · System (`INT`, `CMP`) · Unit (`UNT`). Coding at the bottom (`z: -120`). Right rail into the same Coding point: Acceptance test · System test · Integration · Unit test. Rails from `railPoints`. Perspective floor (`FLOOR`, `floorGridPath`). A donut and status pills count TST `passed` / `failed` / `skipped` / `not_run`. Empty levels stay empty.
2. **Fly-in camera.** Clicking a level dot runs `measurePose` (origin, translate3d, scale). Reduced-motion skips the dolly. Hot/hover halos on the nearest node.
3. **Level view (right node).** That level's checks, status pills, cases, `verifies` targets, domain filter.
4. **Spec view (left node).** Published items of that level's kinds, kind filter. Opening an item enters Focus. **Review** opens the ReviewQueue.
5. **Focus.** One node in the centre. Walk published edges only. Tabs: Connections, USR, REQ, FNC, API, CMP, UNT, Tests. `INT` shares the API ring/hub. Unit code chips are scanned `@trace` hits (file, line, snippet from disk at publish time). Never invent a snippet.
6. **World.** Globe icon on landing (inline SVG). Whole graph on the same V, pan and zoom, Fit / ±. Hubs: USR, REQ, FNC, API, CMP, UNT; tests on the right split by `level`. Coding holds `@trace` points. World is a control, not the first view.
7. **Review queue.** Published items at that spec level (not SSOT writes). Auto flags: missing USR/FNC/TST links, truncated titles, plus lint for that id. Keep / Rewrite / Reject and a note stay in local storage. Prev/Next. Neighborhood opens Focus. This queue does not mark passed.

## Never
- Hardcode a product, game, or brand. `PROJECT` comes from the SSOT.
- Fetch a CDN, require a server, or split the page into extra assets.
- Treat lineage as verification.
- Copy names or copy from another app's debug page.

## Done
Report the path to `v-view.html`, node / edge / `@trace` / lint counts, that landing is the V, and that World is a control. Footer on the page: plan lineage, not proof.
