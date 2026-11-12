#!/usr/bin/env python3
"""Board view of SSOT + GitHub. Not an SSOT publisher.

One parent issue per USR (/usr request); nine stage sub-issues covering
every node from that request. REQ ids are labels/rows, not issues.

Usage:
  python3 vmodel_board.py .vmodel status
  python3 vmodel_board.py .vmodel setup [--owner LOGIN] [--title TITLE]
  python3 vmodel_board.py .vmodel apply [--gh] --proof TEXT [--phase P] ...
  python3 vmodel_board.py .vmodel event KIND USR-or-REQ --proof TEXT [--phase P] ...
  python3 vmodel_board.py .vmodel note ISSUE TEXT --signer AGENT [--req ID]
  python3 vmodel_board.py .vmodel trail USR-or-REQ [--system|--notes]
"""
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import by_kind, in_edges, load, out_edges  # noqa: E402

COLUMNS = ["Backlog", "Ready", "In progress", "In review", "Done"]
PHASES = [
    "Requirements", "Functions", "System design", "Unit design", "Code",
    "Unit test", "Integration test", "System test", "Acceptance test",
]
STAGE_OWNERS = {
    "Requirements": "req-guardian",
    "Functions": "functional-specs",
    "System design": "system-designer",
    "Unit design": "unit-designer",
    "Code": "adept",
    "Unit test": "test-master",
    "Integration test": "test-master",
    "System test": "test-master",
    "Acceptance test": "test-master",
}
LAYER_STAGE = {
    "USR": "Requirements", "REQ": "Requirements",
    "FNC": "Functions", "API": "Functions",
    "CMP": "System design", "INT": "System design",
    "UNT": "Unit design", "code": "Code", "Code": "Code",
}
TEST_STAGE = {
    "unit": "Unit test", "integration": "Integration test",
    "system": "System test", "acceptance": "Acceptance test",
}
LANE_DEFAULTS = {
    "tiny": ["Requirements", "Acceptance test"],
    "small": ["Requirements", "Functions", "System design", "Unit design",
              "Code", "Acceptance test"],
    "standard": list(PHASES),
    "large": list(PHASES),
}
BOARD_FILE = "board.json"
LOG_FILE = "board-log.jsonl"
DEFAULT_TITLE = "A.I.D board"
SIGNERS = {
    "AID": "A.I.D", "board-keeper": "Board Keeper",
    "req-guardian": "Req Guardian", "functional-specs": "Functional Specs",
    "system-designer": "System Designer", "unit-designer": "Unit Designer",
    "adept": "Adept", "test-master": "Test Master", "last-boss": "Last Boss",
    "ssot-gate": "SSOT Gate", "researcher": "Researcher",
    "tools-manager": "Tools Manager",
}
EVENTS = {"intake", "published", "coding", "pr_open", "pr_merged", "phase"}
DEFAULT_PHASE = {
    "intake": "Requirements", "published": "Requirements", "coding": "Code",
    "pr_open": "System test", "pr_merged": "Acceptance test",
}
KIND_SYSTEM = "system"
KIND_NOTE = "note"
KIND_DASHBOARD = "dashboard"
MARKER_DASHBOARD = "<!-- aid-dashboard -->"
MARKER_SYSTEM = "<!-- aid-system -->"
MARKER_NOTE = "<!-- aid-note -->"


def board_path(root):
    return os.path.join(root, BOARD_FILE)


def log_path(root):
    return os.path.join(root, LOG_FILE)


