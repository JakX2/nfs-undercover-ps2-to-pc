#!/usr/bin/env python3
"""Synthetic, original-free safety tests for V178 private stage classifier."""
import tempfile
import unittest
from pathlib import Path
from diagnose_v178_run_stage import classify, details, STAGES, PREFLIGHT_SCRIPTS

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

    def test_inline_original_free_preflight_pinpoints_only_bounded_line(self):
        raw=('V110_WRAPPER syntax_ok\n'
             'Traceback (most recent call last):\n'
             '  File "<stdin>", line 10, in <module>\n'
             'AssertionError\n'
             'PRIVATE_FILE=/secret/owner.bin\n')
        self.assertEqual(classify(raw),
            'V178_FAILURE_STAGE phase=runner_preflight reason=python_error script=inline_cache_line_10')
        self.assertEqual(classify(raw.replace('line 10','line 999')),
            'V178_FAILURE_STAGE phase=runner_preflight reason=python_error script=none')

    def test_public_traceback_is_whitelisted_without_private_path(self):
        raw=('V110_WRAPPER syntax_ok\n'
             'Traceback (most recent call last):\n'
             '  File "/tmp/research/native_recomp/test_v178_run_stage.py", line 33\n'
             '  File "/private/research/secret/original_owner_tool.py", line 1\n'
             'ValueError: secret bytes 123456\n')
        self.assertEqual(classify(raw),
            'V178_FAILURE_STAGE phase=runner_preflight reason=python_error script=test_v178_run_stage')
        self.assertNotIn('/tmp/', classify(raw))
        self.assertNotIn('original_owner_tool', classify(raw))

    def test_v38_stage_and_exception_are_bounded(self):
        data=("V38_STAGE v29_runtime_verified\n"
              "V38_STAGE native_compiled\n"
              "Traceback (most recent call last):\n"
              "FileNotFoundError: private owner /mnt/originals/secret.dol\n")
        self.assertEqual(details(data),
                         "V178_FAILURE_DETAIL v38=native_compiled exception=FileNotFoundError")
        self.assertEqual(details("some raw private text\n"),
                         "V178_FAILURE_DETAIL v38=none exception=none")
        self.assertEqual(details(data+"\nSpecialPrivateError: no\n"),
                         "V178_FAILURE_DETAIL v38=native_compiled exception=none")
        self.assertNotIn("originals",details(data))

    def test_classifier_contract_matches_owner_workflow(self):
        # Only public files are inspected. A private failure must be reduced
        # to an ID before any user-visible CI output.
        flow=(Path(__file__).resolve().parents[2]/
              ".github/workflows/wii-v178-sc-reply-burst.yml").read_text(encoding="utf-8")
        self.assertIn("V67_NATIVE_ASSERTION id=[0-9]{3,4}",flow)
        self.assertNotIn("V178_NATIVE_ASSERTION id=[0-9]{4}",flow)
        self.assertIn('"$code" != "000"',flow)
        self.assertIn('"$code" != "0000"',flow)
        decoder=(Path(__file__).with_name("diagnose_v178_sc_reply_burst.py")
                 .read_text(encoding="utf-8"))
        self.assertIn("1<=index<=9999",decoder)
        classifier=(Path(__file__).with_name("classify_v38_native_failure.py")
                    .read_text(encoding="utf-8"))
        self.assertIn("index>9999",classifier)
        self.assertEqual(flow.count("      - name: Remove private owner and generated code"),1)

    def test_unknown_failure_class_is_explicit(self):
        self.assertEqual(classify(""),"V178_FAILURE_STAGE phase=wrapper reason=unclassified script=none")

    def test_oversized_log_fails_closed(self):
        with self.assertRaises(ValueError): classify("x"*25_000_001)

if __name__=="__main__":
    unittest.main()
