---
name: aid-board
description: GitHub Project (v2) board for A.I.D. Setup, status, one-step moves, trail comments, and signed blocks. Agent-invoked from /board and by Board Keeper or the A.I.D runner. Not a slash duplicate of other commands.
user-invocable: false
---

# Board (GitHub Project v2)

The board is a **view** of SSOT plus GitHub. It is not the source of truth. Only **Board Keeper** and **A.I.D** (the `/usr` runner) write to it. Other roles ask Board Keeper.

Store ids in `.vmodel/board.json`. Append one line per comment to `.vmodel/board-log.jsonl` (time, issue, req, from, to, phase, who, changed, proof, comment_url). ssot-gate does not write these files.

## Setup (`/board setup`)

From the project root (needs `gh` auth). GraphQL via `gh api graphql` if field options are missing. GitHub MCP is the fallback when `gh` is not installed.

```
python3 <plugin>/scripts/vmodel_board.py .vmodel setup
```

Creates or finds a project titled `A.I.D board`. Status options: Backlog, Ready, In progress, In review, Done. Writes `.vmodel/board.json`.

## Status, apply, trail

```
python3 <plugin>/scripts/vmodel_board.py .vmodel status
python3 <plugin>/scripts/vmodel_board.py .vmodel apply --proof TEXT --phase Code --who "adept ; Last Boss slice"
python3 <plugin>/scripts/vmodel_board.py .vmodel trail REQ-KTL-001
```

`--gh` reads issues and PRs. Apply moves **one column** (never skip). **No proof, no move** — report a blocker to A.I.D. Done still needs a merged PR. `/board trail REQ-ID` prints the comment chain oldest to newest.

## Events (A.I.D → Board Keeper)

Every event carries `--phase` `--who` `--changed` `--proof` `--next` (or `--json '{...}'`). A phase comment is posted even when the column does not move (header `no column change`).

```
python3 <plugin>/scripts/vmodel_board.py .vmodel event intake REQ-KTL-001 --phase Requirements --who "req-guardian ; intake" --changed USR-KTL-001,REQ-KTL-001 --proof "proposal USR-KTL-001" --next "ssot-gate Gate 1"
python3 <plugin>/scripts/vmodel_board.py .vmodel event phase REQ-KTL-001 --phase Functions --who "functional-specs ; SSOT Gate published" --changed FNC-KTL-001 --proof "baseline 2026-10-16-g1" --next system-designer
python3 <plugin>/scripts/vmodel_board.py .vmodel event pr_merged REQ-KTL-001 --gh --phase "Acceptance test" --proof "https://github.com/xWhiteSpace/aid-plugin/pull/NN"
```

Kinds: `intake` `published` `coding` `pr_open` `pr_merged` `phase`.

## Comments

Same block, always. Board Keeper signs as Board Keeper. A.I.D uses `--signer AID`.

```
python3 <plugin>/scripts/vmodel_board.py .vmodel comment 12 --req REQ-KTL-001 --phase Code --who "A.I.D ; runner" --changed UNT-KTL-001 --proof abc123 --next "test-master" --signer AID
```

Block labels (same every time): Phase done, Who, Changed, Next, Proof, Back. **Back** is the previous comment URL on that issue, or `first entry`.
