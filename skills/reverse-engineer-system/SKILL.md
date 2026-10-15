---
name: reverse-engineer-system
description: "Use when reverse-engineering: allocate functions to components and name only seams the code trace shows."
---
# Reverse engineer: system

Use when functions exist and a code trace shows which parts talk. You place functions and name seams. You do not specify line-level behavior.

## Inputs
- Published functions for this slice.
- A code trace of files that write, read, or send.

## You do
1. Put each function on the component that owns that behavior. Reuse a component if one already fits. Mint one only when the trace shows a separate part.
2. A seam exists only where the trace shows a call, a route, or a message. Name who sends and who receives.
3. If the client sends an empty body and the server rebuilds the data, the seam is the server rebuild, not the empty post.
4. A screen that only displays a stored field does not own the function that computes it.
5. Propose components, allocation, and seams to ssot-gate (write to `.vmodel/proposals/`). Do not publish.

## You do not
- Change function behavior.
- Write field lists. That is unit design.
- Invent a seam the trace does not show.
