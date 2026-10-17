# Curiosity → Imagination → Intelligence: temperature display (KTL)

Worked loop on a real kettle choice. Published facts only: USR-KTL-001..003, REQ-KTL-001..004, FNC-KTL-002..004 (`water_temp_c` is a control input). No user asked to see a number. Possibilities are labelled as such.

## Curiosity

Unknown / assumed:

- Whether any stakeholder needs to *see* water temperature (no USR says so).
- Whether a display would change boil, shut-off, boil-dry, or keep-warm acceptance (those already use °C in the REQ).
- Cost, power, and readability of a display (not in SSOT — do not invent figures).

Questions that would change the decision:

- Did a user ask to read live °C, or only to boil / stay safe / keep warm?
- Would a wrong displayed number fail a published REQ, or only confuse?

Edge / views: tea drinker (USR-KTL-003) cares that water stays warm, not that a digit is shown; parent (USR-KTL-002) cares about shut-off, not a readout.

## Imagination (possibilities)

**A — No user-facing temperature.** World: `water_temp_c` stays internal (FNC-KTL-002..004). Risk: a later "show the heat" ask needs a new USR/REQ. Wrong if a published USR requires a visible temperature.

**B — Numeric °C on a panel.** World: a new display UNT/CMP, extra TST for the reading. Risk: invents a need; no acceptance for accuracy exists. Wrong if we mint UI with no USR/REQ.

**C — Band LEDs (cold / heating / ready).** World: coarse state, not a number. Risk: "ready" is already implied by shut-off and keep-warm. Wrong if users need a value the bands cannot give — and no such USR is published.

## Intelligence

- **Chosen:** A
- **Reason:** Every published need is already met without a readout. B and C add product surface that no USR/REQ asks for.
- **Rejected:** B — no accuracy REQ, would be a design dressed as a need. C — redundant with existing boil / keep-warm behaviour.
- **Predicted:** No temperature-display USR/REQ/UNT appears until a user asks to see heat.
- **Check:** `usr.json` / `req.json` still have no display need; Last Boss refuses a display UNT with no parent REQ.

```text
decision:
  question: Show live water temperature to the user?
  options: [A-none, B-numeric, C-bands]
  chosen: A-none
  reason: Published USR/REQ already close boil, safety, and keep-warm without a readout.
  rejected:
    - { id: B-numeric, why: no USR/REQ for a visible °C }
    - { id: C-bands, why: state already signalled by shut-off and keep-warm }
  predicted: No display node until a user asks to see heat.
  check: registries have no temperature-display USR/REQ/UNT
```
