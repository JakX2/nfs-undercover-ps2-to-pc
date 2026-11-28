#!/usr/bin/env python3
"""Original-free Windows post-system-time boundary regression."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v434_windows_startup_scope import OS_SI_HANDLER_TIME, log
from windows_time_suffix_v750 import launch_overlay, inspect, diagnostic
from windows_full_build_v426 import build as windows_build

TAIL = [
    b'V726_HANDLER_CONTROL ordinal=4 kind=1 opcode=18',
    b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0',
    b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=32 polls=0',
]


def sample(prefix=None, tail=None):
    return log((OS_SI_HANDLER_TIME if prefix is None else prefix) +
               (TAIL if tail is None else tail))


class WindowsSuffixTests(unittest.TestCase):
    def test_explicit_option_and_legacy_control(self):
        self.assertEqual(launch_overlay('os-si-handler-time', False, False), {})
        self.assertEqual(launch_overlay('startup', True, False), {})
        self.assertEqual(launch_overlay('os-si-handler-time', False, True),
                         {'UNDERCOVER_V747_TIME_SUFFIX': '1'})
        for scope, synthetic in (('startup', False), ('os-si-os-leaves', False),
                                 ('os-si-handler-time', True)):
            with self.subTest(scope=scope, synthetic=synthetic):
                with self.assertRaises(ValueError):
                    launch_overlay(scope, synthetic, True)
        with self.assertRaises(ValueError):
            launch_overlay('os-si-handler-time', False, 1)

    def test_windows_runner_cli_refuses_unpaired_suffix(self):
        import inspect as std_inspect
        self.assertIn('owner_time_suffix', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-time-suffix', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                for scope in ('startup', 'os-si-handler-time'):
                    p = subprocess.run([sys.executable, str(runner),
                                        str(root/'missing-upstream'), str(root/'new-work'),
                                        '--owner-scope', scope, '--owner-time-suffix'],
                                       capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=suffix_scope', p.stdout)

    def test_exact_guarded_refusal(self):
        row, ok = inspect(sample(), 126)
        self.assertTrue(ok, row)
        self.assertIn('exit=expected_refusal', row)
        self.assertIn('time_verified=1 boundary_verified=1', row)
        self.assertIn('handler_return=0 boot_verified=0', row)
        self.assertTrue(diagnostic(TAIL[1]))
        self.assertFalse(diagnostic(TAIL[1] + b' original=secret'))

    def test_exit_and_timeout_never_claim_success(self):
        for rc, timeout in ((0, False), (1, False), (124, False),
                            (126, True), (0xC0000005, False),
                            (-1073741819, False)):
            with self.subTest(rc=rc, timeout=timeout):
                row, ok = inspect(sample(), rc, timeout)
                self.assertFalse(ok, row)
                self.assertIn('boundary_verified=0', row)
        self.assertIn('exit=timeout', inspect(sample(), 126, True)[0])

    def test_reject_modified_suffix_and_wrong_geometry(self):
        altered = [
            TAIL[:-1], [TAIL[0], TAIL[0], *TAIL[1:]], TAIL[::-1],
            [TAIL[0].replace(b'ordinal=4', b'ordinal=5'), *TAIL[1:]],
            [TAIL[0].replace(b'opcode=18', b'opcode=19'), *TAIL[1:]],
            [TAIL[0], TAIL[1].replace(b'executed=0', b'executed=1'), TAIL[2]],
            [TAIL[0], TAIL[1].replace(b'visits=32', b'visits=31'), TAIL[2]],
            [TAIL[0], TAIL[1], TAIL[2].replace(b'polls=0', b'polls=1')],
            [*TAIL, b'V726_HANDLER_STAGE n=3'],
            [*TAIL, b'unexpected host output after refusal'],
            [*TAIL, b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0'],
        ]
        for n, tail in enumerate(altered):
            with self.subTest(case=n):
                self.assertFalse(inspect(sample(tail=tail), 126)[1])

    def test_scope_and_prefix_cannot_be_forged(self):
        bad_inputs = [
            [*OS_SI_HANDLER_TIME, OS_SI_HANDLER_TIME[-1]],
            OS_SI_HANDLER_TIME[:-1],
            [*OS_SI_HANDLER_TIME[:-1], b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0',
             OS_SI_HANDLER_TIME[-1]],
            [b'V672_SI_ACK_INVALID reason=1 trace=0', *OS_SI_HANDLER_TIME],
            [*OS_SI_HANDLER_TIME[:-1],
             OS_SI_HANDLER_TIME[-1].replace(b'total=43', b'total=42')],
        ]
        for n, prefix in enumerate(bad_inputs):
            with self.subTest(prefix=n):
                self.assertFalse(inspect(sample(prefix=prefix), 126)[1])

    def test_unrelated_errors_after_time_return_are_rejected(self):
        for injection in (
            b'V672_SI_ACK_INVALID reason=1 trace=0',
            b'V742_TIME_INVALID reason=1 stage=2 leaf=3 witness=0 trace=1',
            b'V726_HANDLER_INVALID kind=1 witness=4 stage=2 visits=32 polls=0',
            b'V663_EXTERNAL_PENDING active=1',
            b'V726_HANDLER_STAGE n=3',
            b'V747_EXTRA_MARKER n=1',
        ):
            with self.subTest(injection=injection):
                self.assertFalse(inspect(sample(tail=[injection, *TAIL]), 126)[1])

    def test_invalid_inputs(self):
        for obj in (b'x' * (8 * 1024 * 1024 + 1), 'text', bytearray()):
            with self.assertRaises(ValueError):
                inspect(obj, 126)
        for rc, expired in ((True, False), (126, 1)):
            with self.assertRaises(ValueError):
                inspect(sample(), rc, expired)


if __name__ == '__main__':
    unittest.main()
