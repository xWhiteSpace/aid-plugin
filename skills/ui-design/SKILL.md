---
name: ui-design
description: Design every user-facing screen before Adept writes UI code. Layout, visual hierarchy, spacing and type scale, colour and contrast (WCAG AA), every state, keyboard/accessibility, responsive breakpoints. Language- and framework-agnostic; follows the confirmed TOL stack. Record the design in UNT fields or an SSOT doc; code must follow it. Use before any screen, page, or visible control is implemented.
---

# UI design (before any screen is coded)

Adept follows this skill **before** writing or editing user-facing UI. There is no separate UI agent. Unit-designer records durable fields; Adept may also write an SSOT design doc. Last Boss reviews the running UI against this design; she does not invent it.

Skip this skill when the published UNT is not a screen, page, dialog, or visible control (for example firmware or a pure function with no presentation).

## Stack gate

Load `.vmodel/registries/tol.json`. Confirmed `language` is required; use `framework` when it is not `none`. Do not pick a UI library, CSS tool, icon set, or design kit that is not in the TOL catalog. Do not infer a stack from file extensions or from examples in this plugin.

## 1. Design first (do not code yet)

Produce a design for the exact UNT (or slice of UNTs) you are about to implement. Cover every item below. If any item is unknown, **stop** and ask; do not fill it from taste.

### Layout
Where each region sits (header, main, aside, footer, overlays). What is primary vs supporting. Alignment, grouping, and density. What is hidden until needed.

### Visual hierarchy
What the eye hits first, second, third. Size, weight, contrast, and position that encode importance. One primary action per view unless the published UNT says otherwise.

### Spacing and type scale
A spacing scale (for example 4 / 8 / 12 / 16 / 24 / 32) and a type scale (for example caption / body / subtitle / title) with sizes and line-height. Name the scale; do not sprinkle ad-hoc pixels.

### Colour and contrast
Foreground, background, border, accent, danger, success, disabled, and focus colours. Every text and meaningful icon on its background must meet **WCAG 2.2 AA** (4.5:1 normal text, 3:1 large text and UI components). State the ratio you are targeting; do not ship colour that fails AA.

### Every state
Design each of these, even if the happy path is simple:

| State | What the user sees and can do |
|---|---|
| empty | No data yet; how to start |
| loading | In-progress; what stays interactive |
| error | Failure; how to recover |
| hover | Pointer affordance (and the no-hover equivalent) |
| focus | Keyboard focus ring; visible, not colour-only |
| disabled | Why it is inert; not the only cue as colour |

Add other states the UNT names (selected, dirty, success, offline).

### Keyboard and accessibility
Tab order, focus move on open/close, Enter/Escape/Arrow behaviour, labels, names, roles, and live regions. Text is not information-only-in-colour. Hit targets are usable. Images and icons that convey meaning have a text alternative. Do not rely on pointer-only gestures.

### Responsive breakpoints
At least three widths the TOL/product needs (for example a narrow viewport, a mid viewport, a wide viewport). For each: layout changes, what collapses or stacks, what stays reachable. Do not design desktop-only and hope.

## 2. Record the design (SSOT)

Do not keep the design only in chat. Persist it in **one** of:

1. **UNT fields** (preferred). Ask `unit-designer` to propose an amend that sets `ui` on the published UNT (see `references/vmodel-schema.md`). Adept does not write registries.
2. **SSOT doc.** Write `.vmodel/docs/<PROJECT>/ui/<UNT-id>.md` with the same headings as §1. `/docs` does not own this file; do not put it in a generated Mermaid path.

The record must be enough for Last Boss to review without asking you what you meant: layout, hierarchy, scales, colour + AA contrast, every state, keyboard/accessibility, breakpoints.

If the published UNT already has `ui` (or a doc) and it is wrong or incomplete, **stop**. Report it; do not code a different design and do not silently overwrite.

## 3. Then code — follow the record

Implement only what the recorded design and the published UNT describe. Names and structure match the design (regions, states, type/spacing tokens). No explanatory comments; `@trace UNT-{PROJECT}-NNN` only on implementing functions/modules, in the language TOL `comment_syntax`.

If implementation cannot match the design (framework limit, missing token, contradictory UNT), **stop** and report; do not invent a third design in code.

## Never

- Code a user-facing screen before the design is recorded.
- Add a UI agent, a new kind, or a private style fork (`STD` / `VOC` stay with Researcher).
- Guess a framework, component library, or palette because it is common.
- Treat a mock or screenshot as published truth unless it is attached to the UNT or the SSOT doc.
- Skip empty / loading / error / focus / disabled because the demo uses only the happy path.
- Claim WCAG AA without stating contrast for text and controls.
