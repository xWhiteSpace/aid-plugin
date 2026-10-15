#!/usr/bin/env python3
"""Build graphical V-model docs from a .vmodel/ SSOT tree. Standard library only.

Usage: python3 vmodel_docs.py .vmodel
Writes .vmodel/docs/index.html (offline) and per-project Mermaid, trace
matrix (md + csv) and variables.json.
"""
import csv
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import by_kind, in_edges, load, out_edges  # noqa: E402
from vmodel_lint import lint, walk_fields  # noqa: E402


def mid(nid):
    return nid.replace("-", "_")


def label(n):
    t = (n.get("title") or "").replace('"', "'")
    return "%s<br/>%s" % (n["id"], t)


def req_diagram(nodes, edges, p):
    lines = ["flowchart TB"]
    for k in ("USR", "REQ"):
        for n in by_kind(nodes, k, p):
            shape = '(["«stakeholder need» %s"])' if k == "USR" else '["«requirement» %s"]'
            lines.append("  %s%s" % (mid(n["id"]), shape % label(n)))
    for n in by_kind(nodes, "REQ", p):
        for u in out_edges(edges, n["id"], "derives"):
            lines.append("  %s -->|«deriveReqt»| %s" % (mid(n["id"]), mid(u)))
    return "\n".join(lines) + "\n"


def bdd(nodes, edges, p):
    lines = ["classDiagram"]
    for c in by_kind(nodes, "CMP", p):
        lines.append("  class %s[\"%s\"] {" % (mid(c["id"]), c.get("title", c["id"])))
        lines.append("    <<block>>")
        for f in in_edges(edges, c["id"], "allocated_to"):
            lines.append("    +%s()" % mid(f))
        for u in in_edges(edges, c["id"], "refines"):
            if nodes.get(u, {}).get("kind") == "UNT":
                lines.append("    -part %s" % mid(u))
        lines.append("  }")
    for i in by_kind(nodes, "INT", p):
        if i.get("from_cmp") and i.get("to_cmp"):
            lines.append("  %s --> %s : %s" % (mid(i["from_cmp"]), mid(i["to_cmp"]), i["id"]))
    return "\n".join(lines) + "\n"


def ibd(nodes, edges, p):
    lines = ["flowchart LR"]
    for c in by_kind(nodes, "CMP", p):
        lines.append("  subgraph %s[\"«part» %s\"]" % (mid(c["id"]), c.get("title", c["id"])))
        ports = [i for i in by_kind(nodes, "INT", p) if c["id"] in (i.get("from_cmp"), i.get("to_cmp"))]
        if not ports:
            lines.append("    %s_none[ ]" % mid(c["id"]))
        for i in ports:
            side = "out" if i.get("from_cmp") == c["id"] else "in"
            lines.append("    %s_%s_%s((%s))" % (mid(c["id"]), mid(i["id"]), side, side))
        lines.append("  end")
    for i in by_kind(nodes, "INT", p):
        a, b = i.get("from_cmp"), i.get("to_cmp")
        if a and b:
            lines.append("  %s_%s_out -->|\"%s: %s\"| %s_%s_in" % (
                mid(a), mid(i["id"]), i["id"], (i.get("title") or "").replace('"', "'"), mid(b), mid(i["id"])))
    return "\n".join(lines) + "\n"


def seq(nodes, edges, f):
    seams = sorted((i for i in nodes.values() if i["kind"] == "INT" and i.get("implements_fnc") == f["id"]), key=lambda x: x["id"])
    parts = list(out_edges(edges, f["id"], "allocated_to"))
    for i in seams:
        for c in (i.get("from_cmp"), i.get("to_cmp")):
            if c and c not in parts:
                parts.append(c)
    lines = ["sequenceDiagram", "  actor User"]
    for c in parts:
        lines.append("  participant %s as %s" % (mid(c), nodes.get(c, {}).get("title", c)))
    owner = mid(parts[0]) if parts else "System"
    if not parts:
        lines.append("  participant System")
    lines.append("  User->>%s: %s" % (owner, ", ".join(f.get("inputs") or []) or "trigger"))
    for i in seams:
        lines.append("  %s->>%s: %s %s" % (mid(i["from_cmp"]), mid(i["to_cmp"]), i["id"], (i.get("title") or "").replace(";", ",")))
    rule = (f.get("rule") or "").replace(";", ",").replace("\n", " ")
    if rule:
        lines.append("  Note over %s: %s" % (owner, rule[:120]))
    lines.append("  %s-->>User: %s" % (owner, ", ".join(f.get("outputs") or []) or "result"))
    return "\n".join(lines) + "\n"


