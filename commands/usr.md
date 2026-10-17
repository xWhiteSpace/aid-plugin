---
name: usr
description: State a need in plain words. Runs the A.I.D V-model pipeline from a lean SSOT slice and publishes to .vmodel/. Stops if there is no confirmed TOL stack. Last Boss light-checks each stage slice; full-graph challenge at design-complete and Done.
---
Run the `aid-usr-flow` skill from the A.I.D plugin on the user's message that follows this command.

After Gate 1, run `aid-ssot-slice` for each REQ and hand that JSON to every later role. A role may ask `ssot-gate` for a wider slice or the full graph. After each pipeline stage (REQ quality, FNC, CMP/INT, UNT, code if Adept ran, tests) spawn `last-boss` for a **light slice check** before moving on. Spawn `last-boss` on the **full graph** only at design-complete (after Gate 2) and before any claim of Done. She never marks anything passed. Publish lint and `/v-view` stay whole-project.
