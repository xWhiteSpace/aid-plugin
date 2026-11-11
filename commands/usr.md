---
name: usr
description: State a need in plain words. Imagine the use first, then run only the V-model effort that use earns. Publishes to .vmodel/. Stops if there is no confirmed TOL stack.
---
Run the `aid-usr-flow` skill from the A.I.D plugin on the user's message that follows this command.

Before any gate plan, run **Imagine the use** (`aid-curiosity-imagination`). Write `effort` (lane `tiny` 2 / `small` 4 / `standard` 7 / `large` 11 gates) on the USR/REQ. Copy only the pipeline steps that lane earned. Words like "just" or "quick" mean imagine small. After Gate 1, run `aid-ssot-slice` for each REQ. Hand `board-keeper` the matching board event with proof (intake → Backlog, published → Ready, coding → In progress, open PR → In review, merged PR + proven → Done; every V phase posts the trail block). Per-stage Last Boss only when the lane earns it; full-graph Last Boss at design-complete and Done when those gates are in the lane. She never marks anything passed. Publish lint and `/v-view` stay whole-project.
