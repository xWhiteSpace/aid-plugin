---
name: reverse-engineer-tests
description: "Use when reverse-engineering: design tests from published units, not from source alone."
---
# Reverse engineer: tests

Use when units for a catch-up slice are published. You design tests from those units. Passing tests are not evidence until last-boss accepts them.

## You do
1. Read the published unit: fields, inputs, return, and the requirement it implements.
2. One test intent per observable rule. Include the case the unit says does not count.
3. Name the input and the expected output. Do not copy a whole file into the test plan.
4. If the unit says a value is stored and another is computed, test them separately.
5. Propose test cases to ssot-gate (write to `.vmodel/proposals/`). Do not mark them passed.
6. Test code that implements a published TST carries `@trace TST-{PROJECT}-NNN` in the language TOL `comment_syntax`. No explanatory comments.

## You do not
- Treat the current source as the spec when it disagrees with the published unit. Report the disagreement.
- Invent a rule the unit does not state.
- Close evidence. last-boss does that.
