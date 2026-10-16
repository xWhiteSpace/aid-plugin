---
name: aid-v-view
description: Rebuild the offline V-model debug view (.vmodel/docs/v-view.html) from published registries and graph/edges.json. V landing, per-level spec and test lists, Focus walk (USR>REQ>FNC/API>CMP/INT>UNT>code @trace>TST), World, and a review queue of lint flags. Owned by ssot-gate; agent-invoked on every publish and from the /v-view command. Inline JS/CSS, no CDN.
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
1. **Landing is a V.** Left rail, top to bottom: USR · Requirements (`REQ`) · Functional (`FNC`, `API`) · System (`INT`, `CMP`) · Unit (`UNT`). Coding at the bottom. Right rail into the same Coding point: Acceptance test · System test · Integration · Unit test. A donut and status pills count TST `passed` / `failed` / `skipped` / `not_run`. Empty levels stay empty.
2. **Level view (right node).** That level's checks, status pills, cases, `verifies` targets.
3. **Spec view (left node).** Published items of that level's kinds. Opening an item enters Focus.
4. **Focus.** One node in the centre. Walk published edges only: USR ↔ REQ ↔ FNC/API ↔ CMP/INT ↔ UNT ↔ `@trace` in code ↔ TST (and back). Tabs: Connections, USR, REQ, FNC, API, CMP, INT, UNT, Code, Tests. Code chips are scanned `@trace` hits (file, line, snippet from disk at publish time). Never invent a snippet.
5. **World.** Whole graph on the same V, pan and zoom. Hubs on the left rail (USR, REQ, FNC, API, CMP, INT, UNT) and tests on the right split by `level`. Coding holds `@trace` points. World is a control, not the first view.
6. **Review queue.** Lint flags only: broken `@trace`, orphan UNT, planned TST with no code carrying that id, missing links (orphan/gap), and other lint categories. Prev/Next. Open in Focus when the flag id is a published node. This queue does not write SSOT and does not mark passed.

## Never
- Hardcode a product, game, or brand. `PROJECT` comes from the SSOT.
- Fetch a CDN, require a server, or split the page into extra assets.
- Treat lineage as verification.
- Copy names or copy from another app's debug page.

## Done
Report the path to `v-view.html`, node / edge / `@trace` / lint counts, that landing is the V, and that World is a control. Footer on the page: plan lineage, not proof.
