---
name: aid-board
description: GitHub Project (v2) board for A.I.D. Parent issue plus nine V-stage sub-issues, dashboards, system comments, and agent notes. Agent-invoked from /board and by Board Keeper or the A.I.D runner.
user-invocable: false
---

# Board (GitHub Project v2)

The board is a **view** of SSOT plus GitHub. Only **Board Keeper** writes dashboards and system comments. Engineering agents post **notes**. ssot-gate does not write board files.

One **parent** issue per `/usr` request (USR). Nine **sub-issues** (native GitHub sub-issues: `POST /repos/{owner}/{repo}/issues/{n}/sub_issues` or GraphQL `addSubIssue`), always in this order: 1 Requirements, 2 Functions, 3 System design, 4 Unit design, 5 Code, 6 Unit test, 7 Integration test, 8 System test, 9 Acceptance test. Title `USR-XXX-NNN · <stage>`. Each stage covers every node from that request. REQ ids are labels and dashboard rows, not issues. Lane skips and `empty_test_levels` still create the sub-issue, then close it as **not planned** with a one-line reason. Amendments attach to a new parent; the dashboard marks amended REQs with a link to the earlier parent.

Parent column: Backlog until stage 1 is closed; Ready when 1–4 closed; In progress when 5 is open with a branch; In review when a PR is open; Done only when all 9 are closed (completed or not planned), **every REQ acceptance test is passing**, and the PR(s) are merged.

## Setup

```
python3 <plugin>/scripts/vmodel_board.py .vmodel setup
```

## Events, trail, notes

Phase trail (system block) goes on the **stage sub-issue**; the sub-issue closes when that phase is proven. Parent gets one system summary per **column move**; parent **Back** is the latest sub-issue system comment.

```
python3 <plugin>/scripts/vmodel_board.py .vmodel event phase USR-KTL-001 --phase Functions --proof "baseline g1" --who "functional-specs ; SSOT Gate published" --changed FNC-KTL-001
python3 <plugin>/scripts/vmodel_board.py .vmodel note 101 "what I did, why, concern" --signer adept --req USR-KTL-001 --phase Code
python3 <plugin>/scripts/vmodel_board.py .vmodel trail USR-KTL-001
python3 <plugin>/scripts/vmodel_board.py .vmodel trail REQ-KTL-001 --system
python3 <plugin>/scripts/vmodel_board.py .vmodel trail USR-KTL-001 --notes
```

`/board trail` walks **parent then sub-issues in stage order**. Backtrack reads **system** comments only.

## Two comment kinds

1. **Dashboard** (`<!-- aid-dashboard -->`) — first comment on parent and on each sub-issue, **edited in place** (never reposted). Parent: USR + request, column, REQ table (id, sentence, stage reached, acceptance TST, proof, earlier parent), table of 9 stages, PR, updated time. Sub-issue: stage, owner, status, node ids in scope with status, proof, gate, parent link.
2. **System** (`<!-- aid-system -->`, starts with `[system]`) — machine trail block for column move, stage open/close, gate, PR, test run. Board Keeper / this script.
3. **Note** (`<!-- aid-note -->`) — free plain words, signed with the agent name. Every engineering agent posts at least one when it finishes its stage (`note <issue> <text> --signer <agent>`). Last Boss notes include challenge and verdict.

`.vmodel/board-log.jsonl` fields include `usr`, `reqs`, `stage` and `sub_issue`. `/board trail` accepts a USR or REQ id (REQ resolves to its parent).
