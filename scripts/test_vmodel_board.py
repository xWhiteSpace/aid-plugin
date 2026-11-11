#!/usr/bin/env python3
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_board import (  # noqa: E402
    COLUMNS, PHASES, cmd_event, cmd_trail, desired_column, format_block,
    next_column, plan_rows, proof_ok, read_log, req_facts, sign_comment,
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
        self.assertEqual([r["phase"] for r in rows], PHASES)
        changed = [r["to"] for r in rows if r.get("from") != r.get("to")]
        self.assertEqual(changed, COLUMNS)
        self.assertEqual(rows[-1]["to"], "Done")
        self.assertTrue(all(r.get("proof") for r in rows))


class Comment(unittest.TestCase):
    def test_sign(self):
        self.assertIn("— A.I.D", sign_comment("hello", "AID"))
        self.assertIn("— Board Keeper", sign_comment("moved", "board-keeper"))

    def test_block_labels(self):
        body = format_block(
            "REQ-KTL-001", "Ready", "In progress", "Code",
            "adept ; Last Boss slice", "UNT-KTL-001; src/start_guard.py",
            "test-master unit tests", "abc123", "first entry")
        self.assertIn("**REQ-KTL-001: Ready → In progress**", body)
        for label in ("Phase done:", "Who:", "Changed:", "Next:", "Proof:", "Back:"):
            self.assertIn("**%s**" % label, body)
        signed = sign_comment(body, "board-keeper")
        self.assertTrue(signed.endswith("— Board Keeper"))
        aid = sign_comment(body, "AID")
        self.assertTrue(aid.endswith("— A.I.D"))

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
        self.assertIn("**Proof:** proposal USR-KTL-001", out["comment"])
        self.assertIn("first entry", out["comment"])
        log = read_log(self.root)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["to"], "Backlog")
        phase = cmd_event(self.root, "phase", "REQ-KTL-001", payload={
            "phase": "Functions",
            "who": "functional-specs ; SSOT Gate published",
            "changed": "FNC-KTL-001",
            "next": "system-designer",
            "proof": "baseline 2026-10-16-g1",
        })
        self.assertFalse(phase.get("moved"))
        self.assertIn("no column change", phase["comment"])
        trail = cmd_trail(self.root, "REQ-KTL-001")
        self.assertEqual(len(trail["rendered"]), 2)
        self.assertIn("first entry", trail["rendered"][0])
        self.assertIn(log[0]["time"], trail["rendered"][1])


if __name__ == "__main__":
    unittest.main()
