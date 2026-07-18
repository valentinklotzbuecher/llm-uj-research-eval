import importlib.util
import json
import pathlib
import re
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_concordance_codex.py"
SPEC = importlib.util.spec_from_file_location("run_concordance_codex", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ConcordanceCodexPrivacyTests(unittest.TestCase):
    def test_sol_prompt_anonymizes_human_issue_attribution(self):
        cases = [
            {
                "paper_id": "paper",
                "human_issues": [
                    {
                        "id": "paper::H001",
                        "severity": "necessary",
                        "text": (
                            'Reviewer 2 [Exampleperson]: "The comparison is underpowered."\n'
                            "Testperson\n"
                            "Sampleperson notes that the robustness check is missing.\n"
                            "Alex Example is not an expert on this design."
                        ),
                    }
                ],
                "llm_issues": [
                    {
                        "id": "paper::L001",
                        "text": "The comparison may lack statistical power.",
                    }
                ],
            }
        ]
        candidates = [
            {
                "paper_id": "paper",
                "human_issue_id": "paper::H001",
                "llm_issue_ids": ["paper::L001"],
                "reason": "Borderline overlap score",
                "terra_judgment": None,
            }
        ]

        prompt = MODULE.build_sol_prompt(candidates, cases)

        self.assertNotIn("Reviewer 2", prompt)
        self.assertNotIn("Exampleperson", prompt)
        self.assertNotIn("Testperson", prompt)
        self.assertNotIn("Sampleperson", prompt)
        self.assertNotIn("Alex Example", prompt)
        self.assertIn("human evaluator", prompt)
        self.assertIn("The comparison is underpowered.", prompt)

    def test_current_source_has_no_known_attribution_formats_after_scrubbing(self):
        source = SCRIPT.parents[1] / "tools" / "issue_annotation_ui" / "data.json"
        data = json.loads(source.read_text())
        residual_attribution = re.compile(
            r"\b(?:reviewer|evaluator)\s*\d+\b|\bE\d+\b|\bDR\b|"
            r"^\s*[A-Z][A-Za-z'’.-]{2,30}\s*$|"
            r"\[[A-Z][A-Za-z'’.-]{2,30}\]|"
            r"\b[A-Z][A-Za-z'’.-]{2,30}\s+(?=(?:notes?|argues?|observes?|"
            r"requests?|requested|recommended|suggests?|emphasizes?|critiqued|"
            r"wrote|writes?|said|says?)\b)",
            re.MULTILINE,
        )

        for paper in data["papers"]:
            for issue in paper.get("human_issue_suggestions", []):
                scrubbed = MODULE.anonymize_human_issue(issue["text"])
                self.assertIsNone(
                    residual_attribution.search(scrubbed),
                    msg=f"Residual attribution in {paper['paper_id']}: {scrubbed}",
                )


class ConcordanceCodexCacheTests(unittest.TestCase):
    def test_completed_call_artifacts_are_marked_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = pathlib.Path(directory)
            calls_dir = run_dir / "calls"
            calls_dir.mkdir()
            (calls_dir / "cached.final.json").write_text('{"papers": []}')
            (calls_dir / "cached.meta.json").write_text(
                json.dumps(
                    {
                        "call_name": "cached",
                        "usage": {
                            "input_tokens": 12,
                            "cached_input_tokens": 3,
                            "output_tokens": 4,
                            "reasoning_output_tokens": 1,
                        },
                    }
                )
            )

            result, meta = MODULE.run_codex_call(
                call_name="cached",
                prompt="not sent",
                schema={"type": "object"},
                model="unused",
                effort="high",
                run_dir=run_dir,
                binary=pathlib.Path("/binary/is/not/invoked"),
                timeout=1,
                force=False,
            )

            self.assertEqual(result, {"papers": []})
            self.assertTrue(meta["artifact_reused_this_execution"])
            self.assertEqual(meta["usage"]["input_tokens"], 12)


if __name__ == "__main__":
    unittest.main()
