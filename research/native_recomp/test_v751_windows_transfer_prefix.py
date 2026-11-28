#!/usr/bin/env python3
"""Original-free Windows V751 fourth SI-handler call prefix regressions."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_v434_windows_startup_scope import OS_SI_HANDLER_TIME, log
from windows_transfer_prefix_v751 import launch_overlay, inspect, diagnostic, plan
from windows_full_build_v426 import build as windows_build

TAIL = [
    b'V768_TRANSFER_ENTRY channel=1 type=1 idle=1',
    b'V768_TRANSFER_RESULT original_entry=1 save=1 disable=1 boundary=1 visits=24 mmio_executed=0 boot_verified=0',
]


def sample(prefix=None, tail=None):
    return log((OS_SI_HANDLER_TIME if prefix is None else prefix) +
               (TAIL if tail is None else tail))


class WindowsTransferPrefixTests(unittest.TestCase):
    def test_transfer_analyzer_and_observer_contract(self):
        p = plan('os-si-handler-time', False, True, False)
        self.assertEqual(p.analyzer, ('--transfer-prefix',))
        self.assertEqual(p.observers, (('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),))
        self.assertEqual(p.env, launch_overlay('os-si-handler-time', False, True, False))
        control = plan('os-si-handler-time', False, False, False)
        self.assertEqual(control, ({}, (), ()))

    def test_isolated_launch_option(self):
        expected = {'UNDERCOVER_V747_TIME_SUFFIX': '1',
                    'UNDERCOVER_V768_TRANSFER_PREFIX': '1'}
        self.assertEqual(launch_overlay('os-si-handler-time', False, True, False), expected)
        self.assertEqual(launch_overlay('os-si-handler-time', False, False, True), {})
        for scope, synthetic, suffix in (
            ('startup', False, False), ('os-si-os-leaves', False, False),
            ('os-si-handler-time', True, False),
            ('os-si-handler-time', False, True),
        ):
            with self.subTest(scope=scope, synthetic=synthetic, suffix=suffix):
                with self.assertRaises(ValueError):
                    launch_overlay(scope, synthetic, True, suffix)
        for args in (
            ('os-si-handler-time', False, 1, False),
            ('os-si-handler-time', 0, True, False),
            ('os-si-handler-time', False, True, 0),
        ):
            with self.assertRaises(ValueError):
                launch_overlay(*args)

    def test_cli_wiring_and_refusal_for_unpaired_owner_flag(self):
        import inspect as std_inspect
        self.assertIn('owner_transfer_prefix', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-transfer-prefix', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                for extra, reason in (([], 'transfer_scope'),
                                      (['--owner-time-suffix'], 'suffix_scope')):
                    cmd = [sys.executable, str(runner),
                           str(root/'missing-upstream'), str(root/'fresh-work'),
                           '--owner-transfer-prefix', '--owner-scope',
                           'os-si-handler-time', *extra]
                    p = subprocess.run(cmd, capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=' + reason, p.stdout)

    def test_original_time_and_prefix_required(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('time_verified=1 transfer_prefix_verified=1', row)
        self.assertIn('mmio_executed=0 boot_verified=0', row)
        self.assertTrue(diagnostic(TAIL[0]))
        self.assertTrue(diagnostic(TAIL[1]))
        self.assertFalse(diagnostic(TAIL[1] + b' original=secret'))

    def test_no_extra_output_or_reordered_events(self):
        altered = [
            TAIL[:1], TAIL[::-1], [TAIL[0], TAIL[0], TAIL[1]],
            [*TAIL, b'unexpected host output'],
            [b'unexpected host output', *TAIL],
            [TAIL[0], b'unexpected host output', TAIL[1]],
            [TAIL[0], TAIL[1].replace(b'mmio_executed=0', b'mmio_executed=1')],
            [TAIL[0], TAIL[1].replace(b'save=1', b'save=0')],
            [TAIL[0], TAIL[1].replace(b'visits=24', b'visits=999')],
            [TAIL[0].replace(b'type=1', b'type=2'), TAIL[1]],
            [TAIL[0], b'V768_TRANSFER_INVALID kind=3 reason=2 stage=2 visits=9 trace=0', TAIL[1]],
        ]
        for n, tail in enumerate(altered):
            with self.subTest(case=n):
                self.assertFalse(inspect(sample(tail=tail), 0)[1])

    def test_no_foreign_event_before_time(self):
        for before in (
            [b'V768_TRANSFER_ENTRY channel=1 type=1 idle=1', *OS_SI_HANDLER_TIME],
            [*OS_SI_HANDLER_TIME[:-1], TAIL[0], OS_SI_HANDLER_TIME[-1]],
            OS_SI_HANDLER_TIME[:-1],
            [*OS_SI_HANDLER_TIME, OS_SI_HANDLER_TIME[-1]],
        ):
            with self.subTest(case=len(before)):
                self.assertFalse(inspect(sample(prefix=before), 0)[1])

    def test_exit_timeout_and_type_guards(self):
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])
        for arg in (b'x'*(8*1024*1024+1), 'text', bytearray()):
            with self.assertRaises(ValueError):
                inspect(arg, 0)
        for rc, timeout in ((True, False), (0, 1)):
            with self.assertRaises(ValueError):
                inspect(sample(), rc, timeout)


if __name__ == '__main__':
    unittest.main()
