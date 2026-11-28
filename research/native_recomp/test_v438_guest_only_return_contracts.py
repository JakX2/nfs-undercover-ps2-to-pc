#!/usr/bin/env python3
"""Execute three original-free return witnesses in legacy and V438 guest-only modes.

The current native dispatcher emits a tick only at an authentic translated
PPC label. Never compensate with a phantom host-dispatch tick. Preserve the
legacy policy for independent regression/control builds.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCES=(
    ("test_callback_return_dispatch_v849.cpp","V849_RETURN_DISPATCH valid=2 refused=12"),
    ("test_si_handler_return_v725.cpp","V725_HANDLER_RETURN synthetic=1 valid=3 refused=17"),
    ("test_external_return_v706.cpp","V706_EXTERNAL_RETURN synthetic=1 cases=22 valid=1 rejects=21"),
    ("test_cold_external_entry_v663.cpp","V663_EXTERNAL synthetic=1 rejects=16"),
)


class NativeGuestOnlyReturnContracts(unittest.TestCase):
    def test_both_policies_execute_and_reject_invalid_guest_ticks(self):
        compiler=shutil.which("g++")
        if not compiler:self.skipTest("C++20 compiler unavailable")
        with tempfile.TemporaryDirectory() as work:
            for policy in (0,1):
                for i,(name,marker) in enumerate(SOURCES):
                    with self.subTest(policy=policy,source=name):
                        exe=Path(work)/f"v438-{policy}-{i}"
                        build=subprocess.run(
                            [compiler,"-std=c++20","-O1","-g","-Wall","-Wextra",
                             "-Werror","-fsanitize=address,undefined","-fno-pie",
                             "-no-pie","-fno-omit-frame-pointer","-I",str(HERE),
                             f"-DUNDERCOVER_WII_GUEST_ONLY_DISPATCH={policy}",
                             str(HERE/name),"-o",str(exe)],
                            capture_output=True,text=True,timeout=60)
                        self.assertEqual(build.returncode,0,build.stdout+build.stderr)
                        run=subprocess.run([str(exe)],capture_output=True,
                                           text=True,timeout=15)
                        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                        self.assertIn(marker,run.stdout)
                        self.assertNotIn("runtime error:",run.stderr)

    def test_unsupported_policy_is_compile_time_refused(self):
        compiler=shutil.which("g++")
        if not compiler:self.skipTest("C++20 compiler unavailable")
        source=HERE/SOURCES[0][0]
        bad=subprocess.run(
            [compiler,"-std=c++20","-fsyntax-only","-I",str(HERE),
             "-DUNDERCOVER_WII_GUEST_ONLY_DISPATCH=2",str(source)],
            capture_output=True,text=True,timeout=60)
        self.assertNotEqual(bad.returncode,0)
        self.assertIn("unknown native dispatch guest tick policy",bad.stderr)

    def test_windows_emitter_and_tick_policy_remain_coupled(self):
        from inspect import getsource
        from windows_full_build_v426 import build
        source=getsource(build)
        self.assertIn("run_stage('native_tick_labels'",source)
        self.assertIn("if not legacy_ticks:",source)
        self.assertIn("UNDERCOVER_WII_GUEST_ONLY_DISPATCH",source)
        self.assertIn("('0' if legacy_ticks else '1')",source)
        link=(HERE/'run_private_full_link.sh').read_text(encoding='utf-8')
        linux=(HERE/'run_v572_full_sc_translation.sh').read_text(encoding='utf-8')
        self.assertIn('DUNDERCOVER_WII_GUEST_ONLY_DISPATCH=$dispatch_policy',link)
        self.assertIn('UNDERCOVER_WII_GUEST_ONLY_DISPATCH=1 bash',linux)
        self.assertIn('apply_native_tick_v438',linux)


if __name__=="__main__":unittest.main()