def load_board(root):
    path = board_path(root)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_board(root, data):
    path = board_path(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return path


def read_log(root):
    path = log_path(root)
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_log(root, row):
    with open(log_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def skipped_stages(effort, empty_test_levels=None):
    effort = effort or {}
    earned = set(LANE_DEFAULTS.get(effort.get("lane")) or [])
    for s in effort.get("stages") or []:
        mapped = LAYER_STAGE.get(s) or TEST_STAGE.get(s)
        if mapped:
            earned.add(mapped)
    if not earned:
        earned = set(PHASES)
    skip = [p for p in PHASES if p not in earned]
    extra = []
    for item in empty_test_levels or []:
        level = item.get("level") if isinstance(item, dict) else item
        st = TEST_STAGE.get(level)
        if st and st not in skip:
            extra.append(st)
    return skip + extra


def skip_reason(phase, effort, empty_test_levels=None):
    for item in empty_test_levels or []:
        if isinstance(item, dict) and TEST_STAGE.get(item.get("level")) == phase:
            return item.get("reason") or ("empty_test_levels: %s" % phase)
    lane = (effort or {}).get("lane") or "lane"
    return "not planned: %s lane skips %s" % (lane, phase)


def column_from_subs(subs, gh=None):
    gh = gh or {}
    subs = subs or {}

    def closed(name):
        rec = subs.get(name) or {}
        return rec.get("state") == "closed"

    def rec(name):
        return subs.get(name) or {}

    if not closed(PHASES[0]):
        return "Backlog"
    if not all(closed(p) for p in PHASES[:4]):
        return "Backlog"
    if all(closed(p) for p in PHASES) and gh.get("pr_merged") and gh.get("acceptance_ok"):
        return "Done"
    if gh.get("pr_open") or gh.get("pr_merged"):
        return "In review"
    code = rec("Code")
    if code.get("state") == "open" and (gh.get("branch") or code.get("branch")):
        return "In progress"
    if closed("Code") or gh.get("branch"):
        return "In progress"
    return "Ready"


def req_facts(nodes, edges, nid):
    n = nodes.get(nid) or {}
    published = n.get("status") in ("published", "amended")
    fncs = in_edges(edges, nid, "implements")
    unts = []
    for f in fncs:
        unts.extend(in_edges(edges, f, "refines"))
    coded = False
    for u in unts:
        if out_edges(edges, u, "coded_in"):
            coded = True
            break
    tsts = in_edges(edges, nid, "verifies")
    tests_pass = False
    for t in tsts:
        if in_edges(edges, t, "evidences"):
            tests_pass = True
            break
    effort = n.get("effort")
    if not effort:
        for usr in out_edges(edges, nid, "derives"):
            effort = (nodes.get(usr) or {}).get("effort") or effort
    empty = n.get("empty_test_levels") or []
    acc = [t for t in tsts if (nodes.get(t) or {}).get("level") == "acceptance"]
    acc_pass = bool(acc) and all(in_edges(edges, t, "evidences") for t in acc)
    return {
        "published": published,
        "design_ready": published,
        "coding_started": coded or bool(unts and any(
            (nodes.get(u) or {}).get("source_files") for u in unts)),
        "tests_pass": tests_pass,
        "acceptance_ok": acc_pass,
        "acceptance": acc[0] if acc else None,
        "statement": n.get("statement") or n.get("title") or nid,
        "title": n.get("title") or nid,
        "project": n.get("project"),
        "effort": effort or {},
        "empty_test_levels": empty,
        "amended": n.get("status") == "amended",
    }


def reqs_of_usr(nodes, edges, usr_id):
    return [n for n in by_kind(nodes, "REQ") if usr_id in out_edges(edges, n["id"], "derives")]


def usr_facts(nodes, edges, usr_id):
    n = nodes.get(usr_id) or {}
    reqs = reqs_of_usr(nodes, edges, usr_id)
    facts = [req_facts(nodes, edges, r["id"]) for r in reqs]
    return {
        "published": (n.get("status") in ("published", "amended")
                      or (bool(facts) and all(f["published"] for f in facts))),
        "design_ready": bool(facts) and all(f.get("design_ready") for f in facts),
        "coding_started": any(f["coding_started"] for f in facts),
        "tests_pass": bool(facts) and all(f["tests_pass"] for f in facts),
        "acceptance_ok": bool(facts) and all(f.get("acceptance_ok") for f in facts),
        "statement": n.get("statement") or n.get("title") or usr_id,
        "title": n.get("title") or usr_id,
        "request": n.get("source") or n.get("statement") or "",
        "effort": n.get("effort") or {},
        "empty_test_levels": n.get("empty_test_levels") or [],
        "reqs": [r["id"] for r in reqs],
        "req_facts": {r["id"]: f for r, f in zip(reqs, facts)},
        "scope": stage_scope(nodes, edges, usr_id),
        "project": n.get("project"),
    }


def _scope_ids(nodes, nids):
    seen, out = [], []
    for i in nids:
        if i in seen:
            continue
        seen.append(i)
        st = (nodes.get(i) or {}).get("status") or "-"
        out.append({"id": i, "status": st})
    return out


def stage_scope(nodes, edges, usr_id):
    reqs = [r["id"] for r in reqs_of_usr(nodes, edges, usr_id)]
    fncs, apis, cmps, unts, files, tsts = [], [], [], [], [], []
    for rid in reqs:
        for f in in_edges(edges, rid, "implements"):
            kind = (nodes.get(f) or {}).get("kind")
            (apis if kind == "API" else fncs).append(f)
            unts.extend(in_edges(edges, f, "refines"))
            cmps.extend(out_edges(edges, f, "allocated_to"))
        tsts.extend(in_edges(edges, rid, "verifies"))
    for u in unts:
        files.extend(out_edges(edges, u, "coded_in"))
        cmps.extend([t for t in out_edges(edges, u, "refines")
                     if (nodes.get(t) or {}).get("kind") in ("CMP", "INT")])
    ints = []
    for c in cmps:
        ints.extend(in_edges(edges, c, "integrates_with"))
    by_level = {lv: [] for lv in TEST_STAGE}
    for t in tsts:
        lv = (nodes.get(t) or {}).get("level")
        if lv in by_level:
            by_level[lv].append(t)
    return {
        "Requirements": _scope_ids(nodes, reqs),
        "Functions": _scope_ids(nodes, fncs + apis),
        "System design": _scope_ids(nodes, cmps + ints),
        "Unit design": _scope_ids(nodes, unts),
        "Code": _scope_ids(nodes, files) or _scope_ids(nodes, unts),
        "Unit test": _scope_ids(nodes, by_level["unit"]),
        "Integration test": _scope_ids(nodes, by_level["integration"]),
        "System test": _scope_ids(nodes, by_level["system"]),
        "Acceptance test": _scope_ids(nodes, by_level["acceptance"]),
    }


def resolve_usr(nid, nodes, edges, board=None):
    board = board or {}
    if (nid or "").startswith("USR-"):
        return nid
    mapped = (board.get("req_parent") or {}).get(nid)
    if mapped:
        return mapped
    if (nid or "").startswith("REQ-"):
        usrs = out_edges(edges, nid, "derives")
        if usrs:
            return usrs[0]
    return nid


def log_matches(row, usr_id):
    if row.get("usr") == usr_id:
        return True
    if row.get("req") == usr_id:
        return True
    return usr_id in (row.get("reqs") or [])


def desired_column(ssot, gh=None, event=None, subs=None):
    gh = gh or {}
    if subs:
        gh2 = dict(gh)
        if ssot.get("coding_started") or event == "coding":
            gh2.setdefault("branch", True)
        if event == "pr_open":
            gh2.setdefault("pr_open", True)
        if event == "pr_merged":
            gh2.setdefault("pr_merged", gh.get("pr_merged"))
        if ssot.get("acceptance_ok") or ssot.get("tests_pass"):
            gh2.setdefault("acceptance_ok", True)
        return column_from_subs(subs, gh2)
    if event == "phase":
        return None
    if gh.get("pr_merged") and (ssot.get("acceptance_ok") or ssot.get("tests_pass") or gh.get("last_boss_ok")):
        return "Done"
    if gh.get("pr_open") or event == "pr_open":
        return "In review"
    if (ssot.get("coding_started") or event == "coding" or gh.get("branch")):
        return "In progress"
    if ssot.get("published") or ssot.get("design_ready") or event == "published":
        return "Ready"
    return "Backlog"


def next_column(current, desired):
    if desired is None:
        return current if current in COLUMNS else None
    if current not in COLUMNS:
        return "Backlog"
    if desired not in COLUMNS:
        return current
    ci, di = COLUMNS.index(current), COLUMNS.index(desired)
    if di <= ci:
        return current
    return COLUMNS[ci + 1]


def plan_rows(nodes, edges, gh_map=None, event=None, event_req=None, board=None):
    gh_map = gh_map or {}
    board = board or {}
    rows = []
    for n in by_kind(nodes, "USR"):
        if n.get("status") == "retired":
            continue
        nid = n["id"]
        ssot = usr_facts(nodes, edges, nid)
        ev = event if event_req in (None, nid) or event_req in ssot["reqs"] else None
        subs = ((board.get("sub_issues") or {}).get(nid))
        desired = desired_column(ssot, gh_map.get(nid), ev, subs=subs)
        rows.append({
            "id": nid,
            "title": ssot["title"],
            "statement": ssot["statement"],
            "request": ssot.get("request") or ssot["statement"],
            "desired": desired,
            "published": ssot["published"],
            "coding_started": ssot["coding_started"],
            "tests_pass": ssot["tests_pass"],
            "acceptance_ok": ssot.get("acceptance_ok"),
            "reqs": ssot["reqs"],
            "label": nid,
        })
    return rows


def run_gh(args, runner=None):
    fn = runner or subprocess.check_output
    return fn(["gh"] + args, stderr=subprocess.STDOUT)


def gh_json(args, runner=None):
    out = run_gh(args, runner=runner)
    if isinstance(out, bytes):
        out = out.decode("utf-8")
    return json.loads(out)


def sign_comment(text, signer):
    who = SIGNERS.get(signer, signer)
    body = (text or "").strip()
    return "%s\n\n— %s" % (body, who)


def proof_ok(proof):
    return bool((proof or "").strip())


def move_header(req_id, current, nxt):
    if not nxt or current == nxt:
        return "%s: no column change" % req_id
    left = current if current in COLUMNS else "(new)"
    return "%s: %s → %s" % (req_id, left, nxt)


def format_block(req_id, current, nxt, phase, who, changed, next_step, proof, back):
    return "\n".join([
        "**%s**" % move_header(req_id, current, nxt),
        "**Phase done:** %s" % (phase or "-"),
        "**Who:** %s" % (who or "-"),
        "**Changed:** %s" % (changed or "-"),
        "**Next:** %s" % (next_step or "-"),
        "**Proof:** %s" % (proof or "-"),
        "**Back:** %s" % (back or "first entry"),
    ])


def format_system(block, signer="board-keeper"):
    return "%s\n[system]\n%s" % (MARKER_SYSTEM, sign_comment(block, signer))


def format_note(text, signer):
    return "%s\n%s" % (MARKER_NOTE, sign_comment(text, signer))


def stage_status(rec):
    rec = rec or {}
    if rec.get("state") == "closed" and rec.get("reason") == "not_planned":
        return "not planned"
    if rec.get("state") == "closed":
        return "closed"
    return rec.get("state") or "open"


def format_scope(scope):
    if not scope:
        return "-"
    if isinstance(scope, str):
        return scope
    parts = []
    for n in scope:
        if isinstance(n, dict):
            parts.append("%s (%s)" % (n.get("id"), n.get("status") or "-"))
        else:
            parts.append(str(n))
    return ", ".join(parts) or "-"


def format_parent_dashboard(usr_id, statement, column, stages, pr, updated, reqs=None):
    lines = [
        MARKER_DASHBOARD,
        "**%s** — %s" % (usr_id, statement or ""),
        "**Column:** %s" % (column or "Backlog"),
        "**PR:** %s" % (pr or "none"),
        "",
        "| REQ | Sentence | Stage | Acceptance TST | Proof | Earlier |",
        "|---|---|---|---|---|---|",
    ]
    for r in reqs or []:
        earlier = r.get("amended_from") or "-"
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r.get("id"), r.get("statement") or "-", r.get("stage") or "-",
            r.get("acceptance") or "-", r.get("proof") or "-", earlier))
    if not reqs:
        lines.append("| - | - | - | - | - | - |")
    lines.extend([
        "",
        "| # | Stage | Status | Owner | Proof | Issue |",
        "|---|---|---|---|---|---|",
    ])
    for i, phase in enumerate(PHASES, 1):
        rec = (stages or {}).get(phase) or {}
        issue = rec.get("number")
        link = "#%s" % issue if issue not in (None, "example") else (issue or "-")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            i, phase, stage_status(rec), rec.get("owner") or STAGE_OWNERS.get(phase),
            rec.get("proof") or "-", link))
    lines.append("")
    lines.append("Updated: %s" % (updated or now_iso()))
    return "\n".join(lines)


