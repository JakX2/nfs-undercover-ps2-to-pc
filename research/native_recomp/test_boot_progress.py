#!/usr/bin/env python3
"""Source-only tests for boot_progress, with no game executable or assets."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

from boot_progress import main


class BootProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.report = self.root / "report.json"

    def invoke(self, code, extra=None, lane="synthetic", timeout="3", report=None):
        argv = ["--lane", lane, "--report", str(report or self.report), "--timeout", timeout]
        argv += extra or []
        argv += ["--", sys.executable, "-c", code]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = main(argv)
        data = json.loads((report or self.report).read_text()) if (report or self.report).exists() else None
        return rc, data

    def test_uninstrumented_not_misreported_as_checkpoint(self):
        rc, info = self.invoke("print('PASS: synthetic native test')")
        self.assertEqual(rc, 0)
        self.assertEqual(info["status"], "passed_uninstrumented")
        self.assertIsNone(info["observed_pc"])

    def test_verified_original_start_marker(self):
        rc, info = self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                               lane="continuous-start")
        self.assertEqual(rc, 0)
        self.assertEqual(info["status"], "passed_instrumented")
        self.assertEqual(info["observed_pc"], 0x805206B4)
        self.assertEqual(info["stage"], 26)

    def test_stage_advance_requires_new_pc_and_stage(self):
        self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                    lane="continuous-start")
        old = self.root / "baseline.json"
        self.report.replace(old)
        rc, data = self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805208C4 stage=27')",
                               ["--baseline", str(old), "--require-progress"], lane="continuous-start")
        self.assertEqual(rc, 0)
        self.assertEqual(data["status"], "advanced")
        self.assertEqual(data["observed_pc"], 0x805208C4)

    def test_regressed_stage_is_rejected(self):
        self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805208C4 stage=27')",
                    lane="continuous-start")
        old = self.root / "baseline.json"
        self.report.replace(old)
        rc, data = self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                               ["--baseline", str(old), "--require-progress"], lane="continuous-start")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "no_verified_stage_advance")

    def test_wrong_lane_does_not_compare(self):
        self.invoke("print('PASS: ok\\nBOOT_PROGRESS entry=0x80520670 pc=0x805208C4 stage=68')",
                    lane="osinit-direct")
        old = self.root / "baseline.json"
        self.report.replace(old)
        rc, data = self.invoke("print('PASS: ok')", ["--baseline", str(old), "--require-progress"], lane="continuous-start")
        self.assertEqual(rc, 2)
        self.assertIsNone(data)

    def test_missing_expected_stop(self):
        rc, data = self.invoke("print('PASS: ok')", ["--expected-pc", "0x805208C4"])
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "expected_stop_not_observed")

    def test_nonzero_exit_and_no_pass(self):
        rc, data = self.invoke("print('PASS: seems okay');raise SystemExit(7)")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "runner_failed")
        rc, data = self.invoke("print('all fine')")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "no_native_pass_marker")

    def test_timeout_is_recorded_without_original_log(self):
        rc, data = self.invoke("import time;time.sleep(1)", timeout="0.02")
        self.assertEqual(rc, 1)
        self.assertTrue(data["timed_out"])
        self.assertEqual(data["failure_reason"], "timeout")

    def test_refuses_unpinned_or_mismatched_dol(self):
        fixture = self.root / "PRIVATE_EXAMPLE.dol"
        fixture.write_bytes(b"not original data")
        extra = ["--dol", str(fixture), "--sha256", "0" * 64]
        rc, _ = self.invoke("print('PASS: should not run')", extra)
        self.assertEqual(rc, 2)
        self.assertFalse(self.report.exists())

    def test_report_does_not_leak_arguments_or_output(self):
        secret = "private-game-path-DO-NOT-LOG"
        rc, data = self.invoke(f"print('PASS: {secret}')")
        self.assertEqual(rc, 0)
        serialized = self.report.read_text()
        self.assertNotIn(secret, serialized)
        self.assertNotIn(sys.executable, serialized)
        self.assertIsNone(data["owner_image_sha256"])

    def test_conflicting_checkpoint_markers(self):
        code = "print('PASS: ok\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B8 stage=27')"
        rc, data = self.invoke(code, lane="continuous-start")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "conflicting_guest_checkpoints")


    def test_failed_runner_cannot_publish_checkpoint(self):
        code = "print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805208C4 stage=27');raise SystemExit(7)"
        rc, data = self.invoke(code, lane="continuous-start")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "runner_failed")
        self.assertIsNone(data["observed_pc"])
        self.assertIsNone(data["observed_entry"])
        self.assertIsNone(data["stage"])

    def test_timeout_cannot_publish_early_checkpoint(self):
        code = "import time;print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805208C4 stage=27',flush=True);time.sleep(1)"
        rc, data = self.invoke(code, lane="continuous-start", timeout="0.02")
        self.assertEqual(rc, 1)
        self.assertEqual(data["failure_reason"], "timeout")
        self.assertIsNone(data["observed_pc"])

    def test_report_must_not_overwrite_pinned_input(self):
        private_input = self.root / "synthetic_fixture.bin"
        payload = b"independently-authored-test-image"
        private_input.write_bytes(payload)
        args = ["--lane", "synthetic", "--report", str(private_input),
                "--dol", str(private_input),
                "--sha256", hashlib.sha256(payload).hexdigest(),
                "--", sys.executable, "-c", "print('PASS: synthetic')"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = main(args)
        self.assertEqual(rc, 2)
        self.assertEqual(private_input.read_bytes(), payload)

    def test_report_must_not_overwrite_baseline(self):
        self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                    lane="continuous-start")
        baseline = self.root / "baseline.json"
        self.report.replace(baseline)
        original = baseline.read_bytes()
        rc, _ = self.invoke("print('PASS: synthetic')",
                            ["--baseline", str(baseline)], lane="continuous-start",
                            report=baseline)
        self.assertEqual(rc, 2)
        self.assertEqual(baseline.read_bytes(), original)

    def test_corrupt_baseline_is_rejected_before_launch(self):
        self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                    lane="continuous-start")
        baseline = self.root / "baseline.json"
        self.report.replace(baseline)
        original = json.loads(baseline.read_text())
        for changes in ({"schema": "foreign-schema"},
                        {"observed_entry": 0x80520670},
                        {"stage": True},
                        {"observed_pc": -1}):
            baseline.write_text(json.dumps(dict(original, **changes)))
            rc, data = self.invoke("print('PASS: synthetic')",
                                   ["--baseline", str(baseline)],
                                   lane="continuous-start")
            self.assertEqual(rc, 2)
            self.assertIsNone(data)

    def test_checkpoint_baseline_must_match_pinned_owner(self):
        self.invoke("print('PASS: synthetic\\nBOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26')",
                    lane="continuous-start")
        baseline = self.root / "baseline.json"
        self.report.replace(baseline)
        fixture = self.root / "synthetic_fixture.bin"
        fixture.write_bytes(b"not proprietary content")
        rc, data = self.invoke("print('PASS: synthetic')",
                               ["--baseline", str(baseline), "--dol", str(fixture),
                                "--sha256", hashlib.sha256(fixture.read_bytes()).hexdigest()],
                               lane="continuous-start")
        self.assertEqual(rc, 2)
        self.assertIsNone(data)


    def test_failure_diagnostics_only_show_allowlisted_original_free_stages(self):
        secret = "owner-private-DO-NOT-PRINT"
        code = (
            "print('V35_STAGE v29_runtime_verified', flush=True);"
            "print('V35_STAGE fixture_generated', flush=True);"
            f"print('{secret}', flush=True);"
            "print('V35_STAGE injected-source-bytecode', flush=True);"
            "raise SystemExit(7)"
        )
        args = ["--lane", "synthetic", "--report", str(self.report),
                "--diagnostic-runner", "V35", "--", sys.executable, "-c", code]
        output = io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        emitted=output.getvalue()
        self.assertIn("BOOT_DIAGNOSTIC stage=V35.v29_runtime_verified",emitted)
        self.assertIn("BOOT_DIAGNOSTIC stage=V35.fixture_generated",emitted)
        self.assertNotIn(secret,emitted)
        self.assertNotIn("injected-source-bytecode",emitted)
        self.assertNotIn(secret,self.report.read_text())
        self.assertEqual(json.loads(self.report.read_text())["status"],"failed")

    def test_success_does_not_emit_diagnostic_or_break_checkpoint(self):
        code=("print('V35_STAGE native_compiled')\n"
              "print('PASS: independent synthetic')\n"
              "print('BOOT_PROGRESS entry=0x8000403C pc=0x80520CA8 stage=35')")
        args=["--lane","continuous-start","--report",str(self.report),
              "--diagnostic-runner","V35","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,0)
        self.assertNotIn("BOOT_DIAGNOSTIC",output.getvalue())
        self.assertEqual(json.loads(self.report.read_text())["observed_pc"],0x80520CA8)

    def test_numeric_public_only_assertion_diagnostic(self):
        code=(
            "print('V35_STAGE native_compiled',flush=True);"
            "print('V35_NATIVE_ASSERTION id=027',flush=True);"
            "print('V35_NATIVE_ASSERTION id=unsafe-private-memory',flush=True);"
            "raise SystemExit(7)"
        )
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V35","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V35.027",output.getvalue())
        self.assertNotIn("unsafe-private-memory",output.getvalue())
        self.assertNotIn("unsafe-private-memory",self.report.read_text())

    def test_v36_numeric_diagnostic_keeps_original_content_private(self):
        private="PRIV_opaque_wii_original_instruction_data"
        code=(
            "print('V36_STAGE native_compiled',flush=True);"
            "print('V36_NATIVE_ASSERTION id=043',flush=True);"
            f"print('{private}',flush=True);"
            "raise SystemExit(9)"
        )
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V36","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V36.native_compiled",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V36.043",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v37_guarded_numeric_diagnostics(self):
        code=(
            "print('V37_STAGE native_compiled',flush=True);"
            "print('V37_NATIVE_ASSERTION id=037',flush=True);"
            "print('private-exception-vector-data',flush=True);"
            "raise SystemExit(7)"
        )
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V37","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V37.native_compiled",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V37.037",output.getvalue())
        self.assertNotIn("private-exception-vector-data",output.getvalue())
        self.assertNotIn("private-exception-vector-data",self.report.read_text())

    def test_v38_original_free_diagnostics(self):
        code=(
            "print('V38_STAGE negative_guards_verified',flush=True);"
            "print('V38_NATIVE_ASSERTION id=038',flush=True);"
            "print('secret-owner-vector-template-bytes',flush=True);"
            "raise SystemExit(7)"
        )
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V38","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V38.negative_guards_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V38.038",output.getvalue())
        self.assertNotIn("secret-owner-vector-template-bytes",output.getvalue())
        self.assertNotIn("secret-owner-vector-template-bytes",self.report.read_text())

    def test_v52_safe_stages_and_numeric_diagnostic_only(self):
        private = "private-owner-EXI-guest-instruction-bytes"
        code = (
            "print('V52_STAGE fixture_generated',flush=True);"
            "print('V52_STAGE native_compiled',flush=True);"
            "print('V52_STAGE untrusted-leak',flush=True);"
            "print('V52_NATIVE_ASSERTION id=052',flush=True);"
            f"print('{private}',flush=True);"
            "raise SystemExit(7)"
        )
        args = ["--lane", "synthetic", "--report", str(self.report),
                "--diagnostic-runner", "V52", "--", sys.executable, "-c", code]
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            rc = main(args)
        self.assertEqual(rc, 1)
        emitted = output.getvalue()
        self.assertIn("BOOT_DIAGNOSTIC stage=V52.fixture_generated", emitted)
        self.assertIn("BOOT_DIAGNOSTIC stage=V52.native_compiled", emitted)
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V52.052", emitted)
        self.assertNotIn("untrusted-leak", emitted)
        self.assertNotIn(private, emitted)
        self.assertNotIn(private, self.report.read_text())

    def test_v53_original_free_diagnostics(self):
        secret = "private-owner-guest-original-data"
        code = (
            "print('V53_STAGE fixture_generated',flush=True);"
            "print('V53_STAGE native_compiled',flush=True);"
            "print('V53_NATIVE_ASSERTION id=053',flush=True);"
            f"print('{secret}',flush=True);"
            "raise SystemExit(7)"
        )
        args = ["--lane", "synthetic", "--report", str(self.report),
                "--diagnostic-runner", "V53", "--", sys.executable, "-c", code]
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V53.fixture_generated",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC stage=V53.native_compiled",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V53.053",output.getvalue())
        self.assertNotIn(secret,output.getvalue())
        self.assertNotIn(secret,self.report.read_text())

    def test_v54_safe_diagnostic_ids(self):
        private="original-owner-exi-handler-private-bytes"
        code=("print('V54_STAGE geometry_verified',flush=True);"
              "print('V54_NATIVE_ASSERTION id=054',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V54","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V54.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V54.054",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v55_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V55_STAGE geometry_verified',flush=True);"
              "print('V55_NATIVE_ASSERTION id=055',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V55","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V55.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V55.055",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v56_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V56_STAGE geometry_verified',flush=True);"
              "print('V56_NATIVE_ASSERTION id=056',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V56","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V56.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V56.056",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v57_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V57_STAGE geometry_verified',flush=True);"
              "print('V57_NATIVE_ASSERTION id=057',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V57","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V57.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V57.057",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v58_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V58_STAGE geometry_verified',flush=True);"
              "print('V58_NATIVE_ASSERTION id=058',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V58","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V58.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V58.058",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v59_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V59_STAGE geometry_verified',flush=True);"
              "print('V59_NATIVE_ASSERTION id=059',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V59","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V59.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V59.059",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v60_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V60_STAGE geometry_verified',flush=True);"
              "print('V60_NATIVE_ASSERTION id=060',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V60","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V60.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V60.060",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v61_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V61_STAGE geometry_verified',flush=True);"
              "print('V61_NATIVE_ASSERTION id=061',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V61","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V61.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V61.061",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v62_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V62_STAGE geometry_verified',flush=True);"
              "print('V62_NATIVE_ASSERTION id=062',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V62","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V62.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V62.062",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v63_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V63_STAGE geometry_verified',flush=True);"
              "print('V63_NATIVE_ASSERTION id=063',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V63","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V63.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V63.063",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v64_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V64_STAGE geometry_verified',flush=True);"
              "print('V64_NATIVE_ASSERTION id=064',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V64","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V64.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V64.064",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v65_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V65_STAGE geometry_verified',flush=True);"
              "print('V65_NATIVE_ASSERTION id=065',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V65","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V65.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V65.065",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_v66_masked_private_diagnostic(self):
        private="owner-original-ID-private-dol-text"
        code=("print('V66_STAGE geometry_verified',flush=True);"
              "print('V66_NATIVE_ASSERTION id=066',flush=True);"
              f"print('{private}',flush=True);"
              "raise SystemExit(7)")
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","V66","--",sys.executable,"-c",code]
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            rc=main(args)
        self.assertEqual(rc,1)
        self.assertIn("BOOT_DIAGNOSTIC stage=V66.geometry_verified",output.getvalue())
        self.assertIn("BOOT_DIAGNOSTIC assertion_id=V66.066",output.getvalue())
        self.assertNotIn(private,output.getvalue())
        self.assertNotIn(private,self.report.read_text())

    def test_unknown_diagnostic_prefix_rejected(self):
        args=["--lane","synthetic","--report",str(self.report),
              "--diagnostic-runner","secrets_dump","--",
              sys.executable,"-c","print('PASS: synthetic')"]
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                main(args)
        self.assertEqual(stopped.exception.code,2)
        self.assertFalse(self.report.exists())

if __name__ == "__main__":
    unittest.main()
