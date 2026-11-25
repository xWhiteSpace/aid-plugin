---
name: aid-board
description: GitHub Project (v2) for A.I.D. The Issue Manager empties Backlog. Parent issue plus the process sub-issues A.I.D names. Agent-invoked from /issue-manager.
user-invocable: false
---

# Board (GitHub Project v2)

The board is a **view** of SSOT plus GitHub. Only the **Issue Manager** writes dashboards, system comments, and Workflow Status. Engineer AI Agents post signed notes. They do not move a card.

The six Engineer AI Agents and the sub-issues they own:

- `req-guardian` — SYS.2, SWE.1
- `system-designer` — SYS.3, SWE.2
- `unit-designer` and `adept` — SWE.3, one shared sub-issue
- `test-master` — SWE.4, SWE.5, SWE.6, SYS.4, SYS.5. Test Engineer on In review. Black box: What, Why, Criteria, and the result. Does not look at code.
- `functional-specs` notes on SYS.2 and SYS.3 when that degree opens them. No sub-issue of its own.

`ssot-gate` publishes, `researcher` briefs, and `tools-manager` approves tools. They may post a signed note. They do not change Workflow Status. Last Boss and the Test Engineer may raise an issue. A.I.D tells the Issue Manager, and that issue starts in Backlog.

A parent is SYS.1 (requirement) or SUP.9 (fix). Sub-issues open only for the processes A.I.D names, in this order: SYS.2, SYS.3, SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6, SYS.4, SYS.5. Title `USR-XXX-NNN · SYS.2 System Requirements Analysis`. A process not on the list is a dashboard row, not an issue. VAL.1 is Criteria on the parent.

Workflow Status: Backlog, Ready, In progress, In review, Done. Never skip. No proof, no move. The proof is a `/gate-` comment whose first line is the token. The Action calls this script. Agents do not set the column themselves.

- `/gate-Parent-accept` — A.I.D. Does not leave Backlog.
- `/gate-Parent-breakdown` — A.I.D, with the process list. Opens those sub-issues and moves the parent and the next sub-issue to Ready.
- `/gate-Sub-issue-start` — the owning Engineer AI. Sub-issue and parent go to In progress.
- `/gate-Sub-issue-review-accept` — Test Engineer. Pass moves the sub-issue to Done. `fail` opens a new Backlog issue linked to that comment.
- `/gate-PR-accept` — Test Engineer, on the pull request. Merges only when every opened sub-issue is already Done, then the parent can be Done.

## Commands

```
python3 <plugin>/scripts/vmodel_board.py .vmodel setup
python3 <plugin>/scripts/vmodel_board.py .vmodel check --body "..." --allowed SWE.3,SWE.4
python3 <plugin>/scripts/vmodel_board.py .vmodel attach 12 USR-APP-001 --kind Requirement --processes SWE.3,SWE.4 --what "Boil water"
python3 <plugin>/scripts/vmodel_board.py .vmodel gate --body "/gate-Parent-breakdown" --issue 12 --signer AID
python3 <plugin>/scripts/vmodel_board.py .vmodel note 101 "what I did, why, concern" --signer adept --req USR-APP-001 --phase SWE.3
python3 <plugin>/scripts/vmodel_board.py .vmodel trail USR-APP-001
```

## Comments

1. **Dashboard** (`<!-- aid-dashboard -->`) — edited in place. Parent lists all ten processes. A process with no sub-issue says so.
2. **System** (`<!-- aid-system -->`, starts with `[system]`) — Issue Manager. Column moves and gate results.
3. **Note** (`<!-- aid-note -->`) — one engineer, 1–3 lines, signed. Never edit another agent's comment.

`.vmodel/board-log.jsonl` copies the same lines. Signer label is Issue Manager.
