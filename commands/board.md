---
name: board
description: Run the GitHub Project board for this repo's REQs (setup, status, moves, comments). Board Keeper owns it; A.I.D may comment.
---
Run the `aid-board` skill from the A.I.D plugin.

`/board setup` — create or find the Project (v2) and Status options (Backlog, Ready, In progress, In review, Done) with `gh project` / `gh issue` / `gh api graphql` (GitHub MCP if `gh` is missing). Save ids in `.vmodel/board.json`.

`/board` or `/board status` — print the desired column per REQ from `.vmodel/` (add `--gh` when issues exist).

`/board apply` — move each card one column toward that status. Never skip. Never Done without a merged PR. Post one short comment per move.

Spawn `board-keeper` for moves. The `/usr` runner may post comments through the skill signed as A.I.D.
