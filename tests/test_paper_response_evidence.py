import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "paper_response_evidence.py"
SPEC = importlib.util.spec_from_file_location("paper_response_evidence", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class PaperResponseEvidenceTests(unittest.TestCase):
    def test_normalize_doi_handles_legacy_typo(self):
        self.assertEqual(
            MODULE.normalize_doi("doig.org/10.3386/w31899"),
            "10.3386/w31899",
        )
        self.assertEqual(
            MODULE.stable_paper_id(
                "The Effect of Public Science on Corporate R&D",
                "doig.org/10.3386/w31899",
            ),
            "the-effect-of-public-science-on-corpor-ef23c268d6",
        )

    def test_stable_paper_id_prefers_normalized_doi(self):
        first = MODULE.stable_paper_id("A Paper Title", "https://doi.org/10.1234/ABC")
        second = MODULE.stable_paper_id("A Paper Title", "10.1234/abc")
        self.assertEqual(first, second)

    def test_identity_score_requires_title_and_author_evidence(self):
        result = MODULE.identity_score(
            "Cash Transfers for Child Development",
            "Jeffrey Weaver,Sandip Sukhtankar",
            "Cash Transfers for Child Development — Jeffrey Weaver and Sandip Sukhtankar",
        )
        self.assertEqual(result["status"], "verified")
        mismatch = MODULE.identity_score(
            "Cash Transfers for Child Development",
            "Jeffrey Weaver,Sandip Sukhtankar",
            "An unrelated article about marine ecology by another research team.",
        )
        self.assertEqual(mismatch["status"], "mismatch")

    def test_identity_score_accepts_only_explicit_title_aliases(self):
        canonical = "Cash Transfers for Child Development: Experimental Evidence from India"
        renamed = "Early-Life Cash and Child Development in India"
        text = f"{renamed} — Jeffrey Weaver and Sandip Sukhtankar"
        without_alias = MODULE.identity_score(
            canonical, "Jeffrey Weaver,Sandip Sukhtankar", text
        )
        with_alias = MODULE.identity_score(
            canonical,
            "Jeffrey Weaver,Sandip Sukhtankar",
            text,
            [renamed],
        )
        self.assertNotEqual(without_alias["status"], "verified")
        self.assertEqual(with_alias["status"], "verified")
        self.assertEqual(with_alias["matched_title"], renamed)
        self.assertTrue(with_alias["matched_title_is_alias"])
        self.assertLess(
            with_alias["canonical_title_token_coverage"],
            with_alias["title_token_coverage"],
        )

    def test_change_cards_anchor_numeric_result_change(self):
        before = [{
            "page": 5,
            "text": "Results\nThe treatment increased attendance by 4 percent in the full sample. "
                    "This estimate was statistically significant and stable across specifications.",
        }]
        after = [{
            "page": 6,
            "text": "Results\nThe treatment increased attendance by 9 percent in the full sample. "
                    "This estimate was statistically significant and stable across specifications. "
                    "We also report a new heterogeneity analysis by baseline income.",
        }]
        cards = MODULE.change_cards(before, after)
        material = [card for card in cards if card["material"]]
        self.assertTrue(material)
        self.assertTrue(any(card["numeric_change"] for card in material))
        self.assertIn(6, material[0]["after_pages"])

    def test_reference_only_change_is_not_material(self):
        before = [{"page": 20, "text": "References\nSmith, A. 2020. A study of policy outcomes and methods."}]
        after = [{"page": 21, "text": "References\nSmith, A. 2020. A study of policy outcomes and methods.\nJones, B. 2024. New citation."}]
        cards = MODULE.change_cards(before, after)
        self.assertFalse(any(card["material"] for card in cards))

    def test_html_pdf_metadata_resolution(self):
        html = '<meta name="citation_pdf_url" content="/downloads/paper.pdf">'
        self.assertEqual(
            MODULE.pdf_link_from_html(html, "https://example.org/article/1"),
            "https://example.org/downloads/paper.pdf",
        )

    def test_manual_timeline_validation_is_bound_to_exact_snapshots(self):
        validation = {"version_timeline": {
            "status": "verified_post_evaluation",
            "before_sha256": "before-hash",
            "after_sha256": "after-hash",
        }}
        self.assertEqual(
            MODULE.manual_timeline_status(
                validation, {"sha256": "before-hash"}, {"sha256": "after-hash"}
            ),
            "manually_verified_post_evaluation",
        )
        self.assertIsNone(
            MODULE.manual_timeline_status(
                validation, {"sha256": "before-hash"}, {"sha256": "new-after-hash"}
            )
        )

    def test_manual_timeline_rejection_is_a_distinct_status(self):
        validation = {"version_timeline": {
            "status": "rejected_not_post_evaluation",
            "before_sha256": "before-hash",
            "after_sha256": "after-hash",
        }}
        self.assertEqual(
            MODULE.manual_timeline_status(
                validation, {"sha256": "before-hash"}, {"sha256": "after-hash"}
            ),
            "manually_rejected_not_post_evaluation",
        )

    def test_manual_no_change_validation_requires_exact_hash_and_evidence(self):
        validation = {"no_change_observation": {
            "status": "verified_no_observed_document_change",
            "sha256": "same-hash",
            "evaluation_date": "2025-01-01",
            "before_version_date": "2024-12",
            "current_checked_at": "2026-07-17",
            "current_source_url": "https://example.org/paper.pdf",
            "evidence": "The evaluated draft date and current public source were checked.",
        }}
        self.assertEqual(
            MODULE.manual_no_change_status(
                validation, {"sha256": "same-hash"}, {"sha256": "same-hash"}
            ),
            "manually_verified_no_observed_document_change",
        )
        self.assertIsNone(
            MODULE.manual_no_change_status(
                validation, {"sha256": "same-hash"}, {"sha256": "different-hash"}
            )
        )

    def test_manual_no_change_validation_rejects_incomplete_evidence(self):
        validation = {"no_change_observation": {
            "status": "verified_no_observed_document_change",
            "sha256": "same-hash",
        }}
        self.assertIsNone(
            MODULE.manual_no_change_status(
                validation, {"sha256": "same-hash"}, {"sha256": "same-hash"}
            )
        )

    def test_manual_public_source_override_requires_review_metadata(self):
        validation = {"current_public_source": {
            "status": "verified_override",
            "url": "https://example.org/revised.pdf",
            "evidence": "The public author response identifies this revised endpoint.",
            "checked_at": "2026-07-17",
        }}
        self.assertEqual(
            MODULE.manual_public_source_url(validation),
            "https://example.org/revised.pdf",
        )
        validation["current_public_source"]["url"] = "http://example.org/revised.pdf"
        self.assertIsNone(MODULE.manual_public_source_url(validation))

    def test_manual_endpoint_status_is_bound_to_stale_public_hash(self):
        validation = {"endpoint_assessment": {
            "status": "known_revised_version_unavailable",
            "stale_public_sha256": "stale-hash",
            "evidence": "The public author response says the paper was revised.",
            "checked_at": "2026-07-17",
        }}
        self.assertEqual(
            MODULE.manual_endpoint_status(validation, {"sha256": "stale-hash"}),
            "known_revised_version_unavailable",
        )
        self.assertIsNone(
            MODULE.manual_endpoint_status(validation, {"sha256": "new-hash"})
        )

    def test_public_document_mapping_recognizes_authors_response(self):
        mapping = MODULE.public_document_mapping(
            "https://unjournal.pubpub.org/pub/evalsumpublicscience/release/1"
        )
        self.assertIn(
            "data/unjournal_evaluations/authorsresponsepublicscience.md",
            mapping["public_response_files"],
        )


if __name__ == "__main__":
    unittest.main()
