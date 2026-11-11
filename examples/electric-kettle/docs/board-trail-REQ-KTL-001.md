# Example data — board trail for REQ-KTL-001

Offline sample of the GitHub issue comments Board Keeper would post, oldest to newest. Not a live Project. Kettle SSOT still sits at In progress (no merged PR in this repo). Run `/board trail REQ-KTL-001` to reprint from `.vmodel/board-log.jsonl`.

**REQ-KTL-001: (new) → Backlog**
**Phase done:** Requirements
**Who:** req-guardian ; intake
**Changed:** USR-KTL-001, REQ-KTL-001
**Next:** ssot-gate Gate 1
**Proof:** proposal USR-KTL-001
**Back:** first entry

— Board Keeper

**REQ-KTL-001: Backlog → Ready**
**Phase done:** Functions
**Who:** functional-specs ; SSOT Gate published
**Changed:** FNC-KTL-001, API-KTL-001
**Next:** system-designer
**Proof:** baseline 2026-10-16-g1
**Back:** example://ktl-board/1

— Board Keeper

**REQ-KTL-001: no column change**
**Phase done:** System design
**Who:** system-designer ; SSOT Gate published
**Changed:** CMP-KTL-003, INT-KTL-002
**Next:** unit-designer
**Proof:** baseline 2026-10-16-g2
**Back:** example://ktl-board/2

— Board Keeper

**REQ-KTL-001: no column change**
**Phase done:** Unit design
**Who:** unit-designer ; SSOT Gate published
**Changed:** UNT-KTL-001
**Next:** adept
**Proof:** proposal UNT-KTL-001
**Back:** example://ktl-board/3

— Board Keeper

**REQ-KTL-001: Ready → In progress**
**Phase done:** Code
**Who:** adept ; Last Boss slice
**Changed:** UNT-KTL-001; src/start_guard.py
**Next:** test-master unit tests
**Proof:** example: v0.10.1 PR
**Back:** example://ktl-board/4

— Board Keeper

**REQ-KTL-001: no column change**
**Phase done:** Unit test
**Who:** test-master ; Last Boss slice
**Changed:** TST-KTL-012
**Next:** test-master integration
**Proof:** example: v0.10.1 PR
**Back:** example://ktl-board/5

— Board Keeper

**REQ-KTL-001: no column change**
**Phase done:** Integration test
**Who:** test-master ; Last Boss slice
**Changed:** TST-KTL-007
**Next:** test-master system tests
**Proof:** example: v0.10.1 PR
**Back:** example://ktl-board/6

— Board Keeper

**REQ-KTL-001: In progress → In review**
**Phase done:** System test
**Who:** adept ; PR opened
**Changed:** TST-KTL-006
**Next:** last-boss Done challenge
**Proof:** example: v0.10.1 PR
**Back:** example://ktl-board/7

— Board Keeper

**REQ-KTL-001: In review → Done**
**Phase done:** Acceptance test
**Who:** last-boss ; PR merged
**Changed:** TST-KTL-001
**Next:** none
**Proof:** example: v0.10.1 PR merged
**Back:** example://ktl-board/8

— Board Keeper
