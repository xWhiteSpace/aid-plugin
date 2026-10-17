# Imagine the use: one-button kettle light (KTL)

Intake: "just a super simple page — one button to turn the kettle light on and off." Size words mean imagine small. Not a flashlight-scale V.

## Person and moment

Someone in a dark kitchen at night, standing by the kettle, three seconds, maybe once an evening. They want to see the vessel, tap, and walk away.

## Futures of use (possibilities)

**A — Smallest honest.** One control on a tiny page (or the existing panel CMP-KTL-005). On, off. No schedule, no colour, no app account.

**B — Scene.** Timed night light, brightness, "away" mode. Needs a USR nobody spoke.

**C — Platform.** Auth, rooms, MCP device hunt. A different product.

## Done and good enough (user's side)

The light is on when they wanted it on, off when they wanted it off. They do not wait for eleven gates.

## Effort

Default smallest honest. No named grow-for (not safety-critical beyond existing boil-dry; not many users; not long-life platform).

```text
effort:
  use: night kitchen, ~3 s, about once an evening
  done_enough: tap on, tap off; can see the kettle
  futures: [A-one-button, B-scene, C-platform]
  lane: tiny
  gates: 2
  stages: [USR, REQ, one UNT if implementing]
  reason: one control, one moment; A is the honest use
  grow_for: null
```

Chosen: **tiny, 2 gates** (Gate 1 · Gate Done). Skip unused V layers, per-stage Last Boss, and tool/MCP hunting. Adept: `ui-design` + installed Python TOL only. Last Boss would flag a standard/large run as **over-built for its future**.
