---
name: aid-board
description: GitHub Project (v2) board for A.I.D. Setup, status, one-step moves, and signed comments. Agent-invoked from /board and by Board Keeper or the A.I.D runner. Not a slash duplicate of other commands.
user-invocable: false
---

# Board (GitHub Project v2)

The board is a **view** of SSOT plus GitHub. It is not the source of truth. Only **Board Keeper** and **A.I.D** (the `/usr` runner) write to it. Other roles ask Board Keeper.

Store ids in `.vmodel/board.json` (project number, Status field, option ids, REQ→issue map). ssot-gate does not write this file.

## Setup (`/board setup`)

From the project root (needs `gh` auth). GraphQL via `gh api graphql` if field options are missing. GitHub MCP is the fallback when `gh` is not installed.

```
python3 <plugin>/scripts/vmodel_board.py .vmodel setup
```

Creates or finds a project titled `A.I.D board`. Status options: Backlog, Ready, In progress, In review, Done. Writes `.vmodel/board.json`.

## Status and apply

```
python3 <plugin>/scripts/vmodel_board.py .vmodel status
python3 <plugin>/scripts/vmodel_board.py .vmodel status --gh
python3 <plugin>/scripts/vmodel_board.py .vmodel apply
python3 <plugin>/scripts/vmodel_board.py .vmodel apply --gh
```

`--gh` reads issues and PRs. `--apply` moves **one column** toward the desired status (never skip). New cards start on Backlog. Done is refused without a merged PR.

## Events (A.I.D → Board Keeper)

```
python3 <plugin>/scripts/vmodel_board.py .vmodel event intake REQ-KTL-001
python3 <plugin>/scripts/vmodel_board.py .vmodel event published REQ-KTL-001
python3 <plugin>/scripts/vmodel_board.py .vmodel event coding REQ-KTL-001
python3 <plugin>/scripts/vmodel_board.py .vmodel event pr_open REQ-KTL-001 --gh
python3 <plugin>/scripts/vmodel_board.py .vmodel event pr_merged REQ-KTL-001 --gh
```

Then `apply --gh` if the next column is allowed.

## Comments

```
python3 <plugin>/scripts/vmodel_board.py .vmodel comment 12 "plain words here"
python3 <plugin>/scripts/vmodel_board.py .vmodel comment 12 "plain words here" --signer AID
```

Board Keeper signs as Board Keeper. A.I.D uses `--signer AID`.
