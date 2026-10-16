---
name: catchup
description: Bring the V-model up to date after you changed code yourself. Reads the local git diff since the last SSOT baseline and runs it through as reverse-engineering (new behavior) or an amendment (changed behavior). Use for /catchup or "sync the docs with my code".
disable-model-invocation: true
---

# /catchup

## 1. Find the range
- Read `.vmodel/graph/meta.json` → `source_commit` of the last publish. If absent, ask the user for a base ref (default: the merge base with the main branch).
- Run `git diff --stat <base>..HEAD` and `git diff <base>..HEAD`, plus `git status --porcelain` for uncommitted work (report it; include it only if the user agrees).

## 2. Trace
Spawn a subagent with the `reverse-engineer-code-read` skill on the changed files. Output is a trace only: symbols, writers, readers, not-seen items.

## 3. Classify against the published graph
For each changed behavior, find the UNT/FNC whose `source_files` or rules cover it.
- Covered, and the observable result changed → **amendment** path: `req-guardian` amends the REQ if the acceptance criterion is now false; owners amend FNC/UNT/TST with `previous`/`new_full` blocks.
- Not covered and user-visible → **reverse-engineering** path: `reverse-engineer-requirements` → `-functions` → `-system` → `-units` → `-tests`.
- Implementation only (refactor, rename, speed with the same result) → no REQ; update `source_files` on the UNT if paths moved.
- A test file with no TST → `test-master` proposes a TST with status `not_run`.

## 4. Publish and map
Run `reverse-engineer-publish-and-map` as `ssot-gate`, with `source_commit` set to `HEAD`. Then run the `docs` skill.

## Reply
The range, amended ids, new ids, items left out (with the reason), lint flags, and open questions for the user.

On publish, `ssot-gate` runs `vmodel_lint.py .vmodel --code <project-tree>` so orphan / untagged / malformed `@trace UNT-…` / `@trace TST-…` tags, and a planned TST with no test in code carrying that id, are reported with the rest of the lint (or "no trace flags"). It then rebuilds `.vmodel/docs/v-view.html`.
