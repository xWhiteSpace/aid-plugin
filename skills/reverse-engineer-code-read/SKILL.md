---
name: reverse-engineer-code-read
description: "Use when reverse-engineering an existing product: read code and report variables, writers, and readers without publishing."
---
# Reverse engineer: code read

Use when an existing product must be understood before new work. The product already exists. You read it. You do not become the source of truth.

## You do
1. Read only the files named in the ask, plus the hops those files actually call.
2. For each behavior, list the real symbols: variable or function name, the file that writes it, the file that reads it, and the payload field if one is stored.
3. Separate a computed value from a stored snapshot when both exist. Say which one each screen uses.
4. Follow a hop if the use is in another file. Do not stop early and call it unused.
5. If a search returns nothing, or you did not open the file, write "not seen". Do not treat a failed search as proof.

## You do not
- Change the repo.
- Publish requirements, functions, components, or units.
- Invent a requirement, a user, or a reason.
- Decide whether something is a feature. req-guardian does that.
- Draw the map. ssot-gate publishes the map from accepted design.

## Reply
A trace only: symbols, writers, readers, files, and not-seen items. No design ids unless the ask already named them as parents.
