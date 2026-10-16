---
name: v-view
description: Rebuild the offline V-model debug view from .vmodel/ and open .vmodel/docs/v-view.html.
---
Run the `v-view` skill from the A.I.D plugin.

1. Locate `scripts/vmodel_vview.py` in the A.I.D plugin (search `~/.cursor/plugins/` for a path ending in `aid-plugin/scripts/vmodel_vview.py` if needed).
2. From the project root, rebuild:
   ```
   python3 <plugin>/scripts/vmodel_vview.py .vmodel --code <project-tree>
   ```
   Use the same `--code` tree as lint (source and tests). Omit `--code` only when there is no source yet.
3. Open `.vmodel/docs/v-view.html` in a browser (local file, no server). Confirm landing is the V, then that a level, Focus, World and the review queue respond.

Reply with the file path, counts from the generator, and that the page is plan lineage, not proof.
