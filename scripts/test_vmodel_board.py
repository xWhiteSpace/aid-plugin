#!/usr/bin/env python3
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_board import (  # noqa: E402
    COLUMNS, KIND_NOTE, KIND_SYSTEM, MARKER_DASHBOARD, MARKER_NOTE,
    MARKER_SYSTEM, PHASES, cmd_event, cmd_note, cmd_trail, column_from_subs,
    desired_column, format_block, format_note, format_parent_dashboard,
    format_sub_dashboard, format_system, link_reqs, log_matches, next_column,
    plan_rows, proof_ok, read_log, req_facts, resolve_usr, sign_comment,
    skipped_stages, usr_facts, check_parent, processes_for, PROCESS_ORDER,
    gate_effect, cmd_attach, cmd_gate, cmd_setup, LANE_PROCESSES,
)
from vmodel_common import load  # noqa: E402

def write_min_ssot(root):
    os.makedirs(os.path.join(root, "registries"))
    os.makedirs(os.path.join(root, "graph"))
    usr = {
        "USR-KTL-001": {
            "id": "USR-KTL-001", "kind": "USR", "project": "KTL",
            "title": "Boil water", "statement": "Boil water at the press of a button.",
            "status": "published", "effort": {"lane": "tiny"},
        }
    }
    req = {
        "REQ-KTL-001": {
            "id": "REQ-KTL-001", "kind": "REQ", "project": "KTL",
            "title": "Boil water", "statement": "Pressing Start heats water until it boils.",
            "status": "published",
        }
    }
    fnc = {
        "FNC-KTL-001": {
            "id": "FNC-KTL-001", "kind": "FNC", "project": "KTL",
            "title": "Start heat", "statement": "Start heats the water.",
            "status": "published",
        }
    }
    unt = {
        "UNT-KTL-001": {
            "id": "UNT-KTL-001", "kind": "UNT", "project": "KTL",
            "title": "start_guard", "statement": "Heater runs when start is pressed.",
            "status": "published", "source_files": ["src/start_guard.py"],
        }
    }
    edges = [
        {"from": "REQ-KTL-001", "to": "USR-KTL-001", "type": "derives"},
        {"from": "FNC-KTL-001", "to": "REQ-KTL-001", "type": "implements"},
        {"from": "UNT-KTL-001", "to": "FNC-KTL-001", "type": "refines"},
        {"from": "UNT-KTL-001", "to": "src/start_guard.py", "type": "coded_in"},
    ]
    pairs = (
        ("usr.json", usr), ("req.json", req), ("fnc.json", fnc), ("unt.json", unt),
    )
    for name, data in pairs:
        with open(os.path.join(root, "registries", name), "w", encoding="utf-8") as f:
            json.dump(data, f)
    with open(os.path.join(root, "graph", "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges, f)
    with open(os.path.join(root, "graph", "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"graph_version": 1, "projects": ["KTL"]}, f)
    with open(os.path.join(root, "board.json"), "w", encoding="utf-8") as f:
        json.dump({"status": {}, "sub_issues": {}, "issues": {}}, f)


class NextColumn(unittest.TestCase):
    def test_new_item_starts_backlog(self):
        self.assertEqual(next_column(None, "Done"), "Backlog")

    def test_one_step(self):
        self.assertEqual(next_column("Backlog", "In review"), "Ready")
        self.assertEqual(next_column("Ready", "Done"), "In progress")
        self.assertEqual(next_column("In progress", "In review"), "In review")

    def test_no_skip_and_no_back(self):
        self.assertEqual(next_column("In review", "Backlog"), "In review")
        self.assertEqual(next_column("Done", "Done"), "Done")
        self.assertEqual(COLUMNS[-1], "Done")


class Desired(unittest.TestCase):
    def test_intake(self):
        self.assertEqual(desired_column({}), "Backlog")
        self.assertEqual(desired_column({}, event="intake"), "Backlog")

    def test_published_ready(self):
        self.assertEqual(desired_column({"published": True}), "Ready")

    def test_coding(self):
        self.assertEqual(desired_column({"published": True, "coding_started": True}),
                         "In progress")

    def test_pr_open(self):
        self.assertEqual(desired_column({"coding_started": True}, {"pr_open": True}),
                         "In review")

    def test_done_needs_merge(self):
        ssot = {"published": True, "coding_started": True, "tests_pass": True}
        self.assertEqual(desired_column(ssot, event="pr_merged"), "In progress")
        self.assertEqual(desired_column(ssot, {"pr_merged": True}), "Done")


class Subs(unittest.TestCase):
    def test_backlog_until_requirements_closed(self):
        self.assertEqual(column_from_subs({}), "Backlog")
        self.assertEqual(column_from_subs({
            "Requirements": {"state": "open"},
        }), "Backlog")

    def test_ready_when_design_closed(self):
        subs = {p: {"state": "closed", "reason": "completed"} for p in PHASES[:4]}
        for p in PHASES[4:]:
            subs[p] = {"state": "open"}
        self.assertEqual(column_from_subs(subs), "Ready")

    def test_in_progress_when_code_open_with_branch(self):
        subs = {p: {"state": "closed", "reason": "completed"} for p in PHASES[:4]}
        subs["Code"] = {"state": "open", "branch": True}
        for p in PHASES[5:]:
            subs[p] = {"state": "open"}
        self.assertEqual(column_from_subs(subs), "In progress")

    def test_done_needs_all_closed_merge_and_acceptance(self):
        subs = {p: {"state": "closed", "reason": "completed"} for p in PHASES}
        self.assertEqual(column_from_subs(subs), "In progress")
        self.assertEqual(column_from_subs(subs, {"pr_open": True}), "In review")
        self.assertEqual(column_from_subs(subs, {"pr_merged": True}), "In review")
        self.assertEqual(column_from_subs(subs, {
            "pr_merged": True, "acceptance_ok": True,
        }), "Done")

    def test_tiny_lane_skips(self):
        skip = skipped_stages({"lane": "tiny", "stages": ["USR", "REQ"]})
        self.assertIn("Functions", skip)
        self.assertIn("Unit test", skip)
        self.assertNotIn("Requirements", skip)
        self.assertNotIn("Acceptance test", skip)

    def test_empty_test_levels(self):
        skip = skipped_stages({"lane": "large"}, [{"level": "integration", "reason": "no INT"}])
        self.assertEqual(skip, ["Integration test"])


class Kettle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, ".vmodel")
        write_min_ssot(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_ktl_001_in_progress(self):
        nodes, edges, _ = load(self.root)
        facts = req_facts(nodes, edges, "REQ-KTL-001")
        self.assertTrue(facts["published"])
        self.assertTrue(facts["coding_started"])
        self.assertFalse(facts["tests_pass"])
        self.assertFalse(facts["acceptance_ok"])
        self.assertEqual(desired_column(facts), "In progress")
        self.assertEqual(resolve_usr("REQ-KTL-001", nodes, edges), "USR-KTL-001")
        usr = usr_facts(nodes, edges, "USR-KTL-001")
        self.assertEqual(usr["reqs"], ["REQ-KTL-001"])
        self.assertEqual(usr["scope"]["Requirements"][0]["id"], "REQ-KTL-001")
        rows = {r["id"]: r for r in plan_rows(nodes, edges)}
        self.assertEqual(rows["USR-KTL-001"]["desired"], "In progress")
        self.assertEqual(rows["USR-KTL-001"]["reqs"], ["REQ-KTL-001"])
        self.assertNotIn("REQ-KTL-001", rows)
        self.assertEqual(next_column(None, rows["USR-KTL-001"]["desired"]), "Backlog")

    def test_amend_links_earlier_parent(self):
        board = {}
        link_reqs(board, "USR-KTL-001", ["REQ-KTL-001"])
        link_reqs(board, "USR-KTL-099", ["REQ-KTL-001"])
        self.assertEqual(board["req_parent"]["REQ-KTL-001"], "USR-KTL-099")
        self.assertEqual(board["amended_from"]["REQ-KTL-001"], "USR-KTL-001")


class Comment(unittest.TestCase):
    def test_sign(self):
        self.assertIn("— A.I.D", sign_comment("hello", "AID"))
        self.assertIn("— Issue Manager", sign_comment("moved", "issue-manager"))
        self.assertIn("— Adept", sign_comment("coded start_guard", "adept"))

    def test_block_labels(self):
        body = format_block(
            "USR-KTL-001", "Ready", "In progress", "Code",
            "adept ; Last Boss slice", "UNT-KTL-001; src/start_guard.py",
            "test-master unit tests", "abc123", "first entry")
        self.assertIn("**USR-KTL-001: Ready → In progress**", body)
        for label in ("Phase done:", "Who:", "Changed:", "Next:", "Proof:", "Back:"):
            self.assertIn("**%s**" % label, body)
        sys_body = format_system(body, "board-keeper")
        self.assertTrue(sys_body.startswith(MARKER_SYSTEM))
        self.assertIn("[system]", sys_body)
        self.assertIn("— Issue Manager", sys_body)

    def test_note_marker(self):
        body = format_note("Coded start_guard. Concern: no dry-run log.", "adept")
        self.assertTrue(body.startswith(MARKER_NOTE))
        self.assertIn("— Adept", body)
        self.assertNotIn("[system]", body)

    def test_dashboards(self):
        stages = {p: {"state": "open", "number": i + 1, "owner": "adept" if p == "Code" else "req-guardian"}
                  for i, p in enumerate(PHASES)}
        reqs = [{
            "id": "REQ-KTL-001",
            "statement": "Pressing Start heats water until it boils.",
            "stage": "Code",
            "acceptance": "TST-KTL-001",
            "proof": "abc123",
            "amended_from": None,
        }]
        parent = format_parent_dashboard(
            "USR-KTL-001", "As a kettle user I want to boil water at the press of a button so I can make tea fast.",
            "In progress", stages, "none", "2026-10-16T05:00:00Z", reqs=reqs)
        self.assertTrue(parent.startswith(MARKER_DASHBOARD))
        self.assertIn("USR-KTL-001", parent)
        self.assertIn("| REQ | Sentence | Stage | Acceptance TST | Proof | Earlier |", parent)
        self.assertIn("REQ-KTL-001", parent)
        self.assertIn("| # | Stage | Status | Owner | Proof | Issue |", parent)
        self.assertIn("Code", parent)
        sub = format_sub_dashboard(
            "Code", "#12 USR-KTL-001", "adept", "open",
            [{"id": "UNT-KTL-001", "status": "published"}],
            "abc123", "Last Boss slice", "2026-10-16T05:00:00Z")
        self.assertTrue(sub.startswith(MARKER_DASHBOARD))
        self.assertIn("**Parent:**", sub)
        self.assertIn("UNT-KTL-001 (published)", sub)

    def test_no_column_change_header(self):
        body = format_block(
            "USR-KTL-001", "Ready", "Ready", "Functions",
            "functional-specs ; SSOT Gate published", "FNC-KTL-001",
            "system-designer", "baseline g1", "first entry")
        self.assertIn("**USR-KTL-001: no column change**", body)

    def test_proof_ok(self):
        self.assertFalse(proof_ok(""))
        self.assertFalse(proof_ok("  "))
        self.assertTrue(proof_ok("abc123"))


class EventLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, ".vmodel")
        write_min_ssot(self.root)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_no_proof_no_move(self):
        out = cmd_event(self.root, "intake", "REQ-KTL-001", payload={"phase": "Requirements"})
        self.assertEqual(out.get("blocked"), "no proof")
        self.assertEqual(read_log(self.root), [])
        with open(os.path.join(self.root, "board.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f).get("status"), {})

    def test_event_writes_block_and_log(self):
        out = cmd_event(self.root, "intake", "REQ-KTL-001", payload={
            "phase": "Requirements",
            "who": "req-guardian ; intake",
            "changed": "USR-KTL-001, REQ-KTL-001",
            "next": "ssot-gate Gate 1",
            "proof": "proposal USR-KTL-001",
        })
        self.assertTrue(out.get("moved"))
        self.assertEqual(out.get("id"), "USR-KTL-001")
        self.assertEqual(out.get("next"), "Backlog")
        self.assertIn("**USR-KTL-001: (new) → Backlog**", out["comment"])
        self.assertIn(MARKER_SYSTEM, out["comment"])
        self.assertIn("[system]", out["comment"])
        log = read_log(self.root)
        self.assertGreaterEqual(len(log), 1)
        self.assertTrue(all((r.get("kind") or KIND_SYSTEM) == KIND_SYSTEM for r in log))
        self.assertTrue(all(r.get("usr") == "USR-KTL-001" for r in log))
        self.assertTrue(all("REQ-KTL-001" in (r.get("reqs") or []) for r in log))
        with open(os.path.join(self.root, "board.json"), encoding="utf-8") as f:
            board = json.load(f)
        self.assertEqual(len(board["sub_issues"]["USR-KTL-001"]), 9)
        self.assertEqual(board["req_parent"]["REQ-KTL-001"], "USR-KTL-001")
        phase = cmd_event(self.root, "phase", "REQ-KTL-001", payload={
            "phase": "Functions",
            "who": "functional-specs ; SSOT Gate published",
            "changed": "FNC-KTL-001",
            "next": "system-designer",
            "proof": "baseline 2026-10-16-g1",
        })
        self.assertFalse(phase.get("moved"))
        self.assertIn("no column change", phase["comment"])
        trail = cmd_trail(self.root, "REQ-KTL-001", kind=KIND_SYSTEM)
        self.assertEqual(trail["usr"], "USR-KTL-001")
        self.assertGreaterEqual(len(trail["rendered"]), 2)
        note = cmd_note(self.root, "s1", "Minted USR and REQ for boil.", "req-guardian",
                        req_id="REQ-KTL-001", stage="Requirements", gh=False)
        self.assertIn(MARKER_NOTE, note["body"])
        self.assertIn("— Req Guardian", note["body"])
        self.assertEqual(note["usr"], "USR-KTL-001")
        sys_only = cmd_trail(self.root, "USR-KTL-001", kind=KIND_SYSTEM)
        notes_only = cmd_trail(self.root, "REQ-KTL-001", kind=KIND_NOTE)
        self.assertTrue(all(MARKER_SYSTEM in b for b in sys_only["rendered"]))
        self.assertTrue(all(MARKER_NOTE in b for b in notes_only["rendered"]))
        self.assertEqual(len(notes_only["entries"]), 1)


GOOD = """### Kind
Requirement

### What
Boil water

### Why
A person making tea

### When
SWE.3

### Criteria
Water boils then heat stops

### How
One button starts a timed heat
"""


class ParentForm(unittest.TestCase):
    def test_five_fields_pass(self):
        out = check_parent(GOOD, allowed=["SWE.3", "SWE.4"])
        self.assertTrue(out["ok"])
        self.assertEqual(out["kind"], "SYS.1")

    def test_missing_heading(self):
        body = GOOD.replace("### Why\nA person making tea\n", "")
        out = check_parent(body)
        self.assertFalse(out["ok"])
        self.assertIn("missing Why", out["errors"])

    def test_fourth_line(self):
        body = GOOD.replace("### What\nBoil water\n", "### What\nBoil water\nline two\nline three\nline four\n")
        out = check_parent(body)
        self.assertFalse(out["ok"])
        self.assertTrue(any("What" in e for e in out["errors"]))

    def test_when_outside_ten(self):
        body = GOOD.replace("SWE.3", "tomorrow")
        out = check_parent(body)
        self.assertFalse(out["ok"])
        self.assertIn("When is not a process id", out["errors"])

    def test_when_not_on_list(self):
        out = check_parent(GOOD, allowed=["SWE.4"])
        self.assertFalse(out["ok"])
        self.assertIn("When is not on the process list", out["errors"])

    def test_lanes(self):
        self.assertEqual(processes_for("tiny"), ["SWE.3", "SWE.4"])
        self.assertEqual(processes_for("large"), PROCESS_ORDER)
        self.assertEqual(len(LANE_PROCESSES["large"]), 10)

    def test_requirement_and_fix(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, ".vmodel")
        os.makedirs(root)
        with open(os.path.join(root, "board.json"), "w", encoding="utf-8") as f:
            json.dump({"nwo": "me/app"}, f)
        req = cmd_attach(root, 12, "USR-APP-001", "Requirement",
                         ["SWE.3", "SWE.4"], what="Boil water")
        self.assertEqual(req["kind"], "SYS.1")
        self.assertEqual(req["processes"], ["SWE.3", "SWE.4"])
        self.assertEqual(req["title"], "USR-APP-001 · Boil water")
        fix = cmd_attach(root, 13, "USR-APP-002", "Fix",
                         ["SWE.3", "SWE.4"], what="Heat never stops")
        self.assertEqual(fix["kind"], "SUP.9")
        self.assertNotIn("SYS.2", fix["processes"])
        self.assertTrue(fix["title"].startswith("SUP.9 ·"))
        shutil.rmtree(tmp)

    def test_gate_token(self):
        self.assertFalse(gate_effect("please start", "AID", "Backlog")["moved"])
        accept = gate_effect("/gate-Parent-accept\nkind SYS.1", "AID", "Backlog")
        self.assertFalse(accept["moved"])
        leave = gate_effect("/gate-Parent-breakdown\nSWE.3 SWE.4", "AID", "Backlog")
        self.assertTrue(leave["moved"])
        self.assertEqual(leave["to"], "Ready")
        wrong = gate_effect("/gate-Parent-breakdown\n", "adept", "Backlog")
        self.assertFalse(wrong["moved"])

    def test_breakdown_leaves_backlog(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, ".vmodel")
        os.makedirs(root)
        with open(os.path.join(root, "board.json"), "w", encoding="utf-8") as f:
            json.dump({"issues": {}, "nwo": "me/app"}, f)
        cmd_attach(root, 12, "USR-APP-001", "Requirement", ["SWE.3", "SWE.4"], what="Boil water")
        out = cmd_gate(root, "/gate-Parent-breakdown\nSWE.3, SWE.4", signer="AID", issue=12)
        self.assertTrue(out["moved"])
        self.assertEqual(out["column"], "Ready")
        with open(os.path.join(root, "board.json"), encoding="utf-8") as f:
            board = json.load(f)
        self.assertEqual(board["sub_issues"]["USR-APP-001"]["SWE.3"]["column"], "Ready")
        self.assertEqual(board["sub_issues"]["USR-APP-001"]["SWE.4"]["column"], "Backlog")
        board["sub_issues"]["USR-APP-001"]["SWE.3"]["number"] = 44
        board["sub_issues"]["USR-APP-001"]["SWE.3"]["column"] = "In progress"
        with open(os.path.join(root, "board.json"), "w", encoding="utf-8") as f:
            json.dump(board, f)
        noted = cmd_note(root, 44, "Heat path is in.", "adept", gh=False)
        self.assertTrue(noted["moved"])
        with open(os.path.join(root, "board.json"), encoding="utf-8") as f:
            board = json.load(f)
        self.assertEqual(board["sub_issues"]["USR-APP-001"]["SWE.3"]["column"], "In review")
        self.assertEqual(board["status"]["USR-APP-001"], "In review")
        shutil.rmtree(tmp)


class KanbanSetup(unittest.TestCase):
    def _runner(self, calls):
        def runner(argv, stderr=None):
            calls.append(argv)
            joined = " ".join(argv)
            if "view" in argv and "repo" in argv:
                return json.dumps({
                    "owner": {"login": "me"}, "name": "app", "nameWithOwner": "me/app",
                })
            if "createProjectV2" in joined:
                return json.dumps({"data": {"createProjectV2": {"projectV2": {
                    "id": "PVT_1", "number": 3, "url": "https://example"}}}})
            if "repository(owner:" in joined:
                return json.dumps({"data": {"repository": {"id": "R_1", "owner": {"id": "O_1"}}}})
            if "groupByFields" in joined:
                return json.dumps({"data": {"node": {
                    "fields": {"nodes": [{"id": "F_1", "name": "Status", "options": [
                        {"id": "o", "name": "Backlog"}]}]},
                    "views": {"nodes": [{"id": "V_1", "name": "View 1", "layout": "TABLE_LAYOUT",
                                         "groupByFields": {"nodes": [{"name": "Status"}]}}]},
                }}})
            if "updateProjectV2View" in joined:
                return json.dumps({"data": {"updateProjectV2View": {"projectV2View": {
                    "id": "V_1", "name": "Board", "layout": "BOARD_LAYOUT"}}}})
            if "updateProjectV2Field" in joined:
                return json.dumps({"data": {"updateProjectV2Field": {"projectV2Field": {
                    "id": "F_1", "name": "Workflow Status",
                    "options": [{"id": "a", "name": c} for c in COLUMNS]}}}})
            return json.dumps({"data": {}})
        return runner

    def test_create_sends_graphql(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, ".vmodel")
        os.makedirs(root)
        calls = []
        out = cmd_setup(root, runner=self._runner(calls))
        blob = "\n".join(" ".join(c) for c in calls)
        self.assertIn("createProjectV2", blob)
        self.assertIn("Workflow Status", blob)
        self.assertIn("BOARD_LAYOUT", blob)
        self.assertTrue(out["created"])
        self.assertEqual(out["field"], "Workflow Status")
        self.assertFalse(out["grouped_by_workflow_status"])
        self.assertTrue(os.path.isfile(os.path.join(tmp, ".github", "ISSUE_TEMPLATE", "aid-request.yml")))
        self.assertTrue(os.path.isfile(os.path.join(tmp, ".github", "workflows", "aid-gates.yml")))
        shutil.rmtree(tmp)

    def test_existing_project_does_not_create(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, ".vmodel")
        os.makedirs(root)
        with open(os.path.join(root, "board.json"), "w", encoding="utf-8") as f:
            json.dump({"project_id": "PVT_9", "project_number": 9}, f)
        calls = []
        out = cmd_setup(root, runner=self._runner(calls))
        self.assertTrue(out["already"])
        self.assertFalse(out["created"])
        self.assertEqual(calls, [])
        shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
