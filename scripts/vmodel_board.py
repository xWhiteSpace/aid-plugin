#!/usr/bin/env python3
"""Board view of SSOT + GitHub. Not an SSOT publisher.

Columns: Backlog → Ready → In progress → In review → Done.
Never skip a column. Never Done without a merged PR.
No proof, no move. Every phase posts a trail block.

Usage:
  python3 vmodel_board.py .vmodel status
  python3 vmodel_board.py .vmodel setup [--owner LOGIN] [--title TITLE]
  python3 vmodel_board.py .vmodel apply [--gh] --proof TEXT [--phase P] ...
  python3 vmodel_board.py .vmodel event KIND REQ-ID --proof TEXT [--phase P] [--who W] [--changed C] [--next N] [--json '{...}'] [--gh]
  python3 vmodel_board.py .vmodel comment ISSUE --req ID --proof TEXT [--phase P] ...
  python3 vmodel_board.py .vmodel trail REQ-ID
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
BOARD_FILE = "board.json"
LOG_FILE = "board-log.jsonl"
DEFAULT_TITLE = "A.I.D board"
SIGNERS = {"AID": "A.I.D", "board-keeper": "Board Keeper"}
EVENTS = {"intake", "published", "coding", "pr_open", "pr_merged", "phase"}
DEFAULT_PHASE = {
    "intake": "Requirements",
    "published": "Requirements",
    "coding": "Code",
    "pr_open": "System test",
    "pr_merged": "Acceptance test",
}


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


def last_back(root, req_id):
    for row in reversed(read_log(root)):
        if row.get("req") == req_id:
            return row.get("comment_url") or row.get("time") or "first entry"
    return "first entry"


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
    return {
        "published": published,
        "design_ready": published,
        "coding_started": coded or bool(unts and any(
            (nodes.get(u) or {}).get("source_files") for u in unts)),
        "tests_pass": tests_pass,
        "statement": n.get("statement") or n.get("title") or nid,
        "title": n.get("title") or nid,
        "project": n.get("project"),
    }


def desired_column(ssot, gh=None, event=None):
    gh = gh or {}
    if event == "phase":
        return None
    if gh.get("pr_merged") and (ssot.get("tests_pass") or gh.get("last_boss_ok")):
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


def plan_rows(nodes, edges, gh_map=None, event=None, event_req=None):
    gh_map = gh_map or {}
    rows = []
    for n in by_kind(nodes, "REQ"):
        if n.get("status") == "retired":
            continue
        nid = n["id"]
        ssot = req_facts(nodes, edges, nid)
        ev = event if event_req in (None, nid) else None
        desired = desired_column(ssot, gh_map.get(nid), ev)
        rows.append({
            "id": nid,
            "title": ssot["title"],
            "statement": ssot["statement"],
            "desired": desired,
            "published": ssot["published"],
            "coding_started": ssot["coding_started"],
            "tests_pass": ssot["tests_pass"],
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
    who = SIGNERS.get(signer, SIGNERS["board-keeper"])
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
        "items": prev.get("items") or {},
        "status": prev.get("status") or {},
        "pending": prev.get("pending") or {},
    }
    path = save_board(root, board)
    return {"board": path, "project_number": number, "url": proj.get("url")}


def cmd_status(root, gh=False, runner=None):
    nodes, edges, _ = load(root)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    rows = plan_rows(nodes, edges, gh_map)
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
            return data.get("html_url")
        run_gh(["issue", "comment", str(issue), "--body", body], runner=runner)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, TypeError):
        return None
    return None


def ensure_issue(root, row, board, runner=None, title=None):
    issues = board.setdefault("issues", {})
    if row["id"] in issues:
        return issues[row["id"]], False
    label = row["label"]
    try:
        run_gh(["label", "create", label, "--description", "A.I.D requirement",
                "--color", "0E8A16"], runner=runner)
    except (OSError, subprocess.CalledProcessError):
        pass
    issue_title = title or "%s %s" % (row["id"], row["title"])
    body = "%s\n\n%s" % (row["id"], row["statement"])
    created = gh_json([
        "issue", "create", "--title", issue_title,
        "--body", body, "--label", label, "--json", "number,url",
    ], runner=runner)
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
                   runner=None, nwo=None, gh=False):
    proof = (payload.get("proof") or "").strip()
    if not proof_ok(proof):
        return None, {"id": req_id, "blocked": "no proof"}
    back = last_back(root, req_id)
    text = format_block(
        req_id, current, nxt,
        payload.get("phase"), payload.get("who"), payload.get("changed"),
        payload.get("next"), proof, back)
    body = sign_comment(text, signer)
    url = None
    if gh and issue is not None:
        url = post_comment(issue, body, runner=runner, nwo=nwo)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {
        "time": now,
        "issue": issue,
        "req": req_id,
        "from": current,
        "to": nxt,
        "phase": payload.get("phase"),
        "who": payload.get("who"),
        "changed": payload.get("changed"),
        "proof": proof,
        "comment_url": url,
        "signer": SIGNERS.get(signer, SIGNERS["board-keeper"]),
    }
    append_log(root, row)
    return body, row


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
    for row in plan_rows(nodes, edges, gh_map):
        cur = current.get(row["id"])
        nxt = next_column(cur, row["desired"])
        if nxt == cur:
            continue
        fields = merge_payload(pending.get(row["id"]), payload)
        if not proof_ok(fields.get("proof")):
            blocked.append({"id": row["id"], "from": cur, "to": nxt, "blocked": "no proof"})
            continue
        issue = None
        created = False
        if gh:
            issue, created = ensure_issue(root, row, board, runner=runner)
            if created:
                nxt = "Backlog"
        body, _log = record_comment(
            root, row["id"], cur, nxt, fields, issue=issue, signer=signer,
            runner=runner, nwo=board.get("nwo"), gh=gh)
        item = (board.get("items") or {}).get(row["id"])
        if gh and item and nxt:
            try:
                set_status(board, item, nxt, runner=runner)
            except (OSError, subprocess.CalledProcessError):
                pass
        current[row["id"]] = nxt
        pending.pop(row["id"], None)
        moves.append({
            "id": row["id"], "from": cur, "to": nxt, "issue": issue,
            "comment": body,
        })
    board["status"] = current
    board["pending"] = pending
    save_board(root, board)
    return {"moves": moves, "blocked": blocked}


def cmd_event(root, kind, req_id, gh=False, runner=None, payload=None, signer="board-keeper"):
    if kind not in EVENTS:
        raise SystemExit("error: event must be one of %s" % ", ".join(sorted(EVENTS)))
    nodes, edges, _ = load(root)
    if req_id not in nodes:
        raise SystemExit("error: %s is not in the registries" % req_id)
    payload = dict(payload or {})
    payload.setdefault("phase", DEFAULT_PHASE.get(kind))
    if not proof_ok(payload.get("proof")):
        return {"id": req_id, "event": kind, "blocked": "no proof"}
    ssot = req_facts(nodes, edges, req_id)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    gh_one = gh_map.get(req_id) or {}
    if kind == "pr_merged" and not gh_one.get("pr_merged"):
        return {"id": req_id, "blocked": "Done needs a merged pull request"}
    board = load_board(root)
    cur = (board.get("status") or {}).get(req_id)
    desired = desired_column(ssot, gh_one, event=kind)
    if kind == "phase" or desired is None:
        nxt = cur
    else:
        nxt = next_column(cur, desired)
    issue = (board.get("issues") or {}).get(req_id)
    if gh and issue is None:
        row = {
            "id": req_id, "title": ssot["title"], "statement": ssot["statement"],
            "label": req_id,
        }
        issue, created = ensure_issue(root, row, board, runner=runner)
        if created:
            nxt = "Backlog"
            cur = None
    body, log_row = record_comment(
        root, req_id, cur, nxt, payload, issue=issue, signer=signer,
        runner=runner, nwo=board.get("nwo"), gh=gh)
    moved = nxt != cur
    if moved:
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
    save_board(root, board)
    return {
        "id": req_id,
        "event": kind,
        "current": cur,
        "desired": desired,
        "next": nxt,
        "moved": moved,
        "comment": body,
        "log": log_row,
    }


def cmd_trail(root, req_id):
    rows = [r for r in read_log(root) if r.get("req") == req_id]
    rendered = []
    for idx, r in enumerate(rows):
        if idx == 0:
            back_val = "first entry"
        else:
            back_val = rows[idx - 1].get("comment_url") or rows[idx - 1].get("time") or "first entry"
        text = format_block(
            r.get("req"), r.get("from"), r.get("to"), r.get("phase"),
            r.get("who"), r.get("changed"), r.get("next"), r.get("proof"),
            back_val)
        signer = "AID" if r.get("signer") == "A.I.D" else "board-keeper"
        rendered.append(sign_comment(text, signer))
    return {"req": req_id, "entries": rows, "rendered": rendered}


def parse_args(argv):
    root = None
    cmd = "status"
    rest = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("status", "setup", "apply", "comment", "event", "trail"):
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
    for a in rest:
        if skip_next:
            skip_next = False
            continue
        if a in flags_with_val:
            skip_next = True
            continue
        if a.startswith("-"):
            continue
        if a in ("AID", "board-keeper"):
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
    if flag(rest, "--signer") and opt(rest, "--signer") == "AID":
        return "AID"
    if rest and rest[-1] == "AID":
        return "AID"
    return opt(rest, "--signer") or "board-keeper"


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
    if cmd == "comment":
        pos = positional(rest)
        if not pos:
            print("error: comment needs ISSUE", file=sys.stderr)
            return 2
        req_id = payload.get("req")
        if not req_id or not proof_ok(payload.get("proof")):
            print("error: comment needs --req and --proof (same trail block)", file=sys.stderr)
            return 2
        board = load_board(root)
        cur = payload.get("from") or (board.get("status") or {}).get(req_id)
        nxt = payload.get("to") or cur
        body, log_row = record_comment(
            root, req_id, cur, nxt, payload, issue=pos[0], signer=signer,
            runner=None, nwo=board.get("nwo"), gh=True)
        print(json.dumps({"issue": pos[0], "body": body, "log": log_row}, indent=2))
        return 0
    if cmd == "event":
        pos = positional(rest)
        if len(pos) < 2:
            print("error: event needs KIND and REQ id", file=sys.stderr)
            return 2
        print(json.dumps(cmd_event(root, pos[0], pos[1], gh=gh, payload=payload,
                                   signer=signer), indent=2))
        return 0
    if cmd == "trail":
        pos = positional(rest)
        if not pos:
            print("error: trail needs REQ id", file=sys.stderr)
            return 2
        out = cmd_trail(root, pos[0])
        for block in out["rendered"]:
            print(block)
            print("")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
