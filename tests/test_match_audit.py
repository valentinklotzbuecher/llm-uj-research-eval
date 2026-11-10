"""Offline tests for scripts/match_audit.py (export and scoring of the human match audit)."""

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import match_audit as ma  # noqa: E402


def toy_data():
    return {"datasets": [{
        "id": "ds", "judges": [{"id": "j1"}, {"id": "j2"}],
        "papers": [{
            "paper_id": "P",
            "human_issues": [{"id": "P::H01"}, {"id": "P::H02"}],
            "model_issues": [{"id": "P::M01"}, {"id": "P::M02"}],
            "judge_matches": {
                "j1": [{"human_id": "P::H01", "model_id": "P::M01", "score": 80},
                       {"human_id": "P::H02", "model_id": "P::M02", "score": 35}],
                "j2": [{"human_id": "P::H01", "model_id": "P::M01", "score": 90},
                       {"human_id": "P::H02", "model_id": "P::M02", "score": 20}],
            },
        }],
    }]}


def review(name, verdicts):
    return {"tool": "issue-match-audit", "reviewer": name,
            "verdicts": [{"dataset": "ds", "human_id": h, "model_id": m, "verdict": v} for h, m, v in verdicts]}


class Scoring(unittest.TestCase):
    def test_precision_recall_against_reviewer(self):
        r = review("a", [("P::H01", "P::M01", "same"), ("P::H02", "P::M02", "different"),
                         ("P::H02", "P::M01", "partial"), ("P::H01", "P::M02", "unsure")])
        out = ma.score_reviews(toy_data(), [r], threshold=30)["datasets"]["ds"]["reviewers"]["a"]
        # j1 proposes H01-M01 and H02-M02; the reviewer confirms one of the two.
        self.assertEqual(out["j1"]["judge_proposals_reviewed"], 2)
        self.assertEqual(out["j1"]["precision"], 0.5)
        # Reviewer matches: H01-M01 and H02-M01; j1 proposed only the first. Unsure is ignored.
        self.assertEqual(out["j1"]["reviewer_matches"], 2)
        self.assertEqual(out["j1"]["recall"], 0.5)
        self.assertEqual(out["j1"]["pairs_reviewed"], 3)
        # j2 at threshold 30 proposes only H01-M01, which the reviewer confirmed.
        self.assertEqual(out["j2"]["precision"], 1.0)

    def test_threshold_changes_proposals(self):
        r = review("a", [("P::H02", "P::M02", "same")])
        hi = ma.score_reviews(toy_data(), [r], threshold=45)["datasets"]["ds"]["reviewers"]["a"]["j1"]
        self.assertEqual(hi["judge_proposals_reviewed"], 0)
        self.assertEqual(hi["recall"], 0.0)

    def test_reviewer_agreement_on_shared_pairs(self):
        a = review("a", [("P::H01", "P::M01", "same"), ("P::H02", "P::M02", "different")])
        b = review("b", [("P::H01", "P::M01", "partial"), ("P::H02", "P::M02", "same"), ("P::H01", "P::M02", "same")])
        ag = ma.score_reviews(toy_data(), [a, b])["datasets"]["ds"]["reviewer_agreement"][0]
        self.assertEqual(ag["shared_pairs"], 2)
        self.assertEqual(ag["percent_agreement"], 50.0)

    def test_non_audit_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x.json"
            p.write_text(json.dumps({"annotator": "z", "rows": []}))
            self.assertEqual(ma.load_reviews([p]), [])


class Export(unittest.TestCase):
    def test_rewrite_is_a_noop_when_content_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "audit.json"
            ui = pathlib.Path(d) / "ui"
            ui.mkdir()
            data = {"generated_at": "t1", "source_commit": "a", **toy_data()}
            self.assertEqual(len(ma.write_export(data, out, ui)), 2)
            again = {**data, "generated_at": "t2", "source_commit": "b"}
            self.assertEqual(ma.write_export(again, out, ui), [])
            self.assertEqual(json.loads(out.read_text())["generated_at"], "t1")
            changed = {**again, "datasets": []}
            self.assertEqual(len(ma.write_export(changed, out, ui)), 2)
            self.assertTrue((ui / "audit_data.js").read_text().startswith("// Generated"))

    def test_real_export_has_no_named_attribution_and_ids_resolve(self):
        data = ma.build_export()
        for ds in data["datasets"]:
            for p in ds["papers"]:
                hids = {h["id"] for h in p["human_issues"]}
                mids = {m["id"] for m in p["model_issues"]}
                for ms in p["judge_matches"].values():
                    for m in ms:
                        self.assertIn(m["human_id"], hids)
                        self.assertIn(m["model_id"], mids)
        focal = [d for d in data["datasets"] if d["id"] == "gpt52_focal_jan2026"]
        if focal:
            n_h = sum(len(p["human_issues"]) for p in focal[0]["papers"])
            n_m = sum(len(p["model_issues"]) for p in focal[0]["papers"])
            self.assertEqual((len(focal[0]["papers"]), n_h, n_m), (12, 63, 142))


if __name__ == "__main__":
    unittest.main()
