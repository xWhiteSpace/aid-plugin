"""Shared loader for a .vmodel/ SSOT tree. Standard library only."""
import json
import os
import re

KINDS = ["USR", "REQ", "FNC", "API", "CMP", "INT", "UNT", "TST",
         "TOL", "RSH", "STD", "VOC", "EVD"]
EDGE_TYPES = {"derives", "linked_from", "implements", "allocated_to",
              "integrates_with", "depends_on", "refines", "verifies",
              "supersedes", "evidences"}
ID_RE = re.compile(r"^(USR|REQ|FNC|API|CMP|INT|UNT|TST|TOL|RSH|STD|VOC|EVD)-([A-Z0-9]{2,5})-(\d{3,})$")


def load(root):
    nodes = {}
    reg = os.path.join(root, "registries")
    for kind in KINDS:
        path = os.path.join(reg, kind.lower() + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for nid, node in json.load(f).items():
                    node.setdefault("id", nid)
                    node.setdefault("kind", kind)
                    nodes[nid] = node
    edges = []
    epath = os.path.join(root, "graph", "edges.json")
    if os.path.exists(epath):
        with open(epath, encoding="utf-8") as f:
            edges = json.load(f)
    meta = {}
    mpath = os.path.join(root, "graph", "meta.json")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as f:
            meta = json.load(f)
    return nodes, edges, meta


def project_of(nid):
    m = ID_RE.match(nid)
    return m.group(2) if m else None


def by_kind(nodes, kind, project=None):
    out = [n for n in nodes.values()
           if n["kind"] == kind and (project is None or n.get("project") == project)]
    return sorted(out, key=lambda n: n["id"])


def out_edges(edges, src, etype=None):
    return [e["to"] for e in edges if e["from"] == src and (etype is None or e["type"] == etype)]


def in_edges(edges, dst, etype=None):
    return [e["from"] for e in edges if e["to"] == dst and (etype is None or e["type"] == etype)]
