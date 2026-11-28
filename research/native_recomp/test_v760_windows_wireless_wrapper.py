#!/usr/bin/env python3
"""Original-free Windows wrapper continuation and EXI-lock stop controls."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v759_windows_callback_frontier import sample as frontier_sample
from windows_transfer_prefix_v751 import plan
from windows_wireless_wrapper_v760 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

ENTRY = b'V847_WIRELESS_ENTRY frontier=1 ordinal=3 changed=0'
RESULT = (
    b'V847_WIRELESS_RESULT ordinal=3 changed=0 visits=62 writes=12 '
    b'returned=1 lock_entry=0 exi_executed=0 callback_return=0 boot_verified=0'
)
CHANGED_ENTRY = ENTRY.replace(b'changed=0', b'changed=1')
CHANGED_RESULT = (RESULT.replace(b'changed=0', b'changed=1')
                  .replace(b'returned=1 lock_entry=0',
                           b'returned=0 lock_entry=1'))


def sample(tail=(ENTRY, RESULT), prefix=None):
    before = frontier_sample() if prefix is None else prefix
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


class WindowsWirelessWrapper(unittest.TestCase):
    def test_exact_native_owner_plan(self):
        p = plan('os-si-handler-time', False, False, False,
                 wireless_wrapper=True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers[-4:],
                         (('callback_prefix_observer',
                           'prepare_v807_callback_prefix.py'),
                          ('callback_time_observer',
                           'prepare_v813_callback_time.py'),
                          ('callback_frontier_observer',
                           'prepare_v831_callback_frontier.py'),
                          ('wireless_wrapper_observer',
                           'prepare_v847_wireless_wrapper.py')))
        self.assertEqual(p.env['UNDERCOVER_V807_CALLBACK_PREFIX'], '1')
        self.assertEqual(p.env['UNDERCOVER_V813_CALLBACK_TIME'], '1')
        self.assertEqual(p.env['UNDERCOVER_V831_CALLBACK_FRONTIER'], '1')
        self.assertEqual(p.env['UNDERCOVER_V847_WIRELESS'], '1')
        for args in (
            {'scope': 'startup'}, {'synthetic': True}, {'prefix': True},
            {'time_suffix': True}, {'returned': True}, {'suffix': True},
            {'alarm': True}, {'alarm_suffix': True},
            {'callback_prefix': True}, {'callback_time': True},
            {'callback_frontier': True},
        ):
            settings = dict(scope='os-si-handler-time', synthetic=False,
                            prefix=False, time_suffix=False, wireless_wrapper=True)
            settings.update(args)
            with self.subTest(settings=args), self.assertRaises(ValueError):
                plan(**settings)

    def test_cli_and_synthetic_refusal(self):
        self.assertIn('owner_wireless_wrapper', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        help_result = subprocess.run([sys.executable, str(runner), '--help'],
                                     capture_output=True, text=True, check=True)
        self.assertIn('--owner-wireless-wrapper', help_result.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td)
                for extra in ([], ['--owner-progression-matrix'],
                              ['--owner-callback-frontier'],
                              ['--owner-callback-prefix']):
                    p = subprocess.run(
                        [sys.executable, str(runner),
                         str(folder/'missing-upstream'), str(folder/'new-work'),
                         '--owner-scope', 'os-si-handler-time',
                         '--owner-wireless-wrapper', *extra],
                        capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=wireless_wrapper_scope',
                                  p.stdout)

    def test_original_return_and_changed_exi_lock(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('frontier_verified=1 wrapper_verified=1', row)
        self.assertIn('original_return=1 exilock_entry=0 exi_executed=0', row)
        row, ok = inspect(sample((CHANGED_ENTRY, CHANGED_RESULT)), 0)
        self.assertTrue(ok, row)
        self.assertIn('changed=1', row)
        self.assertIn('original_return=0 exilock_entry=1', row)

    def test_bad_tail_order_and_geometry(self):
        for bad in ((ENTRY,), (RESULT, ENTRY), (ENTRY, RESULT, RESULT),
                    (ENTRY, RESULT, b'extra'), (ENTRY, b'extra', RESULT),
                    (b'extra', ENTRY, RESULT),
                    (ENTRY, RESULT.replace(b'visits=62', b'visits=321')),
                    (ENTRY, RESULT.replace(b'writes=12', b'writes=65')),
                    (ENTRY, RESULT.replace(b'ordinal=3', b'ordinal=5')),
                    (ENTRY, RESULT.replace(b'returned=1', b'returned=0')),
                    (ENTRY, RESULT.replace(b'lock_entry=0', b'lock_entry=1')),
                    (ENTRY, RESULT.replace(b'exi_executed=0', b'exi_executed=1')),
                    (ENTRY, RESULT.replace(b'callback_return=0', b'callback_return=1')),
                    (ENTRY, RESULT.replace(b'boot_verified=0', b'boot_verified=1')),
                    (ENTRY, b'V847_WIRELESS_INVALID kind=4 stage=1 witness=1 device=0 visits=23 writes=1', RESULT),
                    (CHANGED_ENTRY, RESULT),
                    (ENTRY, CHANGED_RESULT)):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(sample(bad), 0)[1])

    def test_predecessor_and_exit_rejection(self):
        before = frontier_sample()
        for bad in (
            before.replace(b'V831_CALLBACK_FRONTIER_RESULT ordinal=3',
                           b'V831_CALLBACK_FRONTIER_RESULT ordinal=4'),
            before.replace(b'V813_CALLBACK_TIME_RESULT original_return=1',
                           b'V813_CALLBACK_TIME_RESULT original_return=0'),
            before + ENTRY + b'\n',
            before.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                           b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
        ):
            self.assertFalse(inspect(sample(prefix=bad), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])

    def test_diagnostics_and_type_refusal(self):
        for event in (ENTRY, RESULT, CHANGED_ENTRY, CHANGED_RESULT,
                      b'V847_WIRELESS_INVALID kind=4 stage=1 witness=1 device=0 visits=23 writes=1'):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event + b' owner=private'))
        for args in ((b'x'*(8*1024*1024+1),0,False),
                     ('text',0,False), (sample(),True,False),
                     (sample(),0,1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
