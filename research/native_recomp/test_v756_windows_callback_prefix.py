#!/usr/bin/env python3
"""Fail-closed Windows original callback-prologue integration tests."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v754_windows_alarm_return import owner_log
from windows_transfer_prefix_v751 import plan
from windows_callback_prefix_v756 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

ENTRY = b'V807_CALLBACK_ENTRY ordinal=6 identity=1 follow=3'
RESULT = (
    b'V807_CALLBACK_RESULT original_prologue=1 save_return=1 '
    b'stack_writes=8 visits=13 follow=3 continuation_executed=0 '
    b'callback_return=0 boot_verified=0'
)


def sample(tail=None, prefix=None):
    before = owner_log() if prefix is None else prefix
    events = [ENTRY, RESULT] if tail is None else tail
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(events) + b'\n'


class WindowsCallbackPrefix(unittest.TestCase):
    def test_exact_plan_and_pinned_owner_setup(self):
        p = plan('os-si-handler-time', False, False, False, False, False,
                 False, False, True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers, (
            ('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),
            ('transfer_return_observer', 'prepare_v777_transfer_return.py'),
            ('transfer_suffix_observer', 'prepare_v778_transfer_suffix.py'),
            ('alarm_return_observer', 'prepare_v786_alarm_return.py'),
            ('alarm_suffix_observer', 'prepare_v789_alarm_suffix.py'),
            ('callback_prefix_observer', 'prepare_v807_callback_prefix.py'),
        ))
        self.assertEqual(p.env, {
            'UNDERCOVER_V747_TIME_SUFFIX': '1',
            'UNDERCOVER_V777_TRANSFER_RETURN': '1',
            'UNDERCOVER_V778_TRANSFER_SUFFIX': '1',
            'UNDERCOVER_V786_ALARM_RETURN': '1',
            'UNDERCOVER_V789_ALARM_SUFFIX': '1',
            'UNDERCOVER_V807_CALLBACK_PREFIX': '1',
        })
        for args in (
            ('startup', False, False, False, False, False, False, False, True),
            ('os-si-handler-time', True, False, False, False, False, False, False, True),
            ('os-si-handler-time', False, True, False, False, False, False, False, True),
            ('os-si-handler-time', False, False, True, False, False, False, False, True),
            ('os-si-handler-time', False, False, False, True, False, False, False, True),
            ('os-si-handler-time', False, False, False, False, True, False, False, True),
            ('os-si-handler-time', False, False, False, False, False, True, False, True),
            ('os-si-handler-time', False, False, False, False, False, False, True, True),
            ('os-si-handler-time', False, False, False, False, False, False, False, 1),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(*args)

    def test_cli_wiring_and_refusal(self):
        self.assertIn('owner_callback_prefix', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-callback-prefix', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                command = [sys.executable, str(runner),
                           str(root/'missing-upstream'), str(root/'new-work'),
                           '--owner-scope', 'os-si-handler-time',
                           '--owner-callback-prefix']
                p = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('V426_WINDOWS_FAILED reason=transfer_scope', p.stdout)

    def test_original_entry_and_no_return_claim(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('callback_prefix_verified=1 ordinal=6', row)
        self.assertIn('compiler_save=1 continuation_executed=0', row)
        self.assertIn('callback_return=0 handler_return=0 boot_verified=0', row)
        row, ok = inspect(sample([ENTRY.replace(b'ordinal=6', b'ordinal=11'), RESULT]), 0)
        self.assertTrue(ok, row)
        self.assertIn('ordinal=11', row)
        for event in (ENTRY, RESULT):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' original=secret'))

    def test_exclusive_exact_tail(self):
        for bad in (
            [ENTRY], [RESULT, ENTRY], [ENTRY, RESULT, b'extra after stop'],
            [b'extra before callback', ENTRY, RESULT],
            [ENTRY, b'extra between events', RESULT],
            [ENTRY, ENTRY, RESULT],
            [ENTRY, RESULT, RESULT],
            [ENTRY, b'V807_CALLBACK_INVALID kind=4 stage=5 witness=3 device=0 visits=12', RESULT],
            [ENTRY.replace(b'ordinal=6', b'ordinal=7'), RESULT],
            [ENTRY.replace(b'identity=1', b'identity=0'), RESULT],
            [ENTRY.replace(b'follow=3', b'follow=2'), RESULT],
            [ENTRY, RESULT.replace(b'original_prologue=1', b'original_prologue=0')],
            [ENTRY, RESULT.replace(b'visits=13', b'visits=12')],
            [ENTRY, RESULT.replace(b'save_return=1', b'save_return=0')],
            [ENTRY, RESULT.replace(b'stack_writes=8', b'stack_writes=7')],
            [ENTRY, RESULT.replace(b'continuation_executed=0', b'continuation_executed=1')],
            [ENTRY, RESULT.replace(b'callback_return=0', b'callback_return=1')],
        ):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(sample(bad), 0)[1])

    def test_reject_predecessor_and_exit(self):
        before = owner_log()
        for bad in (
            before.replace(b'V786_ALARM_ENTRY lane=4 timer=1',
                           b'V786_ALARM_ENTRY lane=3 timer=1'),
            before.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                           b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
            before + b'V789_ALARM_BOUNDARY ordinal=6 kind=2 target_class=2 executed=0\n',
            before + b'V807_CALLBACK_ENTRY ordinal=6 identity=1 follow=3\n',
        ):
            self.assertFalse(inspect(sample(prefix=bad), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])
        for args in ((b'x'*(8*1024*1024 + 1), 0, False),
                     ('text', 0, False), (sample(), True, False),
                     (sample(), 0, 1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
