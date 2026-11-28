#!/usr/bin/env python3
"""Source-only Windows original callback wireless-dispatch stop."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v758_windows_callback_time import sample as time_sample
from windows_transfer_prefix_v751 import plan
from windows_callback_frontier_v759 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

ENTRY = b'V831_CALLBACK_FRONTIER_ENTRY original_time_return=1 follow=3'
RESULT = (
    b'V831_CALLBACK_FRONTIER_RESULT ordinal=3 visits=27 writes=1 zero_id=1 '
    b'follow=3 store_bytes=1 wireless_executed=0 callback_return=0 boot_verified=0'
)


def sample(tail=(ENTRY, RESULT), prefix=None):
    before = time_sample() if prefix is None else prefix
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


class WindowsCallbackFrontier(unittest.TestCase):
    def test_exact_owner_plan(self):
        p = plan('os-si-handler-time', False, False, False,
                 callback_frontier=True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers[-3:],
                         (('callback_prefix_observer',
                           'prepare_v807_callback_prefix.py'),
                          ('callback_time_observer',
                           'prepare_v813_callback_time.py'),
                          ('callback_frontier_observer',
                           'prepare_v831_callback_frontier.py')))
        self.assertEqual(p.env['UNDERCOVER_V807_CALLBACK_PREFIX'], '1')
        self.assertEqual(p.env['UNDERCOVER_V813_CALLBACK_TIME'], '1')
        self.assertEqual(p.env['UNDERCOVER_V831_CALLBACK_FRONTIER'], '1')
        for args in (
            {'scope': 'startup'},
            {'synthetic': True},
            {'prefix': True},
            {'time_suffix': True},
            {'returned': True},
            {'suffix': True},
            {'alarm': True},
            {'alarm_suffix': True},
            {'callback_prefix': True},
            {'callback_time': True},
        ):
            settings = dict(scope='os-si-handler-time', synthetic=False,
                            prefix=False, time_suffix=False, callback_frontier=True)
            settings.update(args)
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(**settings)

    def test_owner_cli_gating(self):
        self.assertIn('owner_callback_frontier', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        p = subprocess.run([sys.executable, str(runner), '--help'],
                           text=True, capture_output=True, check=True)
        self.assertIn('--owner-callback-frontier', p.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as d:
                w = Path(d)
                for extra in ([], ['--owner-progression-matrix'],
                              ['--owner-callback-time'],
                              ['--owner-callback-prefix']):
                    result = subprocess.run(
                        [sys.executable, str(runner), str(w/'missing'),
                         str(w/'work'), '--owner-scope', 'os-si-handler-time',
                         '--owner-callback-frontier', *extra],
                        text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('reason=callback_frontier_scope', result.stdout)

    def test_original_frontier(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('time_return_verified=1 frontier_verified=1', row)
        self.assertIn('wireless_ordinal=3 visits=27 writes=1 zero_id=1', row)
        self.assertIn('wireless_executed=0 callback_return=0 handler_return=0', row)
        other = RESULT.replace(b'ordinal=3', b'ordinal=5').replace(b'zero_id=1', b'zero_id=0')
        self.assertTrue(inspect(sample((ENTRY, other)), 0)[1])

    def test_exact_tail_and_private_refusal(self):
        for bad in ((ENTRY,), (RESULT, ENTRY), (ENTRY, RESULT, RESULT),
                    (ENTRY, RESULT, b'extra'), (ENTRY, b'extra', RESULT),
                    (b'extra', ENTRY, RESULT),
                    (ENTRY, RESULT.replace(b'ordinal=3', b'ordinal=4')),
                    (ENTRY, RESULT.replace(b'visits=27', b'visits=0')),
                    (ENTRY, RESULT.replace(b'writes=1', b'writes=99')),
                    (ENTRY, RESULT.replace(b'follow=3', b'follow=2')),
                    (ENTRY, RESULT.replace(b'store_bytes=1', b'store_bytes=0')),
                    (ENTRY, RESULT.replace(b'wireless_executed=0', b'wireless_executed=1')),
                    (ENTRY, RESULT.replace(b'callback_return=0', b'callback_return=1')),
                    (ENTRY, RESULT.replace(b'boot_verified=0', b'boot_verified=1')),
                    (ENTRY, b'V831_CALLBACK_FRONTIER_INVALID kind=3 stage=1 witness=1 device=0 visits=24 writes=1', RESULT)):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(sample(bad), 0)[1])
        for line in (ENTRY, RESULT,
                     b'V831_CALLBACK_FRONTIER_INVALID kind=3 stage=1 witness=1 device=0 visits=24 writes=1'):
            self.assertTrue(diagnostic(line))
            self.assertFalse(diagnostic(line+b' secret=123'))

    def test_no_predecessor_substitution_or_timeout(self):
        before = time_sample()
        for bad in (
            before.replace(b'V813_CALLBACK_TIME_RESULT original_return=1',
                           b'V813_CALLBACK_TIME_RESULT original_return=0'),
            before + ENTRY + b'\n',
            before + b'V831_CALLBACK_FRONTIER_INVALID kind=1 stage=0 witness=1 device=0 visits=0 writes=0\n',
            before.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                           b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
        ):
            self.assertFalse(inspect(sample(prefix=bad), 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(sample(), rc, timeout)[1])

    def test_type_and_size_fail_closed(self):
        for args in ((b'x'*(8*1024*1024+1),0,False),
                     ('text',0,False), (sample(),True,False),
                     (sample(),0,1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
