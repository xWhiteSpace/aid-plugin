#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vmodel_board import (COLUMNS, desired_column, next_column, plan_rows,  # noqa: E402
                          req_facts, sign_comment)
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


class Comment(unittest.TestCase):
    def test_sign(self):
        self.assertIn("— A.I.D", sign_comment("hello", "AID"))
        self.assertIn("— Board Keeper", sign_comment("moved", "board-keeper"))


if __name__ == "__main__":
    unittest.main()
