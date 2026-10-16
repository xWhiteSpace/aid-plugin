---
name: usr
description: State a need in plain words. Runs the full A.I.D V-model pipeline and publishes to .vmodel/. Stops if there is no confirmed TOL stack. Last Boss challenges after each stage and again before Done.
---
Run the `usr` skill from the A.I.D plugin on the user's message that follows this command.

After each pipeline stage (REQ quality, FNC, CMP/INT, UNT, code if Adept ran, tests) spawn `last-boss` to challenge that stage **before moving on**. Spawn `last-boss` again before any claim of Done. She never marks anything passed.
