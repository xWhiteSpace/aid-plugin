#!/usr/bin/env python3
"""Board view of SSOT + GitHub. Not an SSOT publisher.

Columns: Backlog → Ready → In progress → In review → Done.
Never skip a column. Never Done without a merged PR.

Usage:
  python3 vmodel_board.py .vmodel status
  python3 vmodel_board.py .vmodel setup [--owner LOGIN] [--title TITLE]
  python3 vmodel_board.py .vmodel apply [--gh]
  python3 vmodel_board.py .vmodel comment ISSUE TEXT [--signer AID|board-keeper]
  python3 vmodel_board.py .vmodel event KIND REQ-ID [--gh]
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_common import by_kind, in_edges, load, out_edges  # noqa: E402

COLUMNS = ["Backlog", "Ready", "In progress", "In review", "Done"]
BOARD_FILE = "board.json"
DEFAULT_TITLE = "A.I.D board"
SIGNERS = {"AID": "A.I.D", "board-keeper": "Board Keeper"}
EVENTS = {"intake", "published", "coding", "pr_open", "pr_merged"}


def board_path(root):
    return os.path.join(root, BOARD_FILE)


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
    board = {
        "title": title,
        "owner": owner,
        "repo": ids.get("repo"),
        "nwo": ids.get("nwo"),
        "project_number": number,
        "project_id": project_id,
        "status_field_id": field_id,
        "status_options": {c: opts.get(c) for c in COLUMNS},
        "issues": load_board(root).get("issues") or {},
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


def comment_issue(issue, text, signer="board-keeper", runner=None):
    body = sign_comment(text, signer)
    run_gh(["issue", "comment", str(issue), "--body", body], runner=runner)
    return body


def ensure_issue(root, row, board, runner=None):
    issues = board.setdefault("issues", {})
    if row["id"] in issues:
        return issues[row["id"]], False
    label = row["label"]
    try:
        run_gh(["label", "create", label, "--description", "A.I.D requirement",
                "--color", "0E8A16"], runner=runner)
    except (OSError, subprocess.CalledProcessError):
        pass
    body = "%s\n\n%s" % (row["id"], row["statement"])
    created = gh_json([
        "issue", "create", "--title", "%s %s" % (row["id"], row["title"]),
        "--body", body, "--label", label, "--json", "number,url",
    ], runner=runner)
    num = created.get("number")
    issues[row["id"]] = num
    url = created.get("url")
    if board.get("project_number") and url:
        try:
            run_gh([
                "project", "item-add", str(board["project_number"]),
                "--owner", board.get("owner") or "",
                "--url", url,
            ], runner=runner)
        except (OSError, subprocess.CalledProcessError):
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


def cmd_apply(root, gh=False, runner=None):
    board = load_board(root)
    nodes, edges, _ = load(root)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    current = board.get("status") or {}
    moves = []
    for row in plan_rows(nodes, edges, gh_map):
        cur = current.get(row["id"])
        nxt = next_column(cur, row["desired"])
        if nxt == cur:
            continue
        issue = None
        created = False
        if gh:
            issue, created = ensure_issue(root, row, board, runner=runner)
            if created:
                nxt = "Backlog"
        why = {
            "Backlog": "new requirement on the board",
            "Ready": "REQ published at the SSOT gate",
            "In progress": "coding started",
            "In review": "a pull request references this issue",
            "Done": "pull request merged and tests/Last Boss hold",
        }.get(nxt, "status update")
        text = "%s moved %s → %s (%s)." % (row["id"], cur or "(new)", nxt, why)
        if gh and issue:
            comment_issue(issue, text, signer="board-keeper", runner=runner)
        current[row["id"]] = nxt
        moves.append({"id": row["id"], "from": cur, "to": nxt, "issue": issue, "comment": text})
    board["status"] = current
    save_board(root, board)
    return {"moves": moves}


def cmd_event(root, kind, req_id, gh=False, runner=None):
    if kind not in EVENTS:
        raise SystemExit("error: event must be one of %s" % ", ".join(sorted(EVENTS)))
    nodes, edges, _ = load(root)
    if req_id not in nodes:
        raise SystemExit("error: %s is not in the registries" % req_id)
    ssot = req_facts(nodes, edges, req_id)
    gh_map = read_gh_state(root, runner=runner) if gh else {}
    gh_one = gh_map.get(req_id) or {}
    if kind == "pr_merged" and not gh_one.get("pr_merged"):
        return {"id": req_id, "blocked": "Done needs a merged pull request"}
    desired = desired_column(ssot, gh_one, event=kind)
    board = load_board(root)
    cur = (board.get("status") or {}).get(req_id)
    nxt = next_column(cur, desired)
    return {"id": req_id, "event": kind, "current": cur, "desired": desired, "next": nxt}


def parse_args(argv):
    root = None
    cmd = "status"
    rest = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("status", "setup", "apply", "comment", "event"):
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
    return [a for a in rest if not a.startswith("-") and a not in (
        "AID", "board-keeper")]


def main():
    root, cmd, rest = parse_args(sys.argv)
    if not root:
        print(__doc__)
        return 2
    gh = flag(rest, "--gh") or cmd in ("setup",)
    if cmd == "setup":
        print(json.dumps(cmd_setup(root, owner=opt(rest, "--owner"),
                                   title=opt(rest, "--title")), indent=2))
        return 0
    if cmd == "status":
        print(json.dumps(cmd_status(root, gh=gh), indent=2))
        return 0
    if cmd == "apply":
        print(json.dumps(cmd_apply(root, gh=gh), indent=2))
        return 0
    if cmd == "comment":
        pos = positional(rest)
        if len(pos) < 2:
            print("error: comment needs ISSUE and TEXT", file=sys.stderr)
            return 2
        signer = "AID" if flag(rest, "--signer") and opt(rest, "--signer") == "AID" else (
            opt(rest, "--signer") or "board-keeper")
        if rest and rest[-1] == "AID":
            signer = "AID"
        body = comment_issue(pos[0], " ".join(pos[1:]), signer=signer)
        print(json.dumps({"issue": pos[0], "body": body}, indent=2))
        return 0
    if cmd == "event":
        pos = positional(rest)
        if len(pos) < 2:
            print("error: event needs KIND and REQ id", file=sys.stderr)
            return 2
        print(json.dumps(cmd_event(root, pos[0], pos[1], gh=gh), indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
