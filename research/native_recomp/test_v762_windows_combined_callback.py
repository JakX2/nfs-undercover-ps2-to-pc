#!/usr/bin/env python3
"""Windows private original V861+V850 combined callback return controls."""
import inspect as std_inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v761_windows_wireless_write import changed_sample
from test_v760_windows_wireless_wrapper import sample as wrapper_sample
from test_v852_callback_return import S, B, T, I
from windows_transfer_prefix_v751 import plan
from windows_combined_callback_v762 import inspect, diagnostic
from windows_full_build_v426 import build as windows_build


def sample(changed=True, tail=(S, B, T)):
    before = changed_sample() if changed else wrapper_sample()
    return before.rstrip(b'\r\n') + b'\n' + b'\n'.join(tail) + b'\n'


def getter():
    before = wrapper_sample()
    before = before.replace(b'V831_CALLBACK_FRONTIER_RESULT ordinal=3',
                            b'V831_CALLBACK_FRONTIER_RESULT ordinal=5')
    before = before.replace(b'zero_id=1 follow=3', b'zero_id=0 follow=3')
    before = before.replace(b'V847_WIRELESS_ENTRY frontier=1 ordinal=3',
                            b'V847_WIRELESS_ENTRY frontier=1 ordinal=5')
    before = before.replace(b'V847_WIRELESS_RESULT ordinal=3',
                            b'V847_WIRELESS_RESULT ordinal=5')
    return before


