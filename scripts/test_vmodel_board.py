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
    format_sub_dashboard, format_system, next_column, plan_rows, proof_ok,
    read_log, req_facts, sign_comment, skipped_stages,
)
from vmodel_common import load  # noqa: E402

KETTLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "examples", "electric-kettle", ".vmodel")


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

    def test_done_needs_all_closed_and_merge(self):
        subs = {p: {"state": "closed", "reason": "completed"} for p in PHASES}
        self.assertEqual(column_from_subs(subs), "In progress")
        self.assertEqual(column_from_subs(subs, {"pr_open": True}), "In review")
        self.assertEqual(column_from_subs(subs, {"pr_merged": True}), "Done")

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
    def test_ktl_001_in_progress(self):
        nodes, edges, _ = load(KETTLE)
        facts = req_facts(nodes, edges, "REQ-KTL-001")
        self.assertTrue(facts["published"])
        self.assertTrue(facts["coding_started"])
        self.assertFalse(facts["tests_pass"])
        self.assertEqual(desired_column(facts), "In progress")
        rows = {r["id"]: r for r in plan_rows(nodes, edges)}
        self.assertEqual(rows["REQ-KTL-001"]["desired"], "In progress")
        self.assertEqual(next_column(None, rows["REQ-KTL-001"]["desired"]), "Backlog")

    def test_sample_trail_covers_v(self):
        rows = [r for r in read_log(KETTLE) if r.get("req") == "REQ-KTL-001"]
        stages = [r["stage"] for r in rows
                  if r.get("stage") and (r.get("kind") or KIND_SYSTEM) == KIND_SYSTEM]
        self.assertEqual(stages, PHASES)
        self.assertTrue(all(r.get("sub_issue") for r in rows if r.get("stage") and r.get("kind") != KIND_NOTE))
        parent = [r["to"] for r in rows
                  if not r.get("stage") and (r.get("kind") or KIND_SYSTEM) == KIND_SYSTEM
                  and r.get("from") != r.get("to")]
        self.assertEqual(parent, COLUMNS)
        notes = [r for r in rows if r.get("kind") == KIND_NOTE]
        self.assertTrue(notes)


class Comment(unittest.TestCase):
    def test_sign(self):
        self.assertIn("— A.I.D", sign_comment("hello", "AID"))
        self.assertIn("— Board Keeper", sign_comment("moved", "board-keeper"))
        self.assertIn("— Adept", sign_comment("coded start_guard", "adept"))

    def test_block_labels(self):
        body = format_block(
            "REQ-KTL-001", "Ready", "In progress", "Code",
            "adept ; Last Boss slice", "UNT-KTL-001; src/start_guard.py",
            "test-master unit tests", "abc123", "first entry")
        self.assertIn("**REQ-KTL-001: Ready → In progress**", body)
        for label in ("Phase done:", "Who:", "Changed:", "Next:", "Proof:", "Back:"):
            self.assertIn("**%s**" % label, body)
        sys_body = format_system(body, "board-keeper")
        self.assertTrue(sys_body.startswith(MARKER_SYSTEM))
        self.assertIn("[system]", sys_body)
        self.assertIn("— Board Keeper", sys_body)

    def test_note_marker(self):
        body = format_note("Coded start_guard. Concern: no dry-run log.", "adept")
        self.assertTrue(body.startswith(MARKER_NOTE))
        self.assertIn("— Adept", body)
        self.assertNotIn("[system]", body)

    def test_dashboards(self):
        stages = {p: {"state": "open", "number": i + 1, "owner": "adept" if p == "Code" else "req-guardian"}
                  for i, p in enumerate(PHASES)}
        parent = format_parent_dashboard(
            "REQ-KTL-001", "Pressing Start heats water until it boils.",
            "In progress", stages, "none", "2026-10-16T05:00:00Z")
        self.assertTrue(parent.startswith(MARKER_DASHBOARD))
        self.assertIn("REQ-KTL-001", parent)
        self.assertIn("| # | Stage | Status | Owner | Proof | Issue |", parent)
        self.assertIn("Code", parent)
        sub = format_sub_dashboard(
            "Code", "#12 REQ-KTL-001", "adept", "open", "UNT-KTL-001",
            "abc123", "Last Boss slice", "2026-10-16T05:00:00Z")
        self.assertTrue(sub.startswith(MARKER_DASHBOARD))
        self.assertIn("**Parent:**", sub)
        self.assertIn("UNT-KTL-001", sub)

    def test_no_column_change_header(self):
        body = format_block(
            "REQ-KTL-001", "Ready", "Ready", "Functions",
            "functional-specs ; SSOT Gate published", "FNC-KTL-001",
            "system-designer", "baseline g1", "first entry")
        self.assertIn("**REQ-KTL-001: no column change**", body)

    def test_proof_ok(self):
        self.assertFalse(proof_ok(""))
        self.assertFalse(proof_ok("  "))
        self.assertTrue(proof_ok("abc123"))


class EventLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, ".vmodel")
        shutil.copytree(KETTLE, self.root)
        with open(os.path.join(self.root, "board-log.jsonl"), "w", encoding="utf-8"):
            pass
        path = os.path.join(self.root, "board.json")
        with open(path, encoding="utf-8") as f:
            board = json.load(f)
        board["status"] = {}
        board["sub_issues"] = {}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(board, f)

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
        self.assertEqual(out.get("next"), "Backlog")
        self.assertIn("**REQ-KTL-001: (new) → Backlog**", out["comment"])
        self.assertIn(MARKER_SYSTEM, out["comment"])
        self.assertIn("[system]", out["comment"])
        log = read_log(self.root)
        self.assertGreaterEqual(len(log), 1)
        self.assertTrue(all((r.get("kind") or KIND_SYSTEM) == KIND_SYSTEM for r in log))
        with open(os.path.join(self.root, "board.json"), encoding="utf-8") as f:
            board = json.load(f)
        self.assertEqual(len(board["sub_issues"]["REQ-KTL-001"]), 9)
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
        self.assertGreaterEqual(len(trail["rendered"]), 2)
        note = cmd_note(self.root, "s1", "Minted USR and REQ for boil.", "req-guardian",
                        req_id="REQ-KTL-001", stage="Requirements", gh=False)
        self.assertIn(MARKER_NOTE, note["body"])
        self.assertIn("— Req Guardian", note["body"])
        sys_only = cmd_trail(self.root, "REQ-KTL-001", kind=KIND_SYSTEM)
        notes_only = cmd_trail(self.root, "REQ-KTL-001", kind=KIND_NOTE)
        self.assertTrue(all(MARKER_SYSTEM in b for b in sys_only["rendered"]))
        self.assertTrue(all(MARKER_NOTE in b for b in notes_only["rendered"]))
        self.assertEqual(len(notes_only["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