def format_sub_dashboard(stage, parent, owner, status, scope, proof, gate, updated):
    return "\n".join([
        MARKER_DASHBOARD,
        "**Stage:** %s" % stage,
        "**Parent:** %s" % parent,
        "**Owner:** %s" % (owner or STAGE_OWNERS.get(stage) or "-"),
        "**Status:** %s" % (status or "open"),
        "**Scope:** %s" % format_scope(scope),
        "**Proof:** %s" % (proof or "-"),
        "**Gate:** %s" % (gate or "-"),
        "Updated: %s" % (updated or now_iso()),
    ])


def last_system_back(root, req_id, sub_only=False):
    for row in reversed(read_log(root)):
        if not log_matches(row, req_id):
            continue
        kind = row.get("kind") or KIND_SYSTEM
        if kind != KIND_SYSTEM:
            continue
        if sub_only and not row.get("sub_issue") and not row.get("stage"):
            continue
        if sub_only and not row.get("stage"):
            continue
        return row.get("comment_url") or row.get("time") or "first entry"
    return "first entry"


def init_sub_issues(board, req_id, skipped=None, reasons=None):
    skipped = skipped or []
    reasons = reasons or {}
    subs = board.setdefault("sub_issues", {}).setdefault(req_id, {})
    for i, phase in enumerate(PHASES, 1):
        rec = subs.get(phase) or {
            "number": None, "state": "open", "reason": None,
            "title": "%s · %s" % (req_id, phase), "index": i,
            "owner": STAGE_OWNERS.get(phase),
        }
        rec.setdefault("title", "%s · %s" % (req_id, phase))
        rec.setdefault("index", i)
        rec.setdefault("owner", STAGE_OWNERS.get(phase))
        if phase in skipped and rec.get("state") != "closed":
            rec["state"] = "closed"
            rec["reason"] = "not_planned"
            rec["why"] = reasons.get(phase) or skip_reason(phase, {"lane": "lane"})
        subs[phase] = rec
    return subs


def repo_ids(runner=None):
    data = gh_json(["repo", "view", "--json", "owner,name,nameWithOwner"], runner=runner)
    owner = (data.get("owner") or {}).get("login") or data.get("owner")
    return {
        "owner": owner,
        "repo": data.get("name"),
        "nwo": data.get("nameWithOwner"),
    }


