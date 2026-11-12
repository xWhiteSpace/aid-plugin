---
name: board
description: Run the GitHub Project board for this repo's REQs (setup, status, moves, comments). Board Keeper owns it; A.I.D may comment.
---
Run the `aid-board` skill from the A.I.D plugin.

`/board setup` — create or find the Project (v2) and Status options (Backlog, Ready, In progress, In review, Done) with `gh project` / `gh issue` / `gh api graphql` (GitHub MCP if `gh` is missing). Save ids in `.vmodel/board.json`.

`/board` or `/board status` — print the desired column per REQ from `.vmodel/` (add `--gh` when issues exist).

`/board apply` — one column toward the parent status derived from sub-issues. Never skip. Never Done without a merged PR. **No proof, no move.**

`/board trail REQ-ID` — parent then stage sub-issues (`--system` or `--notes` to filter). Backtrack reads system comments only.

Spawn `board-keeper` for moves. Engineering agents post notes with `aid-board note <issue> <text> --signer <agent>`.
