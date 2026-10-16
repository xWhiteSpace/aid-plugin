---
name: docs
description: Build the graphical V-model docs from the published .vmodel/ SSOT. SysML-style Mermaid diagrams (requirements, block definition, internal block, per-function sequence), a REQ→FNC→CMP→UNT→TST trace matrix with gaps, and an offline static HTML site under .vmodel/docs/. Use for /docs or "show me the documentation".
disable-model-invocation: true
---

# /docs

1. Locate this plugin's `scripts/vmodel_docs.py` (search `~/.cursor/plugins/` for a path ending in `aid-plugin/scripts/vmodel_docs.py` if you don't know the root).
2. Run from the project root:
   ```
   python3 <plugin>/scripts/vmodel_lint.py .vmodel --write --code <project-tree>
   python3 <plugin>/scripts/vmodel_docs.py .vmodel --code <project-tree>
   python3 <plugin>/scripts/vmodel_vview.py .vmodel --code <project-tree>
   ```
   Python 3.8+ only, no packages. `--code` is source and tests (omit only when there is no source yet).
3. Output under `.vmodel/docs/`:
   - `v-view.html`: interactive V debug view (landing rails, per-level spec/tests, Focus walk, World, review queue of lint flags). Self-contained, no CDN. See the `v-view` skill.
   - `index.html`: open it in a browser, no network needed. One tab per project. Diagrams render as SVG offline when a local `mermaid.min.js` is present in `.vmodel/docs/` (optional), else the page shows a built-in SVG V-overview and the Mermaid source. Link to `v-view.html`.
   - `<PROJECT>/requirements.mmd`: requirements diagram (USR, REQ, derives).
   - `<PROJECT>/bdd.mmd`: block definition diagram (CMP blocks with allocated FNC).
   - `<PROJECT>/ibd.mmd`: internal block diagram (CMP with INT ports/connectors).
   - `<PROJECT>/seq-<FNC-id>.mmd`: one sequence diagram per function.
   - `<PROJECT>/trace-matrix.md` and `.csv`: REQ → FNC → CMP → UNT → TST with gaps marked `GAP`.
   - `<PROJECT>/variables.json`: API fields as a variable list.
4. The docs show published lineage only. They are a plan, not proof. Test status shows `not_run` unless an EVD backs it.

Reply with the path to `index.html` and `v-view.html`, the node counts per project, the number of gaps and the lint flag count.