def find_or_create_project(owner, title, runner=None):
    listing = gh_json(
        ["project", "list", "--owner", owner, "--limit", "50", "--format", "json"],
        runner=runner)
    nodes = listing if isinstance(listing, list) else (listing.get("projects") or listing.get("items") or [])
    for p in nodes:
        if p.get("title") == title:
            return p
    created = gh_json(
        ["project", "create", "--owner", owner, "--title", title, "--format", "json"],
        runner=runner)
    return created


def status_options_from_fields(fields):
    rows = fields if isinstance(fields, list) else (fields.get("fields") or fields.get("items") or [])
    for f in rows:
        name = (f.get("name") or "").lower()
        if name == "status" or f.get("type") in ("ProjectV2SingleSelectField", "TEXT"):
            opts = {}
            for o in f.get("options") or []:
                opts[o.get("name")] = o.get("id")
            if opts:
                return f.get("id"), opts
    return None, {}


SETUP_MUTATION = """
mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  updateProjectV2Field(input: {fieldId: $fieldId, singleSelectOptions: $options}) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        options { id name }
      }
    }
  }
}
"""

SETUP_OPTIONS = [
    {"name": "Backlog", "color": "GRAY", "description": "Intake"},
    {"name": "Ready", "color": "BLUE", "description": "Published REQ"},
    {"name": "In progress", "color": "YELLOW", "description": "Coding"},
    {"name": "In review", "color": "ORANGE", "description": "PR open"},
    {"name": "Done", "color": "GREEN", "description": "Merged and proven"},
]


def ensure_status_options(field_id, current, runner=None):
    if all(current.get(c) for c in COLUMNS):
        return current
    raw = run_gh([
        "api", "graphql",
        "-f", "query=%s" % SETUP_MUTATION.strip(),
        "-f", "fieldId=%s" % field_id,
        "-F", "options=%s" % json.dumps(SETUP_OPTIONS),
    ], runner=runner)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    data = json.loads(raw)
    field = (((data.get("data") or {}).get("updateProjectV2Field") or {}).get("projectV2Field") or {})
    opts = {}
    for o in field.get("options") or []:
        opts[o.get("name")] = o.get("id")
    return opts or current


def cmd_setup(root, owner=None, title=None, runner=None):
    ids = repo_ids(runner=runner)
    owner = owner or ids["owner"]
    title = title or DEFAULT_TITLE
    proj = find_or_create_project(owner, title, runner=runner)
    number = proj.get("number")
    project_id = proj.get("id")
    fields = gh_json(
        ["project", "field-list", str(number), "--owner", owner, "--format", "json"],
        runner=runner)
    field_id, opts = status_options_from_fields(fields)
    if field_id:
        opts = ensure_status_options(field_id, opts, runner=runner)
    nwo = ids.get("nwo")
    if number and nwo:
        try:
            run_gh(["project", "link", str(number), "--owner", owner, "--repo", nwo],
                   runner=runner)
        except (OSError, subprocess.CalledProcessError):
            pass
    prev = load_board(root)
    board = {
        "title": title,
        "owner": owner,
        "repo": ids.get("repo"),
        "nwo": nwo,
        "project_number": number,
        "project_id": project_id,
        "status_field_id": field_id,
        "status_options": {c: opts.get(c) for c in COLUMNS},
        "issues": prev.get("issues") or {},
        "sub_issues": prev.get("sub_issues") or {},
        "items": prev.get("items") or {},
        "status": prev.get("status") or {},
        "pending": prev.get("pending") or {},
        "dashboards": prev.get("dashboards") or {},
        "req_parent": prev.get("req_parent") or {},
        "amended_from": prev.get("amended_from") or {},
        "req_progress": prev.get("req_progress") or {},
    }
    path = save_board(root, board)
    return {"board": path, "project_number": number, "url": proj.get("url")}


def cmd_status(root, gh=False, runner=None):
    board = load_board(root)
    nodes, edges, _ = load(root)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    rows = plan_rows(nodes, edges, gh_map, board=board)
    return {"rows": rows, "columns": COLUMNS}


def read_gh_state(root, runner=None):
    board = load_board(root)
    nwo = board.get("nwo")
    if not nwo:
        try:
            nwo = repo_ids(runner=runner).get("nwo")
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
            return {}
    out = {}
    issues = board.get("issues") or {}
    for req_id, num in issues.items():
        try:
            issue = gh_json(["issue", "view", str(num), "--json", "number,state,url"], runner=runner)
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        prs = []
        try:
            prs = gh_json([
                "pr", "list", "--repo", nwo, "--state", "all", "--search", req_id,
                "--json", "number,url,state,mergedAt,title",
            ], runner=runner)
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            prs = []
        open_pr = [p for p in prs if p.get("state") == "OPEN"]
        merged = [p for p in prs if p.get("mergedAt") or p.get("state") == "MERGED"]
        out[req_id] = {
            "issue": issue.get("number"),
            "issue_url": issue.get("url"),
            "pr_open": bool(open_pr),
            "pr_merged": bool(merged),
            "pr_url": (merged or open_pr or [{}])[0].get("url"),
        }
    return out


def post_comment(issue, body, runner=None, nwo=None):
    if issue is None:
        return None
    try:
        if nwo:
            data = gh_json([
                "api", "repos/%s/issues/%s/comments" % (nwo, issue),
                "-f", "body=%s" % body,
            ], runner=runner)
            return data.get("html_url") or data.get("id")
        run_gh(["issue", "comment", str(issue), "--body", body], runner=runner)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
        return None
    return None


def edit_comment(comment_id, body, runner=None, nwo=None):
    if not comment_id or not nwo:
        return False
    try:
        gh_json([
            "api", "repos/%s/issues/comments/%s" % (nwo, comment_id),
            "-X", "PATCH", "-f", "body=%s" % body,
        ], runner=runner)
        return True
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
        return False


