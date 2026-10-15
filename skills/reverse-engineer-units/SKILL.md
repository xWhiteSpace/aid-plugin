---
name: reverse-engineer-units
description: "Use when reverse-engineering: write atomic unit fields from a code trace for one allocated component."
---
# Reverse engineer: units

Use when a component is allocated and a code trace shows the atomic data. You write the unit interface. You do not restate the whole feature.

## Inputs
- The component and the functions allocated to it.
- A code trace of the fields actually assigned, passed, or rendered.

## You do
1. List each field: name, meaning, who sets it, who reads it.
2. State inputs and the return. If two values share a name but one is computed and one is stored, keep them apart.
3. State the row or record shape when the trace shows one record per pair, not per slot.
4. Ignore fields marked not seen.
5. Propose units and their links to the component and function. Do not publish.

## You do not
- Move functions between components.
- Invent a field to make the interface look complete.
- Write tests. test-master does that from the published unit.
