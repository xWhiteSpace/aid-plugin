#!/usr/bin/env python3
"""Lint a .vmodel/ SSOT tree. Reports inconsistencies, redundancy, unconnected
variables, orphans, gaps and isolation breaks. Optional --code scan for
@trace UNT-… tags.

Usage: python3 vmodel_lint.py .vmodel [--write] [--code <dir>]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import (EDGE_TYPES, ID_RE, by_kind, in_edges, load,  # noqa: E402
                           out_edges, project_of)

SKIP_DIRS = {".git", "node_modules", ".vmodel", "__pycache__", ".venv", "venv"}
SOURCE_EXT = {
    ".py", ".c", ".h", ".cc", ".cpp", ".hpp", ".cxx",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".go", ".rs", ".rb", ".swift", ".kt", ".kts",
    ".cs", ".m", ".mm", ".scala", ".php", ".lua",
}
# Any @trace … token (well-formed UNT checked separately)
TRACE_ANY_RE = re.compile(r"@trace\s+(\S+)")


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
    return {"total": len(flags), "by_category": counts, "flags": flags, "nodes": nodes}


def scan_code(code_dir, nodes):
    """Return list of code-trace flags."""
    flags = []
    tagged = set()  # published UNT ids that appear in at least one well-formed tag

    def flag(nid, msg):
        flags.append({"category": "code_trace", "id": nid, "message": msg})

    if not code_dir or not os.path.isdir(code_dir):
        flag("(code)", "code dir missing or not a directory: %s" % code_dir)
        return flags

    for dirpath, dirnames, filenames in os.walk(code_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in SOURCE_EXT:
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, code_dir)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError as e:
                flag(rel, "unreadable: %s" % e)
                continue
            ssot_projects = {n.get("project") for n in nodes.values() if n.get("project")}
            for m in TRACE_ANY_RE.finditer(text):
                token = m.group(1).rstrip(",;")
                um2 = re.match(r"^(UNT-[A-Z0-9]{2,5}-\d{3,})$", token)
                if not um2:
                    flag(rel, "malformed tag @trace %s" % token)
                    continue
                uid = um2.group(1)
                proj = project_of(uid)
                if proj and ssot_projects and proj not in ssot_projects:
                    flag(uid, "orphan tag in %s (other project)" % rel)
                    continue
                node = nodes.get(uid)
                if node is None or node.get("kind") != "UNT":
                    flag(uid, "orphan tag in %s (not a published UNT)" % rel)
                    continue
                if node.get("status") == "retired":
                    flag(uid, "orphan tag in %s (UNT is retired)" % rel)
                    continue
                tagged.add(uid)

    for u in by_kind(nodes, "UNT"):
        if u.get("status") == "retired":
            continue
        if u["id"] not in tagged:
            flag(u["id"], "untagged unit")

    return flags


def parse_args(argv):
    root = None
    code_dir = None
    write = False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--write":
            write = True
        elif a == "--code":
            i += 1
            if i >= len(argv):
                print("error: --code needs a directory", file=sys.stderr)
                sys.exit(2)
            code_dir = argv[i]
        elif a.startswith("-"):
            print("unknown option: %s" % a, file=sys.stderr)
            sys.exit(2)
        else:
            root = a
        i += 1
    return root, code_dir, write


def main():
    root, code_dir, write = parse_args(sys.argv)
    if not root:
        print(__doc__)
        return 2
    result = lint(root)
    nodes = result.pop("nodes")

    trace_flags = []
    if code_dir is not None:
        trace_flags = scan_code(code_dir, nodes)
        result["trace_flags"] = trace_flags
        result["trace_total"] = len(trace_flags)
        for fl in trace_flags:
            result["flags"].append(fl)
            result["by_category"][fl["category"]] = result["by_category"].get(fl["category"], 0) + 1
        result["total"] = len(result["flags"])

    if write:
        os.makedirs(os.path.join(root, "lint"), exist_ok=True)
        with open(os.path.join(root, "lint", "latest.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    if result["total"] == 0 and not trace_flags:
        print("Lint: no flags.")
    else:
        # Graph/registry flags only
        graph_flags = [fl for fl in result["flags"] if fl["category"] != "code_trace"]
        if not graph_flags:
            print("Lint: no flags.")
        else:
            cats = {}
            for fl in graph_flags:
                cats[fl["category"]] = cats.get(fl["category"], 0) + 1
            print("Lint: %d flag(s) %s" % (len(graph_flags), json.dumps(cats)))
            for fl in graph_flags:
                print("  [%s] %s: %s" % (fl["category"], fl["id"], fl["message"]))

    if code_dir is not None:
        print("Code trace:")
        if not trace_flags:
            print("  no trace flags")
        else:
            for fl in trace_flags:
                print("  [%s] %s: %s" % (fl["category"], fl["id"], fl["message"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
