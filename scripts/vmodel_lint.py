#!/usr/bin/env python3
"""Lint a .vmodel/ SSOT tree. Reports inconsistencies, redundancy, unconnected
variables, orphans, gaps and isolation breaks.

Usage: python3 vmodel_lint.py .vmodel [--write]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import (EDGE_TYPES, ID_RE, by_kind, in_edges, load,  # noqa: E402
                           out_edges, project_of)


def walk_fields(obj, prefix=""):
    if not isinstance(obj, dict):
        return
    for k, v in obj.items():
        path = prefix + "." + k if prefix else k
        if isinstance(v, dict) and not isinstance(v.get("type"), str):
            yield from walk_fields(v, path)
        else:
            yield path, v


def lint(root):
    nodes, edges, _ = load(root)
    flags = []

    def flag(cat, nid, msg):
        flags.append({"category": cat, "id": nid, "message": msg})

    # Id and project consistency
    for nid, n in nodes.items():
        m = ID_RE.match(nid)
        if not m:
            flag("inconsistency", nid, "id does not match {KIND}-{PROJECT}-NNN")
            continue
        if m.group(1) != n["kind"]:
            flag("inconsistency", nid, "id kind %s but registry kind %s" % (m.group(1), n["kind"]))
        if n.get("project") != m.group(2):
            flag("inconsistency", nid, "project field %r does not match id" % n.get("project"))
        if n["kind"] == "TST" and n.get("status") == "passed":
            if not in_edges(edges, nid, "evidences"):
                flag("inconsistency", nid, "status passed without an EVD evidences edge")

    # Edges
    seen = set()
    for e in edges:
        key = (e.get("from"), e.get("to"), e.get("type"))
        if key in seen:
            flag("redundancy", e.get("from"), "duplicate edge %s -%s-> %s" % (key[0], key[2], key[1]))
        seen.add(key)
        if e.get("type") not in EDGE_TYPES:
            flag("inconsistency", e.get("from"), "unknown edge type %r" % e.get("type"))
        for end in (e.get("from"), e.get("to")):
            if end not in nodes:
                flag("inconsistency", end, "edge endpoint not in registry")
        if project_of(e.get("from", "")) != project_of(e.get("to", "")):
            flag("isolation", e.get("from"), "cross-project edge to %s" % e.get("to"))

    # Redundancy: identical statements within a kind+project
    stmts = {}
    for n in nodes.values():
        s = (n.get("statement") or "").strip().lower()
        if s:
            stmts.setdefault((n["kind"], n.get("project"), s), []).append(n["id"])
    for ids in stmts.values():
        if len(ids) > 1:
            flag("redundancy", ids[0], "same statement as " + ", ".join(ids[1:]))

    # Orphans and gaps
    for n in nodes.values():
        nid, k = n["id"], n["kind"]
        if n.get("status") == "retired":
            continue
        if k == "REQ" and not out_edges(edges, nid, "derives") and not out_edges(edges, nid, "linked_from"):
            flag("orphan", nid, "REQ has no derives edge to a USR")
        if k == "REQ" and not in_edges(edges, nid, "implements"):
            flag("gap", nid, "no FNC/API implements this REQ")
        if k == "REQ" and not in_edges(edges, nid, "verifies"):
            flag("gap", nid, "no acceptance TST verifies this REQ")
        if k == "USR" and not in_edges(edges, nid, "derives"):
            flag("gap", nid, "USR has no REQ derived from it")
        if k == "FNC":
            if not out_edges(edges, nid, "implements"):
                flag("orphan", nid, "FNC implements no REQ")
            if not out_edges(edges, nid, "allocated_to"):
                flag("gap", nid, "FNC not allocated to a CMP")
            if not in_edges(edges, nid, "refines"):
                flag("gap", nid, "no UNT refines this FNC")
        if k == "UNT" and not out_edges(edges, nid, "refines"):
            flag("orphan", nid, "UNT refines nothing")
        if k == "TST" and not out_edges(edges, nid, "verifies"):
            flag("orphan", nid, "TST verifies nothing")
        if k == "CMP" and not in_edges(edges, nid, "allocated_to") and not in_edges(edges, nid, "integrates_with"):
            flag("orphan", nid, "CMP has no allocated FNC and no INT")
        if k == "INT":
            for f in ("from_cmp", "to_cmp"):
                if n.get(f) and n[f] not in nodes:
                    flag("inconsistency", nid, "%s %s not in registry" % (f, n[f]))

    # Unconnected variables: API fields never mentioned by any UNT field/input/rule
    unit_text = {}
    for u in by_kind(nodes, "UNT"):
        unit_text.setdefault(u.get("project"), []).append(json.dumps(u).lower())
    for api in by_kind(nodes, "API"):
        texts = unit_text.get(api.get("project"), [])
        slots = {"request.headers": (api.get("request") or {}).get("headers"),
                 "request.query": (api.get("request") or {}).get("query"),
                 "request.body": (api.get("request") or {}).get("body"),
                 "response.success.body": ((api.get("response") or {}).get("success") or {}).get("body")}
        for slot, obj in slots.items():
            for path, _ in walk_fields(obj or {}):
                leaf = path.split(".")[-1].lower()
                if not any(leaf in t for t in texts):
                    flag("unconnected_variable", api["id"], "%s.%s is not used by any UNT" % (slot, path))

    counts = {}
    for f in flags:
        counts[f["category"]] = counts.get(f["category"], 0) + 1
    return {"total": len(flags), "by_category": counts, "flags": flags}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = sys.argv[1]
    result = lint(root)
    if "--write" in sys.argv:
        os.makedirs(os.path.join(root, "lint"), exist_ok=True)
        with open(os.path.join(root, "lint", "latest.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    if result["total"] == 0:
        print("Lint: no flags.")
    else:
        print("Lint: %d flag(s) %s" % (result["total"], json.dumps(result["by_category"])))
        for fl in result["flags"]:
            print("  [%s] %s: %s" % (fl["category"], fl["id"], fl["message"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
