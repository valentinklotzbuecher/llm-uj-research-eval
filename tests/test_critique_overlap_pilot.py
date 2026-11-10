"""Offline tests for the critique-overlap pilot helpers and the eligibility manifest parser."""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_critique_eligibility_manifest as man  # noqa: E402
import critique_overlap_pilot as pilot  # noqa: E402


FRONT = """---
article:
  doi: 10.0/x
author:
- Evaluator 1
date:
  day: 03
  month: 06
  year: 2025
title: Evaluation 2 of "Global potential for natural regeneration in
  deforested tropical regions"
uri: "https://example.org/pub/e2x"
---

# Abstract

Body text here.
"""


class ManifestParsing(unittest.TestCase):
    def test_front_matter_title_and_date(self):
        fm, body = man.split_front_matter(FRONT)
        title = man.front_matter_title(fm)
        self.assertEqual(
            title, 'Evaluation 2 of "Global potential for natural regeneration in deforested tropical regions"')
        self.assertEqual(man.front_matter_date(fm), "2025-06-03")
        self.assertTrue(body.strip().startswith("# Abstract"))

    def test_quoted_title_matches_exactly_after_normalising(self):
        fm, _ = man.split_front_matter(FRONT)
        quoted = man.quoted_titles(man.front_matter_title(fm))
        self.assertEqual(
            [man.norm(q) for q in quoted],
            [man.norm("Global Potential for Natural Regeneration in Deforested Tropical Regions")])

    def test_kind_and_index(self):
        self.assertEqual(man.classify_kind('Evaluation 2 of "X paper title"', "e2x"), "evaluation")
        self.assertEqual(man.evaluator_index('Evaluation 2 of "X paper title"', "e2x"), 2)
        self.assertEqual(man.classify_kind('Evaluation Summary and Metrics: "X"', "evalsumx"), "summary")
        self.assertEqual(man.classify_kind("Authors' response to evaluations", "authorsresponsex"), "author_response")

    def test_norm_strips_accents_and_punctuation(self):
        self.assertEqual(man.norm("Bénabou — et al., 2023"), "benabouetal2023")


class Selection(unittest.TestCase):
    def test_rule_filters_and_orders_by_hash(self):
        def paper(name, eligible=True, n=2, predates=True):
            return {"paper": name, "eligible": eligible, "n_substantive_individual_evaluations": n,
                    "pdf_predates_first_evaluation": predates}

        manifest = {"papers": [paper("A"), paper("B", eligible=False), paper("C", n=1),
                               paper("D", predates=None), paper("E"), paper("F")]}
        chosen = [p["paper"] for p in pilot.select_papers(manifest, 2)]
        pool = sorted(["A", "E", "F"], key=pilot.sha256_text)
        self.assertEqual(chosen, pool[:2])


class QuoteCheck(unittest.TestCase):
    def test_quote_survives_markdown_and_whitespace(self):
        src = "The authors\\' *main* estimate relies on a\nsingle “pre-specified” control variable, which is fragile."
        self.assertTrue(pilot.quote_in_source(
            "main estimate relies on a single \"pre-specified\" control variable", src))

    def test_invented_or_tiny_quote_fails(self):
        src = "The main estimate relies on a single control variable."
        self.assertFalse(pilot.quote_in_source("the estimate depends on two instruments and a placebo", src))
        self.assertFalse(pilot.quote_in_source("single control", src))


class Blinding(unittest.TestCase):
    def setUp(self):
        self.s1 = [{"id": f"P::E1::H{i:02d}", "text": f"human {i}"} for i in range(1, 5)]
        self.s2 = [{"id": f"P::M{i:02d}", "text": f"model {i}"} for i in range(1, 4)]

    def test_deterministic_and_complete(self):
        a = pilot.blind_lists("real::P", self.s1, self.s2)
        b = pilot.blind_lists("real::P", self.s1, self.s2)
        self.assertEqual(a, b)
        self.assertEqual(sorted(a["id_map"].values()), sorted(i["id"] for i in self.s1 + self.s2))
        prompt = pilot.judge_user_prompt(a)
        self.assertNotIn("::H", prompt)
        self.assertNotIn("::M", prompt)

    def test_unblind_round_trip_regardless_of_swap(self):
        for pid in ("real::P", "real::Q", "real::R", "real::S", "real::T", "real::U"):
            bl = pilot.blind_lists(pid, self.s1, self.s2)
            inv = {v: k for k, v in bl["id_map"].items()}
            h, m = self.s1[2]["id"], self.s2[0]["id"]
            ka, kb = sorted([inv[h], inv[m]])  # the A-list id sorts first
            raw = {"matches": [{"a_id": ka, "b_id": kb, "label": "partial", "score": 55, "reason": "r"},
                               {"a_id": "A99", "b_id": "B1", "label": "exact", "score": 90, "reason": "bad id"}]}
            matches, invalid = pilot.unblind_matches(raw, bl)
            self.assertEqual(invalid, 1)
            self.assertEqual((matches[0]["side1_id"], matches[0]["side2_id"]), (h, m))


class Metrics(unittest.TestCase):
    MATCHES = [
        {"side1_id": "h1", "side2_id": "m1", "label": "exact", "score": 90},
        {"side1_id": "h1", "side2_id": "m2", "label": "related_but_distinct", "score": 35},
        {"side1_id": "h2", "side2_id": "m2", "label": "related_but_distinct", "score": 31},
        {"side1_id": "h3", "side2_id": "m3", "label": "partial", "score": 44},
    ]

    def test_coverage_counts_unique_items_not_matches(self):
        self.assertEqual(pilot.covered_ids(self.MATCHES, "side1", "score>=30"), {"h1", "h2", "h3"})
        self.assertEqual(pilot.covered_ids(self.MATCHES, "side1", "score>=45"), {"h1"})
        self.assertEqual(pilot.covered_ids(self.MATCHES, "side1", "label"), {"h1", "h3"})
        self.assertEqual(pilot.covered_ids(self.MATCHES, "side2", "score>=30"), {"m1", "m2", "m3"})
        self.assertEqual(pilot.covered_ids(self.MATCHES, "side2", "label"), {"m1", "m3"})

    def test_rate_and_kappa(self):
        self.assertEqual(pilot.rate(3, 4), 75.0)
        self.assertIsNone(pilot.rate(0, 0))
        self.assertEqual(pilot.cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]), 1.0)
        self.assertEqual(pilot.cohen_kappa([1, 0, 1, 0], [1, 1, 0, 0]), 0.0)
        self.assertIsNone(pilot.cohen_kappa([1, 1], [1, 1]))


if __name__ == "__main__":
    unittest.main()
