---
name: issue-manager
description: Run the GitHub Project. The Issue Manager empties Backlog. It does not answer the person or classify the issue.
---
Run the `aid-board` skill from the A.I.D plugin. Spawn `issue-manager`.

`/issue-manager setup` — create a new Project (v2) with GraphQL. Rename Status to Workflow Status. The only view is a kanban named Board. Write the issue form and the gate Action into this repo. If `.vmodel/board.json` already has a `project_id`, stop and report it.

`/issue-manager check ISSUE` — read the parent body. Kind plus What, Why, When, Criteria, How, each 1–3 lines. When must be one of the ten process ids and on the list A.I.D named. Do not rewrite the body.

`/issue-manager status` — print the column per parent from `.vmodel/`.

`/issue-manager apply` — move one column when a gate comment is the proof. Never skip. No proof, no move.

`/issue-manager trail USR-ID` — parent then process sub-issues (`--system` or `--notes`).

Agents post notes. They do not move Workflow Status. The gate Action calls this manager.
