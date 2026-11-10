import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import critique_overlap_scale as s  # noqa: E402


def row(kind, paper, n1, n2, c1, c2):
    r = {"kind": kind, "paper": paper, "n1": n1, "n2": n2}
    for rule in s.pilot.RULES:
        r[f"c1[{rule}]"], r[f"c2[{rule}]"] = c1, c2
    return r


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for i in range(10):
            p = f"P{i}"
            self.rows += [row("real", p, 10, 5, 5, 4), row("placebo", p, 10, 5, 0, 0),
                          row("human_human", p, 4, 6, 1, 2)]

    def test_pooled(self):
        real = [r for r in self.rows if r["kind"] == "real"]
        hh = [r for r in self.rows if r["kind"] == "human_human"]
        self.assertAlmostEqual(s.pooled(real, "label", "1"), 50.0)
        self.assertAlmostEqual(s.pooled(real, "label", "2"), 80.0)
        self.assertAlmostEqual(s.pooled(hh, "label", "both"), 30.0)
        self.assertIsNone(s.pooled([], "label", "1"))

    def test_identical_papers_give_degenerate_interval(self):
        b = s.bootstrap(self.rows, n_boot=200)
        r = b["label"]
        self.assertEqual(r["real_human_covered"]["point"], 50.0)
        self.assertEqual(r["real_human_covered"]["ci95"], [50.0, 50.0])
        self.assertEqual(r["placebo_human_matched"]["ci95"], [0.0, 0.0])
        self.assertEqual(r["real_minus_human_human"]["point"], 20.0)
        self.assertEqual(b["n_papers"], 10)

    def test_interval_contains_point_and_is_deterministic(self):
        rows = self.rows + [row("real", "PX", 10, 5, 10, 5), row("human_human", "PX", 4, 6, 4, 6)]
        b1, b2 = s.bootstrap(rows, n_boot=300), s.bootstrap(rows, n_boot=300)
        self.assertEqual(b1, b2)
        v = b1["score>=30"]["real_human_covered"]
        self.assertLessEqual(v["ci95"][0], v["point"])
        self.assertGreaterEqual(v["ci95"][1], v["point"])
        self.assertLess(v["ci95"][0], v["ci95"][1])


class DocRefTests(unittest.TestCase):
    def test_doc_ref_uses_file_name_only(self):
        self.assertEqual(s.doc_ref("data/unjournal_evaluations/x.md"), s.doc_ref("x.md"))
        self.assertEqual(len(s.doc_ref("x.md")), 12)


if __name__ == "__main__":
    unittest.main()