def ensure_issue(root, row, board, runner=None, title=None):
    issues = board.setdefault("issues", {})
    if row["id"] in issues:
        return issues[row["id"]], False
    label = row["label"]
    try:
        run_gh(["label", "create", label, "--description", "A.I.D request",
                "--color", "0E8A16"], runner=runner)
    except (OSError, subprocess.CalledProcessError):
        pass
    for req in row.get("reqs") or []:
        try:
            run_gh(["label", "create", req, "--description", "A.I.D requirement row",
                    "--color", "1D76DB"], runner=runner)
        except (OSError, subprocess.CalledProcessError):
            pass
    short = row.get("title") or (row.get("statement") or row["id"])[:72]
    issue_title = title or "%s · %s" % (row["id"], short)
    body = row.get("request") or row.get("statement") or row["id"]
    args = [
        "issue", "create", "--title", issue_title,
        "--body", body, "--label", label, "--json", "number,url,id",
    ]
    for req in row.get("reqs") or []:
        args.extend(["--label", req])
    created = gh_json(args, runner=runner)
    num = created.get("number")
    issues[row["id"]] = num
    url = created.get("url")
    if board.get("project_number") and url:
        try:
            added = gh_json([
                "project", "item-add", str(board["project_number"]),
                "--owner", board.get("owner") or "",
                "--url", url, "--format", "json",
            ], runner=runner)
            if added.get("id"):
                board.setdefault("items", {})[row["id"]] = added.get("id")
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
            pass
    save_board(root, board)
    return num, True


def ensure_sub_issues(root, req_id, board, ssot, runner=None, gh=False):
    skipped = skipped_stages(ssot.get("effort"), ssot.get("empty_test_levels"))
    reasons = {p: skip_reason(p, ssot.get("effort"), ssot.get("empty_test_levels"))
               for p in skipped}
    subs = init_sub_issues(board, req_id, skipped, reasons)
    scope_map = ssot.get("scope") or {}
    for phase, rec in subs.items():
        if not rec.get("scope"):
            rec["scope"] = scope_map.get(phase)
    parent = (board.get("issues") or {}).get(req_id)
    nwo = board.get("nwo")
    if not (gh and parent and nwo):
        save_board(root, board)
        return subs
    for phase in PHASES:
        rec = subs[phase]
        if rec.get("number"):
            continue
        try:
            created = gh_json([
                "issue", "create",
                "--title", rec["title"],
                "--body", "%s\n\nStage: %s\nScope: %s" % (
                    req_id, phase, format_scope(rec.get("scope"))),
                "--json", "number,url,id",
            ], runner=runner)
            rec["number"] = created.get("number")
            rec["id"] = created.get("id")
            gh_json([
                "api", "-X", "POST",
                "repos/%s/issues/%s/sub_issues" % (nwo, parent),
                "-f", "sub_issue_id=%s" % created.get("id"),
            ], runner=runner)
            if rec.get("reason") == "not_planned":
                run_gh([
                    "api", "-X", "PATCH",
                    "repos/%s/issues/%s" % (nwo, rec["number"]),
                    "-f", "state=closed", "-f", "state_reason=not_planned",
                    "-f", "body=%s" % rec.get("why"),
                ], runner=runner)
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
            pass
    save_board(root, board)
    return subs


def close_stage(board, req_id, phase, why="completed", runner=None, gh=False):
    rec = ((board.get("sub_issues") or {}).get(req_id) or {}).get(phase)
    if not rec:
        return
    rec["state"] = "closed"
    rec["reason"] = why
    nwo = board.get("nwo")
    if gh and nwo and rec.get("number"):
        reason = "not_planned" if why == "not_planned" else "completed"
        try:
            run_gh([
                "api", "-X", "PATCH",
                "repos/%s/issues/%s" % (nwo, rec["number"]),
                "-f", "state=closed", "-f", "state_reason=%s" % reason,
            ], runner=runner)
        except (OSError, subprocess.CalledProcessError):
            pass


def set_status(board, item_id, column, runner=None):
    opt = (board.get("status_options") or {}).get(column)
    if not (board.get("project_id") and board.get("status_field_id") and opt and item_id):
        return False
    run_gh([
        "project", "item-edit",
        "--id", item_id,
        "--project-id", board["project_id"],
        "--field-id", board["status_field_id"],
        "--single-select-option-id", opt,
    ], runner=runner)
    return True


def record_comment(root, req_id, current, nxt, payload, issue=None, signer="board-keeper",
                   runner=None, nwo=None, gh=False, kind=KIND_SYSTEM, stage=None,
                   sub_issue=None, body=None):
    proof = (payload.get("proof") or "").strip() if kind == KIND_SYSTEM else (payload.get("proof") or "")
    if kind == KIND_SYSTEM and not proof_ok(proof):
        return None, {"id": req_id, "blocked": "no proof"}
    back = None
    if kind == KIND_SYSTEM:
        back = last_system_back(root, req_id, sub_only=issue is None or stage is None)
        if stage:
            back = last_system_back(root, req_id, sub_only=False)
            prev = None
            for row in reversed(read_log(root)):
                if log_matches(row, req_id) and (row.get("kind") or KIND_SYSTEM) == KIND_SYSTEM and row.get("stage") == stage:
                    prev = row.get("comment_url") or row.get("time")
                    break
            back = prev or "first entry"
        text = format_block(
            req_id, current, nxt,
            payload.get("phase") or stage, payload.get("who"), payload.get("changed"),
            payload.get("next"), proof, back)
        body = format_system(text, signer)
    elif body is None:
        body = format_note(payload.get("text") or "", signer)
    url = None
    if gh and issue is not None:
        url = post_comment(issue, body, runner=runner, nwo=nwo)
    row = {
        "time": now_iso(),
        "issue": issue,
        "usr": payload.get("usr") or (req_id if (req_id or "").startswith("USR-") else None),
        "reqs": payload.get("reqs"),
        "req": req_id,
        "from": current,
        "to": nxt,
        "phase": payload.get("phase") or stage,
        "who": payload.get("who") or SIGNERS.get(signer, signer),
        "changed": payload.get("changed"),
        "proof": proof or payload.get("proof"),
        "comment_url": url,
        "signer": SIGNERS.get(signer, signer),
        "kind": kind,
        "stage": stage,
        "sub_issue": sub_issue if sub_issue is not None else (issue if stage else None),
        "next": payload.get("next"),
        "text": payload.get("text"),
        "back": (back if kind == KIND_SYSTEM else None),
    }
    append_log(root, row)
    return body, row


def req_table_rows(board, usr_id, ssot=None):
    ssot = ssot or {}
    facts = ssot.get("req_facts") or {}
    progress = board.get("req_progress") or {}
    amended = board.get("amended_from") or {}
    rows = []
    for rid in ssot.get("reqs") or list(facts):
        f = facts.get(rid) or {}
        prog = progress.get(rid) or {}
        rows.append({
            "id": rid,
            "statement": f.get("statement") or rid,
            "stage": prog.get("stage") or "-",
            "acceptance": f.get("acceptance") or "-",
            "proof": prog.get("proof") or f.get("proof") or "-",
            "amended_from": amended.get(rid),
        })
    return rows