class WindowsCombinedCallback(unittest.TestCase):
    def test_owner_plan_exact_native_composition(self):
        p = plan('os-si-handler-time', False, False, False,
                 combined_callback=True)
        self.assertEqual(p.analyzer,
                         ('--transfer-prefix', '--transfer-return', '--alarm',
                          '--callback-prefix'))
        self.assertEqual(p.observers[-3:],
                         (('wireless_wrapper_observer',
                           'prepare_v847_wireless_wrapper.py'),
                          ('wireless_write_observer',
                           'prepare_v861_wireless_write.py'),
                          ('combined_callback_observer',
                           'prepare_v863_combined_callback.py')))
        self.assertEqual(p.env['UNDERCOVER_V850_CALLBACK_RETURN'], '1')
        self.assertEqual(p.env['UNDERCOVER_V861_WIRELESS_WRITE'], '1')
        for args in (
            {'scope': 'startup'}, {'synthetic': True}, {'prefix': True},
            {'time_suffix': True}, {'returned': True}, {'suffix': True},
            {'alarm': True}, {'alarm_suffix': True},
            {'callback_prefix': True}, {'callback_time': True},
            {'callback_frontier': True}, {'wireless_wrapper': True},
            {'wireless_write': True},
        ):
            settings = dict(scope='os-si-handler-time', synthetic=False,
                            prefix=False, time_suffix=False, combined_callback=True)
            settings.update(args)
            with self.subTest(settings=args), self.assertRaises(ValueError):
                plan(**settings)

    def test_owner_cli_guards(self):
        self.assertIn('owner_combined_callback', std_inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        p = subprocess.run([sys.executable, str(runner), '--help'],
                           text=True, capture_output=True, check=True)
        self.assertIn('--owner-combined-callback', p.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td)
                for extra in ([], ['--owner-progression-matrix'],
                              ['--owner-wireless-write'],
                              ['--owner-wireless-wrapper']):
                    result = subprocess.run(
                        [sys.executable, str(runner), str(folder/'no-upstream'),
                         str(folder/'fresh'), '--owner-scope', 'os-si-handler-time',
                         '--owner-combined-callback', *extra],
                        text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=combined_callback_scope',
                                  result.stdout)

    def test_owner_cli_requires_original_callback_return(self):
        # The standalone Windows owner flag must use the same fail-closed
        # completion policy as the single-build progression matrix.
        from windows_full_build_v426 import inspect_combined_callback as cli_audit
        from windows_combined_callback_v762 import inspect_completed
        self.assertIs(cli_audit, inspect_completed)

        for early in (sample(True, (S, I)), sample(False, (S, I)), getter()):
            with self.subTest(stop=early.splitlines()[-1]):
                row, ok = cli_audit(early, 0)
                self.assertFalse(ok, row)
                self.assertIn('callback_return=0 outer_dispatch=0', row)

        for changed in (True, False):
            with self.subTest(changed=changed):
                row, ok = cli_audit(sample(changed), 0)
                self.assertTrue(ok, row)
                self.assertIn('callback_return=1 outer_dispatch=1', row)

    def test_changed_and_unchanged_original_callback_return(self):
        for changed in (True, False):
            with self.subTest(changed=changed):
                row, ok = inspect(sample(changed), 0)
                self.assertTrue(ok, row)
                self.assertIn('continuation_verified=1', row)
                self.assertIn('callback_return=1 outer_dispatch=1', row)
                self.assertIn('handler_return=0 rfi=0 boot_verified=0', row)

    def test_unadmitted_suffix_and_getter_avoid_false_return(self):
        for changed in (True, False):
            row, ok = inspect(sample(changed, (S, I)), 0)
            self.assertTrue(ok, row)
            self.assertIn('suffix_boundary=4', row)
            self.assertIn('callback_return=0 outer_dispatch=0', row)
        row, ok = inspect(getter(), 0)
        self.assertTrue(ok, row)
        self.assertIn('wireless_ordinal=5', row)
        self.assertIn('callback_return=0 outer_dispatch=0', row)

    def test_reject_invalid_abi_tail(self):
        for tail in ((), (S,), (S, B), (S, T, B), (S, B, T, T),
                     (S, B, T, b'extra'), (S, b'extra', B, T),
                     (S, B.replace(b'ordinal=13', b'ordinal=4'), T),
                     (S, B.replace(b'visits=37', b'visits=129'), T),
                     (S, B, T.replace(b'callback_return=1', b'callback_return=0')),
                     (S, B, T.replace(b'outer_dispatch=1', b'outer_dispatch=0')),
                     (S, B, T.replace(b'abi=1', b'abi=0')),
                     (S, B, T.replace(b'boot_verified=0', b'boot_verified=1')),
                     (S, B, b'V850_CALLBACK_RETURN_INVALID kind=7 suffix_stage=2 suffix_reason=0 return_stage=4 return_reason=6 device=0')):
            with self.subTest(tail=tail):
                self.assertFalse(inspect(sample(True, tail), 0)[1])

    def test_no_predecessor_substitution_or_timeout(self):
        raw = sample(True)
        for before in (
            raw.replace(b'V861_WIRELESS_WRITE_RESULT original_setter_return=1',
                        b'V861_WIRELESS_WRITE_RESULT original_setter_return=0'),
            raw.replace(b'V847_WIRELESS_RESULT ordinal=3',
                        b'V847_WIRELESS_RESULT ordinal=5'),
            raw.replace(b'V777_TRANSFER_HANDOFF scheduler_tick=1',
                        b'V777_TRANSFER_HANDOFF scheduler_tick=0'),
            raw.replace(b'V850_CALLBACK_SUFFIX_ENTRY setter_return=1',
                        b'V850_CALLBACK_SUFFIX_ENTRY setter_return=0'),
        ):
            self.assertFalse(inspect(before, 0)[1])
        for rc, timeout in ((126, False), (1, False), (0, True),
                            (0xC0000005, False), (-1073741819, False)):
            self.assertFalse(inspect(raw, rc, timeout)[1])

    def test_diagnostics_and_bounded_log(self):
        for event in (S, B, T, I,
                      b'V850_CALLBACK_RETURN_INVALID kind=7 suffix_stage=2 suffix_reason=0 return_stage=4 return_reason=6 device=0'):
            self.assertTrue(diagnostic(event))
            self.assertFalse(diagnostic(event+b' owner=private'))
        for args in ((b'x'*(8*1024*1024+1),0,False),
                     ('text',0,False), (sample(),True,False),
                     (sample(),0,1)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__ == '__main__':
    unittest.main()
