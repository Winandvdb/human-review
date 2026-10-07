"""The cost tab's "Voices" row: price formatting, the ledger narrate-cue.py writes, the
estimate for films recorded before it."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hrbuild.tabs import cost  # noqa: E402

spec = importlib.util.spec_from_file_location("narrate_cue", HERE / "narrate-cue.py")
nc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)


class Money(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(cost.voice_money(0), "< $0.01")
        self.assertEqual(cost.voice_money(0.004), "< $0.01")
        self.assertEqual(cost.voice_money(0.01), "$0.01")
        self.assertEqual(cost.voice_money(1.23), "$1.23")


class Ledger(unittest.TestCase):
    def _fish(self, tmp, calls):
        class Res:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s): calls.append(1); return b"RIFF"
        ledger = Path(tmp) / "a" / "feature.narration-cost.json"
        patches = [mock.patch.object(nc, "CACHE", Path(tmp) / "cache"),
                   mock.patch.object(nc.urllib.request, "urlopen", lambda *a, **k: Res()),
                   mock.patch.object(nc, "voiced_span", lambda p: (0.0, 1.0, 1.0)),
                   mock.patch.dict(nc.os.environ, {"HR_NARRATION_LEDGER": str(ledger)})]
        return ledger, patches

    def test_miss_writes_hit_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            ledger, patches = self._fish(tmp, calls)
            for p in patches: p.start()
            try:
                nc.fish("héllo", Path(tmp) / "o.wav", "k", 1.0, "v1")
                nc.fish("héllo", Path(tmp) / "o.wav", "k", 1.0, "v1")   # cache hit
            finally:
                for p in patches: p.stop()
            rows = json.loads(ledger.read_text())
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0]["bytes"], rows[0]["voice"], rows[0]["model"]),
                             (6, "v1", nc.FISH_MODEL))
            self.assertIn("at", rows[0])


class Row(unittest.TestCase):
    def _report(self, tmp, ledger=None):
        a = Path(tmp) / "assets"; a.mkdir()
        (a / "feature.voices.json").write_text(json.dumps([{"key": "x"}, {"key": "y"}]))
        (a / "feature.cues.json").write_text(json.dumps([{"text": "ab"}, {"text": "é"}]))
        if ledger is not None:
            (a / "feature.narration-cost.json").write_text(json.dumps(ledger))

    def test_estimate_free_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._report(tmp)
            v = cost.voices_cost(Path(tmp))
            self.assertTrue(v["estimated"])
            self.assertEqual((v["bytes"], v["voices"]), (8, 2))
            row = cost.voices_row_html(v)
            self.assertIn("&lt; $0.01</span>", row)
            self.assertIn("free model s2.1-pro-free", row)
            self.assertIn("estimated", row)
            self.assertIn("Fish Audio, 2 voices", row)

    def test_ledger_priced(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._report(tmp, [{"model": "s2.1-pro", "bytes": 200000}])
            v = cost.voices_cost(Path(tmp))
            self.assertFalse(v["estimated"])
            self.assertAlmostEqual(v["usd"], 3.0)
            self.assertIn("$3.00", cost.voices_row_html(v))

    def test_no_voices_no_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(cost.voices_cost(Path(tmp)))
            self.assertEqual(cost.voices_row_html(None), "")


if __name__ == "__main__":
    unittest.main()