def refresh_dashboards(root, req_id, board, statement, column, gh=False, runner=None, ssot=None):
    subs = (board.get("sub_issues") or {}).get(req_id) or {}
    pr = ((board.get("pending") or {}).get(req_id) or {}).get("proof")
    parent_body = format_parent_dashboard(
        req_id, statement, column, subs, pr, now_iso(),
        reqs=req_table_rows(board, req_id, ssot))
    store = board.setdefault("dashboards", {}).setdefault(req_id, {})
    store["parent_body"] = parent_body
    nwo = board.get("nwo")
    parent = (board.get("issues") or {}).get(req_id)
    if gh and parent:
        cid = store.get("parent_comment_id")
        if cid:
            edit_comment(cid, parent_body, runner=runner, nwo=nwo)
        else:
            url = post_comment(parent, parent_body, runner=runner, nwo=nwo)
            store["parent_comment_id"] = url
    stage_ids = store.setdefault("stages", {})
    scope_map = (ssot or {}).get("scope") or {}
    for phase, rec in subs.items():
        status = "not planned" if rec.get("reason") == "not_planned" else rec.get("state")
        scope = scope_map.get(phase) or rec.get("scope")
        body = format_sub_dashboard(
            phase, "%s %s" % (parent or "", req_id), rec.get("owner"),
            status, scope, rec.get("proof"), rec.get("gate"), now_iso())
        rec["dashboard"] = body
        if gh and rec.get("number"):
            sid = stage_ids.get(phase)
            if sid:
                edit_comment(sid, body, runner=runner, nwo=nwo)
            else:
                url = post_comment(rec.get("number"), body, runner=runner, nwo=nwo)
                stage_ids[phase] = url


def merge_payload(base, extra):
    out = dict(base or {})
    for k, v in (extra or {}).items():
        if v is not None and v != "":
            out[k] = v
    return out


def cmd_apply(root, gh=False, runner=None, payload=None, signer="board-keeper"):
    board = load_board(root)
    nodes, edges, _ = load(root)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    current = board.get("status") or {}
    pending = board.get("pending") or {}
    moves = []
    blocked = []
    for row in plan_rows(nodes, edges, gh_map, board=board):
        cur = current.get(row["id"])
        nxt = next_column(cur, row["desired"])
        if nxt == cur:
            continue
        fields = merge_payload(pending.get(row["id"]), payload)
        fields.setdefault("usr", row["id"])
        fields.setdefault("reqs", row.get("reqs"))
        if not proof_ok(fields.get("proof")):
            blocked.append({"id": row["id"], "from": cur, "to": nxt, "blocked": "no proof"})
            continue
        issue = (board.get("issues") or {}).get(row["id"])
        created = False
        if gh:
            issue, created = ensure_issue(root, row, board, runner=runner)
            if created:
                nxt = "Backlog"
        ssot = usr_facts(nodes, edges, row["id"])
        ensure_sub_issues(root, row["id"], board, ssot, runner=runner, gh=gh)
        back = last_system_back(root, row["id"], sub_only=True)
        fields = merge_payload(fields, {"phase": fields.get("phase")})
        body, _log = record_comment(
            root, row["id"], cur, nxt, fields, issue=issue, signer=signer,
            runner=runner, nwo=board.get("nwo"), gh=gh, kind=KIND_SYSTEM)
        if _log:
            _log["proof"] = fields.get("proof")
        item = (board.get("items") or {}).get(row["id"])
        if gh and item and nxt:
            try:
                set_status(board, item, nxt, runner=runner)
            except (OSError, subprocess.CalledProcessError):
                pass
        current[row["id"]] = nxt
        pending.pop(row["id"], None)
        refresh_dashboards(root, row["id"], board, row["statement"], nxt, gh=gh, runner=runner, ssot=ssot)
        moves.append({
            "id": row["id"], "from": cur, "to": nxt, "issue": issue,
            "comment": body, "back": back,
        })
    board["status"] = current
    board["pending"] = pending
    save_board(root, board)
    return {"moves": moves, "blocked": blocked}


def link_reqs(board, usr_id, req_ids):
    parents = board.setdefault("req_parent", {})
    amended = board.setdefault("amended_from", {})
    for rid in req_ids or []:
        prev = parents.get(rid)
        if prev and prev != usr_id:
            amended[rid] = prev
        parents[rid] = usr_id
    return parents


