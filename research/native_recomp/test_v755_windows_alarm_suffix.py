#!/usr/bin/env python3
"""Strict original-free Windows V755 post-fifth-call SI boundary audit."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v754_windows_alarm_return import owner_log
from windows_transfer_prefix_v751 import plan
from windows_alarm_suffix_v755 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

CONTROL = b'V726_HANDLER_CONTROL ordinal=6 kind=2 opcode=19'
CLASS = b'V789_ALARM_BOUNDARY ordinal=6 kind=2 target_class=2 executed=0'
BOUNDARY = b'V778_NEXT_BOUNDARY ordinal=6 kind=2 visits=95 polls=2 follow=3 executed=0'
INVALID = b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=95 polls=2'
BLR = b'V778_HANDLER_BLR abi=1 visits=95 polls=2 follow=3 executed=0 boot_verified=0'
EVENTS = (CONTROL, CLASS, BOUNDARY, INVALID)


def sample(tail=EVENTS):
    return owner_log().rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


class WindowsAlarmSuffix(unittest.TestCase):
    def test_exact_plan(self):
        p = plan('os-si-handler-time', False, False, False, False, False, False, True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm'))
        self.assertEqual(p.observers, (
            ('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),
            ('transfer_return_observer', 'prepare_v777_transfer_return.py'),
            ('transfer_suffix_observer', 'prepare_v778_transfer_suffix.py'),
            ('alarm_return_observer', 'prepare_v786_alarm_return.py'),
            ('alarm_suffix_observer', 'prepare_v789_alarm_suffix.py'),
        ))
        self.assertEqual(p.env, {
            'UNDERCOVER_V747_TIME_SUFFIX': '1',
            'UNDERCOVER_V777_TRANSFER_RETURN': '1',
            'UNDERCOVER_V778_TRANSFER_SUFFIX': '1',
            'UNDERCOVER_V786_ALARM_RETURN': '1',
            'UNDERCOVER_V789_ALARM_SUFFIX': '1',
        })
        for args in (
            ('startup', False, False, False, False, False, False, True),
            ('os-si-handler-time', True, False, False, False, False, False, True),
            ('os-si-handler-time', False, True, False, False, False, False, True),
            ('os-si-handler-time', False, False, True, False, False, False, True),
            ('os-si-handler-time', False, False, False, True, False, False, True),
            ('os-si-handler-time', False, False, False, False, True, False, True),
            ('os-si-handler-time', False, False, False, False, False, True, True),
            ('os-si-handler-time', False, False, False, False, False, False, 1),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(*args)

    def test_cli_and_synthetic_refusal(self):
        self.assertIn('owner_alarm_suffix', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-alarm-suffix', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                command = [sys.executable, str(runner),
                           str(root/'missing-upstream'), str(root/'new-work'),
                           '--owner-scope', 'os-si-handler-time',
                           '--owner-alarm-suffix']
                p = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('V426_WINDOWS_FAILED reason=transfer_scope', p.stdout)

    def test_next_authenticated_call_and_handler_blr(self):
        row, ok = inspect(sample(), 126)
        self.assertTrue(ok, row)
        self.assertIn('suffix_verified=1 ordinal=6 kind=2 target_class=2', row)
        self.assertIn('target_executed=0 handler_return=0 boot_verified=0', row)
        row, ok = inspect(sample((BLR,)), 0)
        self.assertTrue(ok, row)
        self.assertIn('suffix_verified=1 ordinal=0 kind=0', row)
        self.assertIn('blr_boundary=1', row)
        for event in (*EVENTS, BLR):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' private=secret'))

    def test_direct_and_indirect_guards(self):
        direct = (
            CONTROL.replace(b'kind=2 opcode=19', b'kind=1 opcode=18'),
            CLASS.replace(b'kind=2 target_class=2', b'kind=1 target_class=0'),
            BOUNDARY.replace(b'kind=2', b'kind=1'),
            INVALID,
        )
        row, ok = inspect(sample(direct), 126)
        self.assertTrue(ok, row)
        self.assertIn('target_class=0', row)
        for kind in (1, 3, 4):
            alt = CLASS.replace(b'target_class=2', ('target_class=%d' % kind).encode())
            self.assertTrue(inspect(sample((CONTROL, alt, BOUNDARY, INVALID)), 126)[1])

    def test_reject_extra_interleaved_and_bad_identity(self):
        candidates = [
            EVENTS[:-1], EVENTS[::-1], (*EVENTS, b'extra after stop'),
            (b'extra before boundary', *EVENTS),
            (CONTROL, b'extra within boundary', *EVENTS[1:]),
            (CONTROL, CLASS, CLASS, BOUNDARY, INVALID),
            (CONTROL, CLASS, BOUNDARY, b'V786_ALARM_INVALID kind=1 route=0 queue=0 mismatch=0 device=0 stage=0 visits=10', INVALID),
            (CONTROL, CLASS.replace(b'executed=0', b'executed=1'), BOUNDARY, INVALID),
            (CONTROL, CLASS.replace(b'target_class=2', b'target_class=0'), BOUNDARY, INVALID),
            (CONTROL.replace(b'ordinal=6', b'ordinal=7'), CLASS, BOUNDARY, INVALID),
            (CONTROL, CLASS.replace(b'ordinal=6', b'ordinal=7'), BOUNDARY, INVALID),
            (CONTROL, CLASS, BOUNDARY.replace(b'follow=3', b'follow=0'), INVALID),
            (CONTROL, CLASS, BOUNDARY.replace(b'visits=95', b'visits=9999'), INVALID),
            (CONTROL, CLASS, BOUNDARY, INVALID.replace(b'polls=2', b'polls=3')),
        ]
        for candidate in candidates:
            with self.subTest(events=candidate):
                self.assertFalse(inspect(sample(candidate), 126)[1])

    def test_reject_corrupt_predecessor_and_exit(self):
        raw = sample()
        for bad in (
            raw.replace(b'V786_ALARM_ENTRY lane=4 timer=1',
                        b'V786_ALARM_ENTRY lane=3 timer=1'),
            raw.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                        b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
            raw.replace(b'V786_ALARM_RESULT original_return=1',
                        b'V786_ALARM_RESULT original_return=0'),
            raw.replace(b'V786_ALARM_RESULT original_return=1',
                        b'V789_ALARM_BOUNDARY ordinal=6 kind=2 target_class=2 executed=0\nV786_ALARM_RESULT original_return=1'),
        ):
            with self.subTest(tail=bad[-130:]):
                self.assertFalse(inspect(bad, 126)[1])
        self.assertFalse(inspect(sample((BLR,)), 126)[1])
        self.assertFalse(inspect(sample(), 0)[1])
        for rc, timeout in ((126, True), (1, False), (0xC0000005, False),
                            (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])
        for args in ((b'x'*(8*1024*1024 + 1), 126, False),
                     ('text', 126, False), (sample(), True, False),
                     (sample(), 126, 1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