def matrix(nodes, edges, p):
    rows = []
    for r in by_kind(nodes, "REQ", p):
        fncs = [f for f in in_edges(edges, r["id"], "implements") if nodes.get(f, {}).get("kind") == "FNC"]
        if not fncs:
            rows.append([r["id"], "GAP", "GAP", "GAP", tests_for(nodes, edges, [r["id"]])])
        for f in fncs:
            cmps = out_edges(edges, f, "allocated_to")
            unts = [u for u in in_edges(edges, f, "refines") if nodes.get(u, {}).get("kind") == "UNT"]
            tsts = tests_for(nodes, edges, [r["id"], f] + unts)
            rows.append([r["id"], f, ", ".join(cmps) or "GAP", ", ".join(unts) or "GAP", tsts])
    return rows


def tests_for(nodes, edges, targets):
    ts = sorted({t for x in targets for t in in_edges(edges, x, "verifies")})
    return ", ".join("%s (%s)" % (t, nodes[t].get("status", "not_run")) for t in ts) or "GAP"


def variables(nodes, edges, p):
    rows = []
    for api in by_kind(nodes, "API", p):
        reqs = ",".join(out_edges(edges, api["id"], "implements"))
        slots = {"request.headers": (api.get("request") or {}).get("headers"),
                 "request.query": (api.get("request") or {}).get("query"),
                 "request.body": (api.get("request") or {}).get("body"),
                 "response": ((api.get("response") or {}).get("success") or {}).get("body")}
        for slot, obj in slots.items():
            for path, v in walk_fields(obj or {}):
                typ = v.get("type") if isinstance(v, dict) else type(v).__name__
                d = v.get("description") if isinstance(v, dict) else v
                rows.append({"id": "%s#%s.%s" % (api["id"], slot, path), "name": "%s.%s" % (slot.split(".")[-1], path),
                             "type": typ, "definition": d if isinstance(d, str) else json.dumps(d),
                             "parent_interface": api["id"], "traced_requirement": reqs})
    return rows


V_LEFT = [("Requirements", ("USR", "REQ")), ("Functional", ("FNC", "API")), ("System", ("CMP", "INT")), ("Unit", ("UNT",))]
V_RIGHT = [("Acceptance test", "acceptance"), ("System test", "system"), ("Integration test", "integration"), ("Unit test", "unit")]


def v_svg(nodes, p):
    w, h = 760, 360
    parts = ['<svg viewBox="0 0 %d %d" class="v" xmlns="http://www.w3.org/2000/svg">' % (w, h)]
    parts.append('<polyline points="40,30 380,330 720,30" fill="none" stroke="#9ab" stroke-width="3"/>')
    tsts = by_kind(nodes, "TST", p)
    for i, (name, kinds) in enumerate(V_LEFT):
        x, y = 60 + i * 75, 40 + i * 70
        c = sum(len(by_kind(nodes, k, p)) for k in kinds)
        parts.append('<g><rect x="%d" y="%d" width="170" height="40" rx="6" fill="#e8f0fe" stroke="#4a6"/>'
                     '<text x="%d" y="%d">%s</text><text x="%d" y="%d" class="s">%s: %d</text></g>'
                     % (x - 60, y, x - 50, y + 17, name, x - 50, y + 33, "/".join(kinds), c))
    for i, (name, lvl) in enumerate(V_RIGHT):
        x, y = 640 - i * 75, 40 + i * 70
        ts = [t for t in tsts if (t.get("level") or "unit") == lvl]
        nr = sum(1 for t in ts if t.get("status", "not_run") == "not_run")
        parts.append('<g><rect x="%d" y="%d" width="170" height="40" rx="6" fill="#fef3e8" stroke="#c84"/>'
                     '<text x="%d" y="%d">%s</text><text x="%d" y="%d" class="s">TST: %d (not run %d)</text></g>'
                     % (x - 60, y, x - 50, y + 17, name, x - 50, y + 33, len(ts), nr))
    parts.append('<text x="345" y="352">Coding</text></svg>')
    return "".join(parts)


def esc(s):
    return html.escape(str(s))


