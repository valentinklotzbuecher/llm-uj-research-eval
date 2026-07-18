import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "screen_paper_response_matches.py"
SPEC = importlib.util.spec_from_file_location("screen_paper_response_matches", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class PaperResponseScreenTests(unittest.TestCase):
    def test_preexisting_concepts_are_not_counted_as_new_matches(self):
        atom = {
            "category": "Sensitivity analysis",
            "description": "Report a sensitivity analysis using alternative discount rates",
            "quote": "The authors should report a sensitivity analysis using alternative discount rates",
        }
        card = {
            "before_excerpt": "We report sensitivity analysis with alternative discount rates.",
            "after_excerpt": "We report sensitivity analysis with alternative discount rates and add one table.",
            "section": "methods",
        }
        score = MODULE.score_atom_card(atom, card)
        self.assertFalse(score.new_terms)
        self.assertGreaterEqual(len(score.preexisting_terms), 3)
        self.assertEqual(score.score, 0.0)

    def test_specific_new_language_scores_above_generic_overlap(self):
        atom = {
            "category": "Risk of bias",
            "description": "Add a PRISMA flow diagram and report inter-rater extraction checks",
            "quote": "The authors should add a PRISMA flow diagram and report inter-rater extraction checks",
        }
        specific = {
            "before_excerpt": "We conducted a systematic review.",
            "after_excerpt": "We added a PRISMA flow diagram and inter-rater extraction checks.",
            "section": "systematic review methods",
        }
        generic = {
            "before_excerpt": "We conducted a systematic review.",
            "after_excerpt": "We added a new discussion of the findings.",
            "section": "discussion",
        }
        self.assertGreater(
            MODULE.score_atom_card(atom, specific).score,
            MODULE.score_atom_card(atom, generic).score,
        )

    def test_preexisting_concept_elsewhere_in_document_is_suppressed(self):
        atom = {
            "category": "Alternative vegetation measure",
            "description": "Test alternative upwind cone definitions for vegetation concentration",
            "quote": "The authors could test alternative upwind cone definitions",
        }
        card = {
            "before_excerpt": "The baseline uses average greening.",
            "after_excerpt": "We test alternative upwind cone definitions for vegetation concentration.",
            "section": "robustness",
        }
        whole_before = (
            "Appendix results already test alternative upwind cone definitions "
            "for vegetation concentration."
        )
        without_global = MODULE.score_atom_card(atom, card)
        with_global = MODULE.score_atom_card(atom, card, whole_before)
        self.assertGreater(without_global.score, with_global.score)
        self.assertGreaterEqual(
            with_global.whole_before_max_coverage,
            with_global.coverage,
        )
        self.assertFalse(with_global.new_bigrams)

    def test_invalid_timeline_is_hard_excluded(self):
        item = {
            "comparison_path": "data/example.json",
            "evaluation_files": ["data/eval.md"],
            "review_reasons": ["after_version_predates_evaluation"],
        }
        eligible, reasons = MODULE.queue_eligibility(
            item, "manually_rejected_not_post_evaluation"
        )
        self.assertFalse(eligible)
        self.assertIn("after_version_predates_evaluation", reasons)

    def test_placebo_percentile_uses_midrank_for_ties(self):
        self.assertEqual(MODULE.percentile_against_placebos(0.4, [0.1, 0.4, 0.8]), 0.5)


if __name__ == "__main__":
    unittest.main()
