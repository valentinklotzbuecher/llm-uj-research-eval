import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import run_issue_match_judge as j  # noqa: E402


class BlindingTests(unittest.TestCase):
    def setUp(self):
        self.papers = {
            "P1": {"human": {"H1": "h one", "H2": "h two"}, "model": {"L1": "m one", "L2": "m two", "L3": "m three"}},
            "P2": {"human": {"H1": "x"}, "model": {"L1": "y"}},
        }

    @staticmethod
    def case(case_id):
        return {"case_id": case_id, "human_paper": "P1", "model_paper": "P1"}

    def test_text_hides_source(self):
        b = j.blind(self.case("P1__r1"), self.papers)
        low = b["user_text"].lower()
        for word in ("human", "llm", "model", "gpt", "evaluator"):
            self.assertNotIn(word, low)
        self.assertEqual(len(b["key"]), 5)

    def test_deterministic_and_varies_by_case(self):
        b1 = j.blind(self.case("P1__r1"), self.papers)
        self.assertEqual(b1, j.blind(self.case("P1__r1"), self.papers))
        sides = {j.blind(self.case(f"P1__r{i}"), self.papers)["human_is_a"] for i in range(20)}
        self.assertEqual(sides, {True, False})

    def test_unblind_and_metrics(self):
        key = {"A1": "H1", "A2": "H2", "B1": "L1", "B2": "L2", "B3": "L3"}
        parsed = {"pairs": [
            {"a_id": "A1", "b_id": "B2", "category": "same_concern", "broader_side": "neither", "confidence": 90, "reason": ""},
            {"a_id": "A2", "b_id": "B3", "category": "same_concern_different_scope", "broader_side": "B", "confidence": 60, "reason": ""},
            {"a_id": "A2", "b_id": "B1", "category": "same_topic_only", "broader_side": "neither", "confidence": 60, "reason": ""},
            {"a_id": "A1", "b_id": "A2", "category": "same_concern", "broader_side": "neither", "confidence": 60, "reason": ""},
        ]}
        pairs, errors = j.unblind_pairs(parsed, key)
        self.assertEqual(len(pairs), 3)
        self.assertEqual(len(errors), 1)
        m = j.metrics(pairs, 2, 3)
        self.assertEqual(m["strict"]["human_covered"], 1)
        self.assertEqual(m["standard"]["human_covered"], 2)
        self.assertEqual(m["standard"]["model_matched"], 2)
        self.assertEqual(m["loose"]["coverage"], 100.0)
        self.assertEqual(m["human_covered_only_by_broader_model_item"], 1)

    def test_leak_scan_flags_attribution(self):
        hits = j.leak_scan({"P": {"human": {"H1": "The evaluator notes the sample is small."},
                                  "model": {"L1": "The sample is small, limiting power."}}})
        self.assertEqual([h["id"] for h in hits], ["H1"])

    def test_cases_include_controls(self):
        papers = {f"P{i:02d}": {"human": {"H1": "h"}, "model": {"L1": "m"}} for i in range(12)}
        papers["Benabou_et_al._2023"] = {"human": {"H1": "h"}, "model": {"L1": "m"}}
        cases = j.build_cases(papers, 2)
        kinds = [c["kind"] for c in cases]
        self.assertEqual(kinds.count("real"), 24)
        self.assertEqual(kinds.count("documented_mismatch"), 1)
        controls = [c for c in cases if c["kind"] == "cross_paper_control"]
        self.assertEqual(len(controls), 6)
        self.assertTrue(all(c["human_paper"] != c["model_paper"] for c in controls))


if __name__ == "__main__":
    unittest.main()
