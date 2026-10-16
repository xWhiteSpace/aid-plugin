#!/usr/bin/env python3
"""Build an offline V-model debug view from a .vmodel/ SSOT tree.

Usage: python3 vmodel_vview.py .vmodel [--code <dir>] [--out path]
Default out: .vmodel/docs/v-view.html
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import load  # noqa: E402
from vmodel_lint import collect_traces, lint, scan_code  # noqa: E402

NODE_KEEP = (
    "id", "kind", "project", "title", "statement", "status", "level", "cases",
    "source_files", "acceptance", "who", "why", "from_cmp", "to_cmp",
    "carries_api", "implements_fnc", "rule", "inputs", "outputs", "fields",
    "slot", "tool", "priority", "type", "domain",
)
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vview_page.html")


def slim_node(n):
    out = {}
    for k in NODE_KEEP:
        if k in n and n[k] not in (None, "", [], {}):
            out[k] = n[k]
    out.setdefault("id", n.get("id"))
    out.setdefault("kind", n.get("kind"))
    out.setdefault("project", n.get("project"))
    out.setdefault("title", n.get("title") or n.get("id"))
    out.setdefault("status", n.get("status") or "published")
    return out


def payload(root, code_dir=None):
    nodes, edges, meta = load(root)
    lint_res = lint(root)
    flags = list(lint_res.get("flags") or [])
    if code_dir is not None:
        flags.extend(scan_code(code_dir, nodes))
    traces = collect_traces(code_dir) if code_dir else []
    projects = meta.get("projects") or sorted({
        n.get("project") for n in nodes.values() if n.get("project")
    })
    return {
        "meta": {
            "graph_version": meta.get("graph_version"),
            "source_commit": meta.get("source_commit"),
            "updated_at": meta.get("updated_at"),
            "projects": projects,
        },
        "projects": projects,
        "nodes": {nid: slim_node(n) for nid, n in nodes.items()},
        "edges": [{"from": e.get("from"), "to": e.get("to"), "type": e.get("type")}
                  for e in edges],
        "traces": traces,
        "lint": [{"category": f.get("category"), "id": f.get("id"),
                  "message": f.get("message")} for f in flags],
    }


def write_vview(root, code_dir=None, out=None):
    if not os.path.isfile(TEMPLATE):
        raise SystemExit("missing template: %s" % TEMPLATE)
    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    data = payload(root, code_dir)
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e")
    html = page.replace("__DATA__", blob)
    if not out:
        out = os.path.join(root, "docs", "v-view.html")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out, {
        "nodes": len(data["nodes"]),
        "edges": len(data["edges"]),
        "traces": len(data["traces"]),
        "lint": len(data["lint"]),
        "projects": data["projects"],
    }


def parse_args(argv):
    root = None
    code_dir = None
    out = None
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
        elif a.startswith("-"):
            print("unknown option: %s" % a, file=sys.stderr)
            sys.exit(2)
        else:
            root = a
        i += 1
    return root, code_dir, out


def main():
    root, code_dir, out = parse_args(sys.argv)
    if not root:
        print(__doc__)
        return 2
    path, summary = write_vview(root, code_dir, out)
    print(json.dumps({"v_view": path, **summary}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