def cmd_event(root, kind, nid, gh=False, runner=None, payload=None, signer="board-keeper"):
    if kind not in EVENTS:
        raise SystemExit("error: event must be one of %s" % ", ".join(sorted(EVENTS)))
    nodes, edges, _ = load(root)
    if nid not in nodes:
        raise SystemExit("error: %s is not in the registries" % nid)
    board = load_board(root)
    usr_id = resolve_usr(nid, nodes, edges, board)
    req_id = usr_id
    payload = dict(payload or {})
    payload.setdefault("phase", DEFAULT_PHASE.get(kind))
    if not proof_ok(payload.get("proof")):
        return {"id": usr_id, "event": kind, "blocked": "no proof"}
    ssot = usr_facts(nodes, edges, usr_id)
    payload["usr"] = usr_id
    payload["reqs"] = ssot.get("reqs") or []
    link_reqs(board, usr_id, ssot.get("reqs"))
    if nid.startswith("REQ-"):
        prog = board.setdefault("req_progress", {}).setdefault(nid, {})
        prog["stage"] = payload.get("phase")
        prog["proof"] = payload.get("proof")
    else:
        for rid in ssot.get("reqs") or []:
            prog = board.setdefault("req_progress", {}).setdefault(rid, {})
            prog["stage"] = payload.get("phase")
            prog["proof"] = payload.get("proof")
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    gh_one = dict(gh_map.get(usr_id) or {})
    if ssot.get("coding_started") or kind == "coding":
        gh_one.setdefault("branch", True)
    if ssot.get("acceptance_ok"):
        gh_one.setdefault("acceptance_ok", True)
    if kind == "pr_merged" and not gh_one.get("pr_merged"):
        return {"id": usr_id, "blocked": "Done needs a merged pull request"}
    if kind == "pr_merged" and gh_one.get("pr_merged") and not gh_one.get("acceptance_ok"):
        return {"id": usr_id, "blocked": "Done needs every REQ acceptance test to pass"}
    issue = (board.get("issues") or {}).get(usr_id)
    if gh and issue is None:
        row = {
            "id": usr_id, "title": ssot["title"], "statement": ssot["statement"],
            "request": ssot.get("request") or ssot["statement"],
            "reqs": ssot.get("reqs") or [],
            "label": usr_id,
        }
        issue, _created = ensure_issue(root, row, board, runner=runner)
    subs = ensure_sub_issues(root, req_id, board, ssot, runner=runner, gh=gh)
    phase = payload.get("phase") if payload.get("phase") in PHASES else DEFAULT_PHASE.get(kind)
    rec = subs.get(phase) or {}
    if kind in ("published", "phase", "pr_merged") and rec.get("reason") != "not_planned":
        close_stage(board, req_id, phase, why="completed", runner=runner, gh=gh)
        rec = subs.get(phase) or rec
        rec["proof"] = payload.get("proof")
        rec["scope"] = (ssot.get("scope") or {}).get(phase) or payload.get("changed")
        rec["gate"] = payload.get("who")
    if kind == "coding":
        code = subs.setdefault("Code", rec)
        code["state"] = "open"
        code["branch"] = True
        code["reason"] = None
        rec = code
    if kind == "intake":
        rec = subs.get("Requirements") or rec
        rec["state"] = rec.get("state") or "open"
    desired = desired_column(ssot, gh_one, event=kind, subs=subs)
    cur = (board.get("status") or {}).get(req_id)
    nxt = next_column(cur, desired)
    sub_num = rec.get("number")
    sub_body, sub_log = record_comment(
        root, req_id, cur, nxt if nxt == cur else cur, payload,
        issue=sub_num, signer=signer, runner=runner, nwo=board.get("nwo"),
        gh=gh, kind=KIND_SYSTEM, stage=phase, sub_issue=sub_num)
    parent_body = None
    moved = nxt != cur
    if moved:
        back = (sub_log or {}).get("comment_url") or (sub_log or {}).get("time") or "first entry"
        payload_parent = dict(payload)
        parent_body, _plog = record_comment(
            root, req_id, cur, nxt, payload_parent, issue=issue, signer=signer,
            runner=runner, nwo=board.get("nwo"), gh=gh, kind=KIND_SYSTEM)
        board.setdefault("status", {})[req_id] = nxt
        item = (board.get("items") or {}).get(req_id)
        if gh and item and nxt:
            try:
                set_status(board, item, nxt, runner=runner)
            except (OSError, subprocess.CalledProcessError):
                pass
    board.setdefault("pending", {})[req_id] = {
        k: payload.get(k) for k in ("phase", "who", "changed", "next", "proof")
    }
    refresh_dashboards(root, req_id, board, ssot["statement"],
                       (board.get("status") or {}).get(req_id) or nxt,
                       gh=gh, runner=runner, ssot=ssot)
    save_board(root, board)
    return {
        "id": usr_id,
        "event": kind,
        "current": cur,
        "desired": desired,
        "next": nxt,
        "moved": moved,
        "comment": parent_body or sub_body,
        "sub_comment": sub_body,
        "log": sub_log,
        "stage": phase,
        "sub_issue": sub_num,
    }


def lookup_issue(board, issue):
    issue_s = str(issue)
    for req, num in (board.get("issues") or {}).items():
        if str(num) == issue_s:
            return req, None
    for req, subs in (board.get("sub_issues") or {}).items():
        for phase, rec in subs.items():
            if str(rec.get("number")) == issue_s:
                return req, phase
    return None, None


def cmd_note(root, issue, text, signer, req_id=None, stage=None, gh=True, runner=None):
    board = load_board(root)
    found_req, found_stage = lookup_issue(board, issue)
    req_id = req_id or found_req
    stage = stage or found_stage
    if not req_id:
        return {"blocked": "unknown issue", "issue": issue}
    nodes, edges, _ = load(root)
    usr_id = resolve_usr(req_id, nodes, edges, board)
    ssot = usr_facts(nodes, edges, usr_id) if usr_id in nodes else {}
    payload = {
        "text": text, "phase": stage, "who": SIGNERS.get(signer, signer),
        "usr": usr_id, "reqs": ssot.get("reqs"),
    }
    body, log_row = record_comment(
        root, usr_id or req_id, None, None, payload, issue=issue, signer=signer,
        runner=runner, nwo=board.get("nwo"), gh=gh, kind=KIND_NOTE,
        stage=stage, sub_issue=issue if stage else None)
    save_board(root, board)
    return {"issue": issue, "body": body, "log": log_row, "usr": usr_id,
            "req": req_id, "stage": stage}


def trail_order(rows):
    parent = [r for r in rows if not r.get("stage")]
    out = list(parent)
    for phase in PHASES:
        out.extend(r for r in rows if r.get("stage") == phase)
    return out


def cmd_trail(root, nid, kind=None):
    nodes, edges, _ = load(root)
    board = load_board(root)
    usr_id = resolve_usr(nid, nodes, edges, board)
    rows = [r for r in read_log(root)
            if log_matches(r, usr_id) or r.get("req") == nid
            or nid in (r.get("reqs") or [])]
    if kind == KIND_SYSTEM:
        rows = [r for r in rows if (r.get("kind") or KIND_SYSTEM) == KIND_SYSTEM]
    elif kind == KIND_NOTE:
        rows = [r for r in rows if r.get("kind") == KIND_NOTE]
    rows = trail_order(rows)
    rendered = []
    system_prev = {}
    last_sys = "first entry"
    for r in rows:
        kind_r = r.get("kind") or KIND_SYSTEM
        if kind_r == KIND_NOTE:
            rendered.append(format_note(r.get("text") or "",
                                        _signer_key(r.get("signer"))))
            continue
        key = r.get("stage") or "_parent"
        back_val = system_prev.get(key) or last_sys if key != "_parent" else last_system_back_from(rows, r)
        if key == "_parent":
            back_val = "first entry"
            for prev in reversed(rows[:rows.index(r)]):
                if (prev.get("kind") or KIND_SYSTEM) == KIND_SYSTEM and prev.get("stage"):
                    back_val = prev.get("comment_url") or prev.get("time") or "first entry"
                    break
                if (prev.get("kind") or KIND_SYSTEM) == KIND_SYSTEM and not prev.get("stage"):
                    back_val = prev.get("comment_url") or prev.get("time") or "first entry"
                    break
            if rows.index(r) == 0:
                back_val = "first entry"
        else:
            back_val = "first entry"
            for prev in reversed(rows[:rows.index(r)]):
                if (prev.get("kind") or KIND_SYSTEM) != KIND_SYSTEM:
                    continue
                if prev.get("stage") == r.get("stage"):
                    back_val = prev.get("comment_url") or prev.get("time") or "first entry"
                    break
        stored = r.get("comment_url")
        text = format_block(
            r.get("usr") or r.get("req"), r.get("from"), r.get("to"), r.get("phase") or r.get("stage"),
            r.get("who"), r.get("changed"), r.get("next"), r.get("proof"),
            r.get("back") or back_val)
        signer = _signer_key(r.get("signer"))
        rendered.append(format_system(text, signer))
        if kind_r == KIND_SYSTEM:
            last_sys = stored or r.get("time") or last_sys
            system_prev[key] = last_sys
    return {"usr": usr_id, "req": nid, "entries": rows, "rendered": rendered}