def build(root):
    nodes, edges, meta = load(root)
    projects = meta.get("projects") or sorted({n.get("project") for n in nodes.values() if n.get("project")})
    out = os.path.join(root, "docs")
    os.makedirs(out, exist_ok=True)
    lint_res = lint(root)
    has_mermaid = os.path.exists(os.path.join(out, "mermaid.min.js"))
    tabs, panes, summary = [], [], {}
    for p in projects:
        pd = os.path.join(out, p)
        os.makedirs(pd, exist_ok=True)
        diagrams = {"requirements.mmd": ("Requirements diagram", req_diagram(nodes, edges, p)),
                    "bdd.mmd": ("Block definition diagram", bdd(nodes, edges, p)),
                    "ibd.mmd": ("Internal block diagram", ibd(nodes, edges, p))}
        for f in by_kind(nodes, "FNC", p):
            diagrams["seq-%s.mmd" % f["id"]] = ("Sequence: %s %s" % (f["id"], f.get("title", "")), seq(nodes, edges, f))
        for fn, (_, src) in diagrams.items():
            with open(os.path.join(pd, fn), "w", encoding="utf-8") as fh:
                fh.write(src)
        rows = matrix(nodes, edges, p)
        hdr = ["REQ", "FNC", "CMP", "UNT", "TST"]
        with open(os.path.join(pd, "trace-matrix.csv"), "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows([hdr] + rows)
        with open(os.path.join(pd, "trace-matrix.md"), "w", encoding="utf-8") as fh:
            fh.write("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
            for r in rows:
                fh.write("| " + " | ".join(r) + " |\n")
        var_rows = variables(nodes, edges, p)
        with open(os.path.join(pd, "variables.json"), "w", encoding="utf-8") as fh:
            json.dump(var_rows, fh, indent=2)
        gaps = sum(c.count("GAP") for r in rows for c in r)
        summary[p] = {"nodes": sum(1 for n in nodes.values() if n.get("project") == p), "gaps": gaps,
                      "diagrams": len(diagrams), "variables": len(var_rows)}

        tabs.append('<button onclick="show(\'%s\')">%s</button>' % (esc(p), esc(p)))
        body = ['<section id="p-%s" class="pane">' % esc(p), "<h2>%s</h2>" % esc(p), v_svg(nodes, p)]
        body.append("<h3>Trace matrix (REQ → FNC → CMP → UNT → TST)</h3><table><tr>%s</tr>" % "".join("<th>%s</th>" % h for h in hdr))
        for r in rows:
            body.append("<tr>%s</tr>" % "".join('<td class="%s">%s</td>' % ("gap" if c == "GAP" else "", esc(c)) for c in r))
        body.append("</table>")
        for fn, (title, src) in diagrams.items():
            body.append('<h3>%s</h3><pre class="mermaid">%s</pre><p class="s"><a href="%s/%s">%s</a></p>'
                        % (esc(title), esc(src), esc(p), esc(fn), esc(fn)))
        body.append("<h3>Nodes</h3><table><tr><th>ID</th><th>Title</th><th>Status</th><th>Statement</th></tr>")
        for n in sorted((n for n in nodes.values() if n.get("project") == p), key=lambda n: n["id"]):
            body.append("<tr><td id='%s'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(n["id"]), esc(n["id"]), esc(n.get("title", "")), esc(n.get("status", "")), esc(n.get("statement", ""))))
        body.append("</table>")
        body.append("<h3>Variables (%d)</h3><table><tr><th>id</th><th>type</th><th>definition</th><th>REQ</th></tr>" % len(var_rows))
        for v in var_rows:
            body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(esc(v[k]) for k in ("id", "type", "definition", "traced_requirement")))
        body.append("</table></section>")
        panes.append("\n".join(body))

    lint_html = "<p>Lint: no flags.</p>" if lint_res["total"] == 0 else "<ul>%s</ul>" % "".join(
        "<li>[%s] %s: %s</li>" % (esc(f["category"]), esc(f["id"]), esc(f["message"])) for f in lint_res["flags"])
    script = '<script src="mermaid.min.js"></script><script>mermaid.initialize({startOnLoad:true});</script>' if has_mermaid else \
        '<p class="s">Diagrams show Mermaid source (offline). Drop mermaid.min.js next to this file to render them, or paste a .mmd file into any Mermaid viewer.</p>'
    page = """<!doctype html><html><head><meta charset="utf-8"><title>V-model docs</title><style>
body{font-family:system-ui,sans-serif;margin:24px;color:#223}table{border-collapse:collapse;margin:8px 0}
td,th{border:1px solid #ccd;padding:4px 8px;font-size:13px;vertical-align:top}.gap{background:#fdd;font-weight:bold}
pre{background:#f6f8fa;padding:8px;overflow:auto;font-size:12px}.s{font-size:11px;fill:#556;color:#556}
svg.v{max-width:760px;font-size:13px}.pane{display:none}button{margin-right:6px;padding:4px 12px}
</style></head><body><h1>V-model documentation</h1>
<p>Graph version %s · source %s · <b>Plan lineage, not proof. Tests are not run unless evidence (EVD) says otherwise.</b></p>
<div>%s</div><h2>Lint</h2>%s%s
<script>function show(p){document.querySelectorAll('.pane').forEach(e=>e.style.display='none');document.getElementById('p-'+p).style.display='block'}show(%s)</script>
%s</body></html>""" % (esc(meta.get("graph_version", "?")), esc(meta.get("source_commit") or "n/a"), "".join(tabs),
                      lint_html, "\n".join(panes), json.dumps(projects[0] if projects else ""), script)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    return summary, lint_res


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    summary, lint_res = build(sys.argv[1])
    print(json.dumps({"index": os.path.join(sys.argv[1], "docs", "index.html"), "projects": summary,
                      "lint_flags": lint_res["total"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
