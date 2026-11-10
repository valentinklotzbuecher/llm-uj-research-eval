import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import build_human_issue_reference as b  # noqa: E402
import run_human_baseline_judge as h  # noqa: E402

DOC = """---
author:
- Pat Q. Example
- Evaluator 2
title: Evaluation 1 of "A Paper"
---

# Abstract

Pat Example notes the main estimate is biased. Example agrees.

# Summary Measures

+----+----+
| a  | b  |
+----+----+

# Written report

The estimate in Table 2 omits controls.

# Evaluator details

Pat Example, University of Somewhere.
"""


class CleaningTests(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(b.classify('Evaluation 2 of "X"'), "E2")
        self.assertEqual(b.classify('Evaluation 2: "X"'), "E2")
        self.assertEqual(b.classify('Evaluation 2 (anon.) of "X"'), "E2")
        self.assertEqual(b.classify('Evaluation of "X"'), "E1")
        self.assertEqual(b.classify('"Evaluation Summary and Metrics: \\"X\\""'), "EM")
        self.assertEqual(b.classify("Authors' response to Unjournal evaluations of X"), "AR")
        self.assertEqual(b.classify('Compiled evaluations: "X"'), "compiled")

    def test_authors_and_redaction(self):
        self.assertEqual(b.doc_authors(DOC), ["Pat Q. Example"])
        mine = [{"role": "E1", "authors": b.doc_authors(DOC), "title": b.doc_title(DOC)}]
        text = b.clean_text(DOC, b.redaction_patterns(b.reviewer_names(mine)))
        self.assertNotIn("Example", text)
        self.assertNotIn("Pat", text)
        self.assertNotIn("Somewhere", text)  # evaluator details dropped
        self.assertNotIn("+----", text)       # ratings tables dropped
        self.assertIn("Table 2 omits controls", text)
        self.assertIn("[name]", text)

    def test_title_names_are_redacted(self):
        mine = [{"role": "E3", "authors": [], "title": 'Evaluation 3 of "A Paper" by Sam Placeholder'}]
        self.assertEqual(b.reviewer_names(mine), ["Sam Placeholder"])
        mine = [{"role": "E2", "authors": [], "title": 'Evaluation 2 of "A Paper" (anonymous reviewer)'}]
        self.assertEqual(b.reviewer_names(mine), [])

    def test_stub_exports(self):
        self.assertTrue(b.is_full_export(DOC))
        self.assertFalse(b.is_full_export("# Evaluation 1 of X\n\nSource: https://example.org\n"))

    def test_anchor(self):
        self.assertTrue(b.anchor_found("the estimate in table 2", "x The estimate in Table\n2 omits"))
        self.assertFalse(b.anchor_found("not there", "something else"))
        self.assertFalse(b.anchor_found("", "anything"))


class BaselineTests(unittest.TestCase):
    def test_shape_for_v2(self):
        lists = {"P::E1": {"M1": "a", "M2": "b"}, "P::E2": {"M1": "c"}}
        papers, case = h.as_v2_papers({"case_id": "x", "a": "P::E1", "b": "P::E2"}, lists)
        self.assertEqual(set(papers["A"]["human"]), {"H1", "H2"})
        self.assertEqual(set(papers["B"]["model"]), {"L1"})
        bl = h.v2.blind(case, papers)
        self.assertEqual((bl["n_human"], bl["n_model"]), (2, 1))

    def test_minor_exclusion(self):
        pairs = [{"human": "H1", "model": "L1", "category": "same_concern"},
                 {"human": "H2", "model": "L1", "category": "same_concern"}]
        m = h.metrics_excluding_minor(pairs, {"M1", "M2"}, {"M1", "M2"}, {"M2"}, set())
        self.assertEqual((m["n_human"], m["n_model"]), (1, 2))
        self.assertEqual(m["standard"]["human_covered"], 1)
        self.assertEqual(m["standard"]["model_matched"], 1)

    def test_cases_cover_all_evaluator_pairs(self):
        ref = {p: {"E1": [{}], "E2": [{}]} for p in h.CORE[:8]}
        ref[h.CORE[0]]["E3"] = [{}]
        cases = h.build_cases(ref, set(), replicates=2, model_reps=1)
        hh = [c for c in cases if c["kind"] == "hh"]
        self.assertEqual(len(hh), 2 * (7 + 3))
        ctl = [c for c in cases if c["kind"] == "control"]
        self.assertEqual(len(ctl), 6)
        self.assertTrue(all(c["a"].split("::")[0] != c["b"].split("::")[0] for c in ctl))


if __name__ == "__main__":
    unittest.main()
