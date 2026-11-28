#!/usr/bin/env python3
"""Source-only, fail-closed Windows fifth original SI alarm-return checks."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v752_windows_transfer_return import sample
from windows_transfer_prefix_v751 import plan
from windows_alarm_return_v754 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

ENTRY = b'V786_ALARM_ENTRY lane=4 timer=1'
RESULT = (
    b'V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane=4 '
    b'timer=1 deferred=1 calls=77 visits=90 polls=1 follow=3 '
    b'handler_instruction_executed=0 boot_verified=0'
)


def owner_log(tail=None, prefix=None):
    before = sample() if prefix is None else prefix
    events = [ENTRY, RESULT] if tail is None else tail
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(events) + b'\n'


class WindowsAlarmReturn(unittest.TestCase):
    def test_exact_plan_and_order(self):
        p = plan('os-si-handler-time', False, False, False, False, False, True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm'))
        self.assertEqual(p.observers, (
            ('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),
            ('transfer_return_observer', 'prepare_v777_transfer_return.py'),
            ('transfer_suffix_observer', 'prepare_v778_transfer_suffix.py'),
            ('alarm_return_observer', 'prepare_v786_alarm_return.py'),
        ))
        self.assertEqual(p.env, {
            'UNDERCOVER_V747_TIME_SUFFIX': '1',
            'UNDERCOVER_V777_TRANSFER_RETURN': '1',
            'UNDERCOVER_V778_TRANSFER_SUFFIX': '1',
            'UNDERCOVER_V786_ALARM_RETURN': '1',
        })
        for args in (
            ('startup', False, False, False, False, False, True),
            ('os-si-handler-time', True, False, False, False, False, True),
            ('os-si-handler-time', False, True, False, False, False, True),
            ('os-si-handler-time', False, False, True, False, False, True),
            ('os-si-handler-time', False, False, False, True, False, True),
            ('os-si-handler-time', False, False, False, False, True, True),
            ('os-si-handler-time', False, False, False, False, False, 1),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(*args)

    def test_cli_and_synthetic_refusal(self):
        self.assertIn('owner_alarm_return', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-alarm-return', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                command = [sys.executable, str(runner),
                           str(root/'missing-upstream'), str(root/'new-work'),
                           '--owner-scope', 'os-si-handler-time',
                           '--owner-alarm-return']
                p = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('V426_WINDOWS_FAILED reason=transfer_scope', p.stdout)

    def test_verified_alarm_return_and_no_handler_claim(self):
        row, ok = inspect(owner_log(), 0)
        self.assertTrue(ok, row)
        self.assertIn('alarm_return_verified=1 lane=4 timer=1 deferred=1 calls=77', row)
        self.assertIn('handler_resume=0 handler_return=0 boot_verified=0', row)
        for event in (ENTRY, RESULT):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' private=secret'))

    def test_other_original_alarm_lanes(self):
        entry = b'V786_ALARM_ENTRY lane=0 timer=0'
        result = (b'V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane=0 '
                  b'timer=0 deferred=0 calls=3 visits=90 polls=1 follow=3 '
                  b'handler_instruction_executed=0 boot_verified=0')
        row, ok = inspect(owner_log([entry, result]), 0)
        self.assertTrue(ok, row)
        self.assertIn('lane=0 timer=0 deferred=0 calls=3', row)

    def test_exact_tail_and_semantic_refusals(self):
        invalid = (
            [ENTRY], [RESULT, ENTRY], [ENTRY, RESULT, b'extra after return'],
            [b'extra before entry', ENTRY, RESULT],
            [ENTRY, b'extra between events', RESULT],
            [ENTRY, b'V786_ALARM_INVALID kind=3 route=2 queue=0 mismatch=0 device=0 stage=2 visits=9', RESULT],
            [ENTRY, RESULT.replace(b'original_return=1', b'original_return=0')],
            [ENTRY, RESULT.replace(b'queue=1', b'queue=0')],
            [ENTRY, RESULT.replace(b'lane=4', b'lane=3')],
            [ENTRY, RESULT.replace(b'timer=1', b'timer=0')],
            [ENTRY, RESULT.replace(b'deferred=1', b'deferred=2')],
            [ENTRY, RESULT.replace(b'calls=77', b'calls=65')],
            [ENTRY, RESULT.replace(b'follow=3', b'follow=0')],
            [ENTRY, RESULT.replace(b'visits=90', b'visits=999')],
            [ENTRY, RESULT.replace(b'handler_instruction_executed=0',
                                   b'handler_instruction_executed=1')],
        )
        for tail in invalid:
            with self.subTest(tail=tail):
                self.assertFalse(inspect(owner_log(tail), 0)[1])

    def test_predecessor_and_exit_refusals(self):
        prefix = sample()
        for before in (
            prefix + b'V778_NEXT_BOUNDARY ordinal=5 kind=1 visits=40 polls=2 follow=3 executed=0\n',
            prefix + b'V786_ALARM_ENTRY lane=4 timer=1\n',
            prefix + b'V789_ALARM_BOUNDARY ordinal=6 kind=2 target_class=2 executed=0\n',
            prefix + b'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle=1 irq_lane=2 reads=2 writes=3 follow=3 pending=0 total=120 handler_instruction_executed=0 boot_verified=0\n',
            sample().replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1 ack_identity=1',
                             b'V777_TRANSFER_HANDOFF scheduler_tick=0 ack_identity=1'),
        ):
            with self.subTest(before=before[-100:]):
                self.assertFalse(inspect(owner_log(prefix=before), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(owner_log(), rc, timeout)[1])
        for args in ((b'x' * (8*1024*1024 + 1), 0, False),
                     ('text', 0, False), (owner_log(), True, False),
                     (owner_log(), 0, 1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