def last_system_back_from(rows, current):
    idx = rows.index(current)
    if idx == 0:
        return "first entry"
    for prev in reversed(rows[:idx]):
        if (prev.get("kind") or KIND_SYSTEM) == KIND_SYSTEM:
            return prev.get("comment_url") or prev.get("time") or "first entry"
    return "first entry"


def _signer_key(label):
    for k, v in SIGNERS.items():
        if v == label or k == label:
            return k
    return "board-keeper"


def parse_args(argv):
    root = None
    cmd = "status"
    rest = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("status", "setup", "apply", "comment", "event", "trail", "note"):
            cmd = a
            rest = argv[i + 1:]
            break
        elif a.startswith("-"):
            rest = argv[i:]
            break
        elif root is None:
            root = a
        else:
            cmd = a
            rest = argv[i + 1:]
            break
        i += 1
    return root, cmd, rest


def flag(rest, name):
    return name in rest


def opt(rest, name, default=None):
    if name in rest:
        i = rest.index(name)
        if i + 1 < len(rest):
            return rest[i + 1]
    return default


def positional(rest):
    skip_next = False
    out = []
    flags_with_val = {
        "--owner", "--title", "--signer", "--phase", "--who", "--changed",
        "--proof", "--next", "--json", "--from", "--to", "--req",
    }
    skip_vals = set(SIGNERS.keys()) | set(SIGNERS.values())
    for a in rest:
        if skip_next:
            skip_next = False
            continue
        if a in flags_with_val:
            skip_next = True
            continue
        if a.startswith("-"):
            continue
        if a in skip_vals:
            continue
        out.append(a)
    return out


def take_payload(rest):
    data = {}
    raw = opt(rest, "--json")
    if raw:
        data.update(json.loads(raw))
    for key, name in (
        ("phase", "--phase"), ("who", "--who"), ("changed", "--changed"),
        ("proof", "--proof"), ("next", "--next"), ("from", "--from"),
        ("to", "--to"), ("req", "--req"),
    ):
        v = opt(rest, name)
        if v is not None:
            data[key] = v
    return data


def take_signer(rest):
    raw = opt(rest, "--signer")
    if raw in SIGNERS:
        return raw
    if raw:
        for k, v in SIGNERS.items():
            if v == raw or k == raw:
                return k
        return raw
    if rest and rest[-1] == "AID":
        return "AID"
    return "board-keeper"


def main():
    root, cmd, rest = parse_args(sys.argv)
    if not root:
        print(__doc__)
        return 2
    gh = flag(rest, "--gh") or cmd in ("setup",)
    payload = take_payload(rest)
    signer = take_signer(rest)
    if cmd == "setup":
        print(json.dumps(cmd_setup(root, owner=opt(rest, "--owner"),
                                   title=opt(rest, "--title")), indent=2))
        return 0
    if cmd == "status":
        print(json.dumps(cmd_status(root, gh=gh), indent=2))
        return 0
    if cmd == "apply":
        print(json.dumps(cmd_apply(root, gh=gh, payload=payload, signer=signer), indent=2))
        return 0
    if cmd == "note":
        pos = positional(rest)
        if len(pos) < 2:
            print("error: note needs ISSUE and TEXT", file=sys.stderr)
            return 2
        print(json.dumps(cmd_note(root, pos[0], " ".join(pos[1:]), signer,
                                  req_id=payload.get("req"),
                                  stage=payload.get("phase"), gh=True), indent=2))
        return 0
    if cmd == "comment":
        pos = positional(rest)
        if not pos:
            print("error: comment needs ISSUE", file=sys.stderr)
            return 2
        req_id = payload.get("req") or payload.get("usr")
        if not req_id or not proof_ok(payload.get("proof")):
            print("error: comment needs --req (USR or REQ) and --proof", file=sys.stderr)
            return 2
        board = load_board(root)
        nodes, edges, _ = load(root)
        usr_id = resolve_usr(req_id, nodes, edges, board)
        payload.setdefault("usr", usr_id)
        payload.setdefault("reqs", usr_facts(nodes, edges, usr_id).get("reqs") if usr_id in nodes else None)
        cur = payload.get("from") or (board.get("status") or {}).get(usr_id)
        nxt = payload.get("to") or cur
        stage = payload.get("phase")
        body, log_row = record_comment(
            root, usr_id, cur, nxt, payload, issue=pos[0], signer=signer,
            runner=None, nwo=board.get("nwo"), gh=True, kind=KIND_SYSTEM,
            stage=stage, sub_issue=pos[0] if stage else None)
        print(json.dumps({"issue": pos[0], "body": body, "log": log_row}, indent=2))
        return 0
    if cmd == "event":
        pos = positional(rest)
        if len(pos) < 2:
            print("error: event needs KIND and USR or REQ id", file=sys.stderr)
            return 2
        print(json.dumps(cmd_event(root, pos[0], pos[1], gh=gh, payload=payload,
                                   signer=signer), indent=2))
        return 0
    if cmd == "trail":
        pos = positional(rest)
        if not pos:
            print("error: trail needs USR or REQ id", file=sys.stderr)
            return 2
        filt = KIND_SYSTEM if flag(rest, "--system") else (KIND_NOTE if flag(rest, "--notes") else None)
        out = cmd_trail(root, pos[0], kind=filt)
        for block in out["rendered"]:
            print(block)
            print("")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
