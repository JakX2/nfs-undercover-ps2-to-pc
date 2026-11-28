#!/usr/bin/env python3
"""Windows private EXI profile-backed native wireless write controls."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v760_windows_wireless_wrapper import (
    sample as wrapper_sample, CHANGED_ENTRY, CHANGED_RESULT,
)
from windows_transfer_prefix_v751 import plan
from windows_wireless_write_v761 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

RESULT = (
    b'V861_WIRELESS_WRITE_RESULT original_setter_return=1 original_unlock=1 '
    b'transfers=12 bytes=44 visits=3187 polls=74 mmio=52 payload=1 abi=1 '
    b'callback_return=0 boot_verified=0'
)


def changed_sample(tail=(RESULT,), prefix=None):
    before = wrapper_sample((CHANGED_ENTRY, CHANGED_RESULT)) if prefix is None else prefix
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


class WindowsWirelessWrite(unittest.TestCase):
    def test_owner_plan_and_exact_native_observer_order(self):
        p = plan('os-si-handler-time', False, False, False, wireless_write=True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers[-3:],
                         (('callback_frontier_observer', 'prepare_v831_callback_frontier.py'),
                          ('wireless_wrapper_observer', 'prepare_v847_wireless_wrapper.py'),
                          ('wireless_write_observer', 'prepare_v861_wireless_write.py')))
        for key in ('UNDERCOVER_V807_CALLBACK_PREFIX',
                    'UNDERCOVER_V813_CALLBACK_TIME',
                    'UNDERCOVER_V831_CALLBACK_FRONTIER',
                    'UNDERCOVER_V847_WIRELESS',
                    'UNDERCOVER_V861_WIRELESS_WRITE'):
            self.assertEqual(p.env[key], '1')
        for args in (
            {'scope': 'startup'}, {'synthetic': True}, {'prefix': True},
            {'time_suffix': True}, {'returned': True}, {'suffix': True},
            {'alarm': True}, {'alarm_suffix': True},
            {'callback_prefix': True}, {'callback_time': True},
            {'callback_frontier': True}, {'wireless_wrapper': True},
        ):
            settings = dict(scope='os-si-handler-time', synthetic=False,
                            prefix=False, time_suffix=False, wireless_write=True)
            settings.update(args)
            with self.subTest(settings=args), self.assertRaises(ValueError):
                plan(**settings)

    def test_cli_and_refuse_no_owner_original(self):
        self.assertIn('owner_wireless_write', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-wireless-write', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td)
                for extra in ([], ['--owner-progression-matrix'],
                              ['--owner-wireless-wrapper'],
                              ['--owner-callback-frontier']):
                    p = subprocess.run(
                        [sys.executable, str(runner),
                         str(folder/'missing-upstream'), str(folder/'new-work'),
                         '--owner-scope', 'os-si-handler-time',
                         '--owner-wireless-write', *extra],
                        capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=wireless_write_scope',
                                  p.stdout)

    def test_changed_original_exi_transaction(self):
        row, ok = inspect(changed_sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('wrapper_verified=1 write_verified=1', row)
        self.assertIn('ordinal=3 changed=1', row)
        self.assertIn('transfers=12 bytes=44', row)
        self.assertIn('visits=3187 polls=74 mmio=52', row)
        self.assertIn('original_unlock=1', row)
        self.assertIn('callback_return=0 handler_return=0 boot_verified=0', row)

    def test_original_no_write_path(self):
        row, ok = inspect(wrapper_sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('write_verified=1', row)
        self.assertIn('changed=0 transfers=0 bytes=0', row)
        self.assertIn('original_unlock=0', row)

    def test_reject_false_mmio_completion(self):
        for bad in ((RESULT, RESULT), (RESULT, b'extra'), (b'extra', RESULT),
                    (RESULT.replace(b'transfers=12', b'transfers=11'),),
                    (RESULT.replace(b'bytes=44', b'bytes=40'),),
                    (RESULT.replace(b'visits=3187', b'visits=12001'),),
                    (RESULT.replace(b'visits=3187', b'visits=62'),),
                    (RESULT.replace(b'polls=74', b'polls=0'),),
                    (RESULT.replace(b'mmio=52', b'mmio=4097'),),
                    (RESULT.replace(b'original_unlock=1', b'original_unlock=0'),),
                    (RESULT.replace(b'abi=1', b'abi=0'),),
                    (RESULT.replace(b'callback_return=0', b'callback_return=1'),),
                    (b'V861_WIRELESS_WRITE_INVALID kind=5 device=2 reason=3 witness=0 completed=3 bytes=8', RESULT)):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(changed_sample(bad), 0)[1])

    def test_reject_predecessor_substitution(self):
        before = wrapper_sample((CHANGED_ENTRY, CHANGED_RESULT))
        for bad in (
            before.replace(b'V847_WIRELESS_RESULT ordinal=3',
                           b'V847_WIRELESS_RESULT ordinal=5'),
            before.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                           b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
            before + RESULT + b'\n',
        ):
            self.assertFalse(inspect(changed_sample(prefix=bad), 0)[1])
        self.assertFalse(inspect(wrapper_sample()+RESULT+b'\n', 0)[1])
        self.assertFalse(inspect(wrapper_sample((CHANGED_ENTRY, CHANGED_RESULT)), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(changed_sample(), rc, timeout)[1])

    def test_diagnostics_and_bounded_log(self):
        for event in (RESULT,
                      b'V861_WIRELESS_WRITE_INVALID kind=5 device=2 reason=3 witness=0 completed=3 bytes=8'):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' owner=private'))
        for args in ((b'x'*(8*1024*1024+1),0,False),
                     ('text',0,False), (changed_sample(),True,False),
                     (changed_sample(),0,1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
