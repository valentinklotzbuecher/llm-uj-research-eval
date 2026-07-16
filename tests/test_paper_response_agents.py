import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_paper_response_agents.py"
SPEC = importlib.util.spec_from_file_location("run_paper_response_agents", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class PaperResponseAgentValidationTests(unittest.TestCase):
    def test_blank_or_unknown_link_ids_are_rejected(self):
        result = {
            "candidate_links": [
                {"atom_id": "atom-001", "card_id": ""},
                {"atom_id": "atom-999", "card_id": "chg-0001"},
            ]
        }
        errors = MODULE.validate_links(result, {"atom-001"}, {"chg-0001"})
        self.assertIn("unknown card in link: ", errors)
        self.assertIn("unknown atom in link: atom-999", errors)

    def test_change_card_ids_are_checked(self):
        result = {"classifications": [{"card_id": "chg-0002"}]}
        errors = MODULE.validate_change_classifications(result, {"chg-0001"})
        self.assertEqual(errors, ["unknown change card: chg-0002"])


if __name__ == "__main__":
    unittest.main()
