#!/usr/bin/env python3
"""V362 bounded real owner-harness completion, not a boot claim."""
import tempfile
import unittest
from pathlib import Path
from analyze_v362_bounded_native_exit import inspect
from diagnose_v299_native_log import WINDOW

GOOD=(
    "PASS: 1952 V77 recovered continuous original __start->ACK return "
    "and IOS reply assertions; mode=owner trials=16 stop=0x8052f830\n"
)

def run(text:str,code:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"private.log"
        p.write_text(text,encoding="utf-8")
        return inspect(p,code)

class Tests(unittest.TestCase):
    def test_exact_16_trial_owner_pass_but_not_game_boot(self):
        row=run("PRIVATE_GUEST_DATA\n"+GOOD)
        self.assertIn("rc=0 kind=zero size_band=0 sample_complete=1",row)
        self.assertIn("owner_pass=1 synthetic_pass=0 harness_complete=1 game_boot=0",row)
        self.assertNotIn("PRIVATE_GUEST_DATA",row)
        self.assertNotIn("private.log",row)

    def test_zero_exit_without_owner_pass_is_not_success(self):
        self.assertIn("harness_complete=0 game_boot=0",run("no PASS\n",0))

    def test_fatal_signal_cannot_complete_even_if_pass_marker_present(self):
        row=run(GOOD,134)
        self.assertIn("owner_pass=1 synthetic_pass=0 harness_complete=0",row)

    def test_synthetic_pass_cannot_impersonate_original_wii_harness(self):
        row=run(GOOD.replace("mode=owner","mode=synthetic"),0)
        self.assertIn("owner_pass=0 synthetic_pass=1 harness_complete=0",row)

    def test_partial_or_wrong_trial_marker_is_not_success(self):
        for corrupted in (
            GOOD.replace("trials=16","trials=8"),
            GOOD.replace("V77 recovered","V77 replaced"),
            GOOD.replace("stop=0x8052f830","stop=0xnothex"),
            "prefix "+GOOD,
        ):
            with self.subTest(marker=corrupted[:30]):
                self.assertIn("harness_complete=0",run(corrupted))

    def test_incomplete_log_sample_does_not_claim_missing_data(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"private.log"
            with p.open("wb") as f:
                f.write(b"some original guest data\n")
                f.seek(WINDOW+400)
                f.write(b"\n"+GOOD.encode("utf-8"))
            row=inspect(p,0)
            self.assertIn("sample_complete=0 owner_pass=1 harness_complete=1",row)

    def test_invalid_exit_code_is_fail_closed(self):
        for code in (-1,256):
            with self.assertRaises(ValueError):
                run(GOOD,code)

if __name__=="__main__":
    unittest.main()
