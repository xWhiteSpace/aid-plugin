# Reuse-scan: keep-warm duration (KTL)

Calendar-like scheduling for kettle timers is overkill. Published facts: REQ-KTL-004 (hold 80 ± 5 °C for 30 min), FNC-KTL-004, UNT-KTL-004. Duration is a span, not a calendar event. Possibilities labelled as such.

## Curiosity

Unknown: whether keep-warm needs wall-clock dates, time zones, or recurrence (no USR says so). Question that would change the pick: is the 30 min a timedelta, or a scheduled date?

## Imagination (possible futures)

**A — Language stdlib.** World: `datetime.timedelta` / integer seconds on the confirmed Python TOL. Risk: none for a single span. Wrong if a USR asks for calendar recurrence.

**B — Calendar / scheduler library.** World: extra TOL `library`, jobs, time zones. Risk: invents product surface. Wrong unless a published USR needs appointments.

**C — Hand-rolled date math.** World: custom epoch/leap logic. Risk: reinvented wheel; no recorded reason to skip A.

## Intelligence

- **Chosen:** A
- **Reason:** REQ-KTL-004 is a 30 min hold. Stdlib fits the TOL; B is overkill; C has no reuse-scan reason.
- **Predicted:** No calendar TOL/`library` for KTL timers.
- **Check:** Last Boss flags a scheduler or hand-rolled date engine with no `decision`.

```text
decision:
  question: How should keep-warm measure 30 min?
  options: [A-stdlib, B-calendar, C-handroll]
  chosen: A-stdlib
  reason: Span only; Python stdlib; no calendar USR.
  rejected:
    - { id: B-calendar, why: scheduling library is overkill for a timer }
    - { id: C-handroll, why: reinvented wheel; no reason to skip stdlib }
  predicted: Duration uses stdlib or seconds; no calendar package.
  check: no KTL TOL library/api for calendar; no hand-rolled date engine
```
