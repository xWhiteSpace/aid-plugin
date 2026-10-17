#!/usr/bin/env python3
"""Slice a .vmodel/ SSOT tree around one root id.

Given USR/REQ/FNC/API/CMP/INT/UNT/TST, write a small offline JSON
neighborhood: the node, undirected neighbors within N hops (default 2)
on graph/edges.json, chain-adjacent INT/TST, project TOL, registry
entries, and open lint flags for those ids only. No network.

Usage: python3 vmodel_slice.py .vmodel <ID> [--code <dir>] [--out path] [--hops 2]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import ID_RE, by_kind, load, project_of  # noqa: E402
from vmodel_lint import collect_traces, lint, scan_code  # noqa: E402

ROOT_KINDS = {"USR", "REQ", "FNC", "API", "CMP", "INT", "UNT", "TST"}
DEFAULT_HOPS = 2
MAX_HOPS = 8


def adjacency(edges):
    adj = {}
    for e in edges:
        a, b = e.get("from"), e.get("to")
        if not a or not b:
            continue
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    return adj


def neighborhood(adj, root, hops):
    seen = {root: 0}
    queue = [root]
    i = 0
    while i < len(queue):
        cur = queue[i]
        i += 1
        d = seen[cur]
        if d >= hops:
            continue
        for nxt in adj.get(cur, []):
            if nxt not in seen:
                seen[nxt] = d + 1
                queue.append(nxt)
    return seen


def attach_chain(nodes, edges, ids):
    extra = set()
    for n in nodes.values():
        if n.get("kind") != "INT" or n.get("id") in ids:
            continue
        fnc, api = n.get("implements_fnc"), n.get("carries_api")
        if (fnc and fnc in ids) or (api and api in ids):
            extra.add(n["id"])
            if n.get("from_cmp"):
                extra.add(n["from_cmp"])
            if n.get("to_cmp"):
                extra.add(n["to_cmp"])
    for e in edges:
        typ = e.get("type")
        src, dst = e.get("from"), e.get("to")
        if typ == "verifies" and dst in ids and src:
            extra.add(src)
        if typ == "uses" and src in ids and dst:
            extra.add(dst)
    return extra


def project_tol(nodes, project):
    out = set()
    if not project:
        return out
    for t in by_kind(nodes, "TOL", project):
        if t.get("status") != "retired":
            out.add(t["id"])
    return out


def grow_ids(nodes, edges, seed, hops):
    adj = adjacency(edges)
    dist = neighborhood(adj, seed, hops)
    ids = set(dist)
    ids |= project_tol(nodes, project_of(seed) or (nodes.get(seed) or {}).get("project"))
    for _ in range(4):
        extra = attach_chain(nodes, edges, ids) - ids
        extra = {i for i in extra if i in nodes}
        if not extra:
            break
        ids |= extra
    return ids, dist


def filter_lint(flags, ids, project):
    keep = []
    for fl in flags:
        fid = fl.get("id")
        if fid in ids or (project and fid == project):
            keep.append({
                "category": fl.get("category"),
                "id": fid,
                "message": fl.get("message"),
            })
    return keep


def slice_ssot(root, nid, hops=DEFAULT_HOPS, code_dir=None):
    nodes, edges, meta = load(root)
    if nid not in nodes:
        raise SystemExit("error: %s is not in the published registries" % nid)
    node = nodes[nid]
    kind = node.get("kind")
    if kind not in ROOT_KINDS:
        raise SystemExit("error: root must be one of %s" % ", ".join(sorted(ROOT_KINDS)))
    ids, dist = grow_ids(nodes, edges, nid, hops)
    project = node.get("project") or project_of(nid)
    slice_nodes = {}
    for i in sorted(ids):
        n = nodes.get(i)
        if n:
            slice_nodes[i] = n
    slice_edges = []
    for e in edges:
        a, b = e.get("from"), e.get("to")
        if a in ids and b in ids:
            slice_edges.append({"from": a, "to": b, "type": e.get("type")})
    lint_res = lint(root)
    flags = list(lint_res.get("flags") or [])
    if code_dir is not None:
        flags.extend(scan_code(code_dir, nodes))
    traces = []
    if code_dir:
        traces = [t for t in collect_traces(code_dir) if t.get("id") in ids]
    full_n = len(nodes)
    full_e = len(edges)
    return {
        "root": nid,
        "hops": hops,
        "project": project,
        "graph_version": meta.get("graph_version"),
        "ids": sorted(ids),
        "hop": {i: dist[i] for i in sorted(dist) if i in ids},
        "nodes": slice_nodes,
        "edges": slice_edges,
        "tol": sorted(i for i in ids if (nodes.get(i) or {}).get("kind") == "TOL"),
        "lint": filter_lint(flags, ids, project),
        "traces": traces,
        "stats": {
            "slice_nodes": len(slice_nodes),
            "slice_edges": len(slice_edges),
            "full_nodes": full_n,
            "full_edges": full_e,
        },
        "may_widen": (
            "Ask ssot-gate for a wider slice (--hops N) or the full graph "
            "(registries + graph/edges.json). Publish lint and /v-view stay "
            "whole-project."
        ),
    }


def registries_bytes(root):
    reg = os.path.join(root, "registries")
    total = 0
    if not os.path.isdir(reg):
        return total
    for name in os.listdir(reg):
        if name.endswith(".json"):
            total += os.path.getsize(os.path.join(reg, name))
    return total


def parse_args(argv):
    root = None
    nid = None
    code_dir = None
    out = None
    hops = DEFAULT_HOPS
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--code":
            i += 1
            if i >= len(argv):
                print("error: --code needs a directory", file=sys.stderr)
                sys.exit(2)
            code_dir = argv[i]
        elif a == "--out":
            i += 1
            if i >= len(argv):
                print("error: --out needs a path", file=sys.stderr)
                sys.exit(2)
            out = argv[i]
        elif a == "--hops":
            i += 1
            if i >= len(argv):
                print("error: --hops needs an integer", file=sys.stderr)
                sys.exit(2)
            try:
                hops = int(argv[i])
            except ValueError:
                print("error: --hops must be an integer", file=sys.stderr)
                sys.exit(2)
            if hops < 1 or hops > MAX_HOPS:
                print("error: --hops must be 1..%d" % MAX_HOPS, file=sys.stderr)
                sys.exit(2)
        elif a.startswith("-"):
            print("unknown option: %s" % a, file=sys.stderr)
            sys.exit(2)
        elif root is None:
            root = a
        elif nid is None:
            nid = a
        else:
            print("unexpected argument: %s" % a, file=sys.stderr)
            sys.exit(2)
        i += 1
    return root, nid, code_dir, out, hops


def main():
    root, nid, code_dir, out, hops = parse_args(sys.argv)
    if not root or not nid:
        print(__doc__)
        return 2
    if not ID_RE.match(nid) or nid.split("-", 1)[0] not in ROOT_KINDS:
        print("error: root id must be USR|REQ|FNC|API|CMP|INT|UNT|TST-{PROJECT}-NNN",
              file=sys.stderr)
        return 2
    data = slice_ssot(root, nid, hops=hops, code_dir=code_dir)
    data["stats"]["registries_bytes"] = registries_bytes(root)
    data["stats"]["slice_bytes"] = 0
    blob = None
    for _ in range(4):
        blob = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        n = len(blob.encode("utf-8"))
        if data["stats"]["slice_bytes"] == n:
            break
        data["stats"]["slice_bytes"] = n
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(blob)
        print(json.dumps({"slice": out, **data["stats"]}, indent=2))
    else:
        sys.stdout.write(blob)
    return 0


if __name__ == "__main__":
    sys.exit(main())
