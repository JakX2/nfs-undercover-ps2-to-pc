#!/usr/bin/env python3
"""Source-only Windows original callback time return gate."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v756_windows_callback_prefix import sample as prefix_sample
from windows_transfer_prefix_v751 import plan
from windows_callback_time_v758 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build

ENTRY = b'V813_CALLBACK_TIME_ENTRY prefix=1 follow=3'
RESULT = (
    b'V813_CALLBACK_TIME_RESULT original_return=1 abi=1 leaves=3 '
    b'system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 follow=3 '
    b'continuation_executed=0 callback_return=0 boot_verified=0'
)


def sample(tail=(ENTRY, RESULT), prefix=None):
    before = prefix_sample() if prefix is None else prefix
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


class WindowsCallbackTime(unittest.TestCase):
    def test_exact_owner_plan(self):
        p = plan('os-si-handler-time', False, False, False,
                 callback_time=True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers[-2:],
                         (('callback_prefix_observer',
                           'prepare_v807_callback_prefix.py'),
                          ('callback_time_observer',
                           'prepare_v813_callback_time.py')))
        self.assertEqual(p.env['UNDERCOVER_V807_CALLBACK_PREFIX'], '1')
        self.assertEqual(p.env['UNDERCOVER_V813_CALLBACK_TIME'], '1')
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
        ):
            settings = dict(scope='os-si-handler-time', synthetic=False,
                            prefix=False, time_suffix=False, callback_time=True)
            settings.update(args)
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(**settings)

    def test_owner_cli_gating(self):
        self.assertIn('owner_callback_time', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        p = subprocess.run([sys.executable, str(runner), '--help'],
                           text=True, capture_output=True, check=True)
        self.assertIn('--owner-callback-time', p.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as d:
                w = Path(d)
                for extra in ([], ['--owner-progression-matrix'],
                              ['--owner-callback-prefix']):
                    result = subprocess.run(
                        [sys.executable, str(runner), str(w/'missing'),
                         str(w/'work'), '--owner-scope', 'os-si-handler-time',
                         '--owner-callback-time', *extra],
                        text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    # Invalid combinations must not reach private inputs.
                    self.assertIn('reason=callback_time_scope', result.stdout)

    def test_original_time_return(self):
        row, ok = inspect(sample(), 0)
        self.assertTrue(ok, row)
        self.assertIn('callback_prefix_verified=1 time_return_verified=1', row)
        self.assertIn('ordinal=6 leaf_visits=18 polls=1 reads=3', row)
        self.assertIn('callback_return=0 handler_return=0 boot_verified=0', row)
        for polls in (2, 4, 12):
            result = RESULT.replace(b'leaf_visits=18',
                                    f'leaf_visits={18+5*(polls-1)}'.encode())
            result = result.replace(b'polls=1', f'polls={polls}'.encode())
            result = result.replace(b'reads=3', f'reads={3*polls}'.encode())
            self.assertTrue(inspect(sample((ENTRY, result)), 0)[1])

    def test_exact_tail_and_private_refusal(self):
        for bad in ((ENTRY,), (RESULT, ENTRY), (ENTRY, RESULT, RESULT),
                    (ENTRY, RESULT, b'extra'), (ENTRY, b'extra', RESULT),
                    (b'extra', ENTRY, RESULT),
                    (ENTRY, RESULT.replace(b'original_return=1', b'original_return=0')),
                    (ENTRY, RESULT.replace(b'offset=1', b'offset=0')),
                    (ENTRY, RESULT.replace(b'polls=1', b'polls=2')),
                    (ENTRY, RESULT.replace(b'reads=3', b'reads=4')),
                    (ENTRY, RESULT.replace(b'follow=3', b'follow=2')),
                    (ENTRY, RESULT.replace(b'leaves=3', b'leaves=2')),
                    (ENTRY, RESULT.replace(b'callback_return=0', b'callback_return=1')),
                    (ENTRY, RESULT.replace(b'boot_verified=0', b'boot_verified=1')),
                    (ENTRY, b'V813_CALLBACK_TIME_INVALID kind=4 stage=4 witness=3 device=0 visits=24 cursor=1', RESULT)):
            with self.subTest(tail=bad):
                self.assertFalse(inspect(sample(bad), 0)[1])
        for line in (ENTRY, RESULT,
                     b'V813_CALLBACK_TIME_INVALID kind=4 stage=4 witness=3 device=0 visits=24 cursor=1'):
            self.assertTrue(diagnostic(line))
            self.assertFalse(diagnostic(line+b' secret=123'))

    def test_no_predecessor_substitution_or_timeout(self):
        before = prefix_sample()
        for bad in (before.replace(b'V807_CALLBACK_RESULT original_prologue=1',
                                   b'V807_CALLBACK_RESULT original_prologue=0'),
                    before + ENTRY + b'\n',
                    before + b'V813_CALLBACK_TIME_INVALID kind=1 stage=0 witness=1 device=0 visits=0 cursor=0\n',
                    before.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                                   b'V777_TRANSFER_HANDOFF scheduler_tick=0')):
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
