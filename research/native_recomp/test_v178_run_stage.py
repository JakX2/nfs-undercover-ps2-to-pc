#!/usr/bin/env python3
"""Synthetic, original-free safety tests for V178 private stage classifier."""
import tempfile
import unittest
from pathlib import Path
from diagnose_v178_run_stage import classify, STAGES, PREFLIGHT_SCRIPTS

class StageTests(unittest.TestCase):
    def test_successive_runner_stages(self):
        s="V110_WRAPPER derived\nV110_WRAPPER syntax_ok\n"
        self.assertEqual(classify(s),"V178_FAILURE_STAGE phase=runner_preflight reason=unclassified script=none")
        for stage in STAGES:
            s+=f"V79_STAGE {stage}\n"
            self.assertEqual(classify(s),
                             f"V178_FAILURE_STAGE phase={stage} reason=unclassified script=none")

    def test_known_original_free_failures(self):
        self.assertEqual(classify(
            "V110_WRAPPER syntax_ok\nV71 inherited performance/HID4 runtime invalid\n"),
            "V178_FAILURE_STAGE phase=runner_preflight reason=verify_runtime script=none")
        self.assertEqual(classify(
            "V79_STAGE geometry_verified\nV73 generator compilation failed\n"),
            "V178_FAILURE_STAGE phase=geometry_verified reason=generator_compile script=none")
        self.assertEqual(classify(
            "V79_STAGE generation_complete\nV72 original translated native compilation failed\n"),
            "V178_FAILURE_STAGE phase=generation_complete reason=native_compile script=none")
        self.assertEqual(classify(
            "V79_STAGE native_compiled\nV67_NATIVE_ASSERTION id=321\n"),
            "V178_FAILURE_STAGE phase=native_compiled reason=native_assertion script=none")

    def test_does_not_echo_private_material_or_paths(self):
        sensitive=("PRIVATE_DOL: /root/private/owner.dol\n"
                   "DO_NOT_DISCLOSE=deadbeef12345678\n"
                   "secret key abcdef\n")
        output=classify("V110_WRAPPER derived\n"+sensitive)
        self.assertEqual(output,"V178_FAILURE_STAGE phase=runner_syntax reason=unclassified script=none")
        for forbidden in ("private","DO_NOT_DISCLOSE","deadbeef","secret","root"):
            self.assertNotIn(forbidden,output)

    def test_private_traceback_is_reduced_to_allowlisted_public_script(self):
        for name in PREFLIGHT_SCRIPTS:
            raw=("V110_WRAPPER syntax_ok\n"
                 "Traceback (most recent call last):\n"
                 '  File "/do/not/disclose/secret/'+name+'", line 15\n'
                 "PRIVATE_OWNER_KEY=bad\n")
            expected=("V178_FAILURE_STAGE phase=runner_preflight "
                      "reason=python_error script="+name[:-3])
            self.assertEqual(classify(raw),expected)
            self.assertNotIn("secret",classify(raw))

    def test_unknown_failure_class_is_explicit(self):
        self.assertEqual(classify(""),"V178_FAILURE_STAGE phase=wrapper reason=unclassified script=none")

    def test_oversized_log_fails_closed(self):
        with self.assertRaises(ValueError): classify("x"*25_000_001)

if __name__=="__main__":
    unittest.main()
