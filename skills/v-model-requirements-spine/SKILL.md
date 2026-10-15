---
name: v-model-requirements-spine
description: Reference for coordinating V-model / MBSE work with A.I.D. Explains the ID kinds and their owners, the design → code → prove chain, the researcher and last-boss roles, and the single SSOT publisher. Use when unsure which role owns a kind or what comes next.
---
# V-model requirements spine

## ID scheme
Format: `{KIND}-{PROJECT}-NNN`

| Kind | Owner (subagent) | Meaning | SysML analogue |
|---|---|---|---|
| `USR` | req-guardian | Stakeholder need (要求) | Stakeholder requirement |
| `REQ` | req-guardian | Requirement (要件) | «requirement» |
| `FNC` | functional-specs | Function | Activity / behavior |
| `API` | functional-specs | Interface contract | Interface block |
| `CMP` | system-designer | Component | «block» |
| `INT` | system-designer | Integration seam | Port / connector |
| `UNT` | unit-designer | Unit design | Part / operation |
| `TST` | test-master | Test case | «testCase» |
| `TOL` | adept proposes, ssot-gate publishes | Allowed tool and version | |
| `RSH` | researcher | Research brief (informs, never a requirement) | Rationale |
| `STD` | ssot-gate (adept, researcher propose) | Coding and naming standard | |
| `VOC` | ssot-gate (researcher proposes) | Vocabulary | |
| `EVD` | last-boss | Accepted evidence | «verify» result |

## Design → Code → Prove
req-guardian → functional-specs → system-designer → unit-designer → adept (code, using TOL) → test-master → last-boss. ssot-gate publishes between each step.

## Researcher
Beside every phase. Returns cited RSH briefs. Never mints USR/REQ, never publishes. A direction change needs the user's approval.

## Last Boss
Skeptic for left–right verification. Accepts evidence only from a real run (EVD).

## SSOT
One publisher, one graph, in `.vmodel/` in the project repo. Every publish is a dated baseline.

## Entry
`/usr` runs the intake filter first: project intake goes to req-guardian, research asks to researcher, and injection, unrelated or garbage is answered and never forwarded.
