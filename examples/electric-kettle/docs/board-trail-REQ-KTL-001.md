# Example data — board trail for REQ-KTL-001

Offline sample. Not a live GitHub Project. Parent issue plus nine stage sub-issues (`REQ-KTL-001 · <stage>`). Dashboards (`<!-- aid-dashboard -->`) are edited in place and are not in this trail. System comments (`<!-- aid-system -->` `[system]`) are the backtrack. Notes (`<!-- aid-note -->`) are agent prose. `/board trail REQ-KTL-001` prints parent then stages; add `--system` or `--notes`.

Live SSOT/board column is **In progress** (stages 1–4 closed, Code open). The Done parent line below is example data.

## Parent (column moves)

<!-- aid-system -->
[system]
**REQ-KTL-001: (new) → Backlog**
**Phase done:** Requirements
**Who:** req-guardian ; intake
**Changed:** USR-KTL-001, REQ-KTL-001
**Next:** ssot-gate Gate 1
**Proof:** proposal USR-KTL-001
**Back:** first entry

— Board Keeper

<!-- aid-system -->
[system]
**REQ-KTL-001: Backlog → Ready**
**Phase done:** Unit design
**Who:** unit-designer ; SSOT Gate published
**Changed:** UNT-KTL-001
**Next:** adept
**Proof:** proposal UNT-KTL-001
**Back:** example://ktl-board/s4

— Board Keeper

<!-- aid-system -->
[system]
**REQ-KTL-001: Ready → In progress**
**Phase done:** Code
**Who:** adept ; Last Boss slice
**Changed:** UNT-KTL-001; src/start_guard.py
**Next:** test-master unit tests
**Proof:** example: v0.11.0 PR
**Back:** example://ktl-board/s5

— Board Keeper

## Sub-issue `REQ-KTL-001 · Code`

<!-- aid-system -->
[system]
**REQ-KTL-001: no column change**
**Phase done:** Code
**Who:** adept ; Last Boss slice
**Changed:** UNT-KTL-001; src/start_guard.py
**Next:** test-master unit tests
**Proof:** example: v0.11.0 PR
**Back:** first entry

— Board Keeper

<!-- aid-note -->
Implemented start_guard in src/start_guard.py. Why: published UNT-KTL-001. Concern: no hardware interlock in this tree.

— Adept

The other eight stages follow the same pair (system block on the sub-issue, plus a signed note from the owner). Last Boss on Acceptance test records challenge and verdict. Full chain: `.vmodel/board-log.jsonl`.
