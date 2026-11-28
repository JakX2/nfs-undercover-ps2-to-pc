#!/usr/bin/env python3
"""Original-free Windows same-full-image SI progression and stop controls."""
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v752_windows_transfer_return import sample as transfer_sample
from test_v753_windows_transfer_suffix import log as suffix_sample, CALL
from test_v754_windows_alarm_return import owner_log
from test_v755_windows_alarm_suffix import sample as alarm_suffix_sample
from test_v756_windows_callback_prefix import sample as callback_sample
from test_v758_windows_callback_time import sample as time_sample
from test_v759_windows_callback_frontier import sample as frontier_sample
from test_v760_windows_wireless_wrapper import sample as wireless_sample
from test_v761_windows_wireless_write import changed_sample as write_sample
from windows_progression_matrix_v757 import (
    REQUIRED, OPTIONAL, STAGES, ProgressionFailure, stage_environment, run,
)
from windows_full_build_v426 import build as windows_build

FIXTURES = (transfer_sample(), suffix_sample(CALL), owner_log(),
            alarm_suffix_sample(), callback_sample(), time_sample(), frontier_sample(), wireless_sample(), write_sample())
EXIT = (0, 126, 0, 126, 0, 0, 0, 0, 0)
BASE = {key: '1' for key in REQUIRED}


def simulate(contents=FIXTURES, codes=EXIT, timeouts=None):
    """One fake native process per stage. Injected only in original-free tests."""
    seen = []
    writes = []

    def fake(args, log, seconds, *, env, cwd, timeout_status):
        i = len(seen)
        seen.append((args, seconds, dict(env)))
        timeout_status['expired'] = (timeouts or {}).get(i, False)
        log.write_bytes(contents[i])
        return codes[i]

    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        try:
            run(Path('private.exe'), Path('original.dol'), Path('settings.toml'),
                folder, BASE, fake, writes.append)
            failure = None
        except ProgressionFailure as e:
            failure = str(e)
    return seen, writes, failure


class WindowsProgression(unittest.TestCase):
    def test_exact_five_service_boundaries(self):
        self.assertEqual(tuple(s.name for s in STAGES),
                         ('transfer-return', 'transfer-suffix', 'alarm-return',
                          'alarm-suffix', 'callback-prefix', 'callback-time', 'callback-frontier', 'wireless-wrapper', 'wireless-write'))
        self.assertEqual(tuple(len(s.enable) for s in STAGES), (0, 1, 2, 3, 4, 5, 6, 7, 8))
        for i, stage in enumerate(STAGES):
            env = stage_environment(BASE, stage)
            self.assertEqual({key for key in OPTIONAL if key in env},
                             set(OPTIONAL[:i]))
            self.assertEqual(env[REQUIRED[0]], '1')
            self.assertEqual(env[REQUIRED[1]], '1')
            self.assertEqual(BASE, {key: '1' for key in REQUIRED})

    def test_full_progression_uses_one_executable(self):
        seen, output, failure = simulate()
        self.assertIsNone(failure)
        self.assertEqual(len(seen), 9)
        self.assertEqual(len({tuple(map(str, v[0])) for v in seen}), 1)
        self.assertTrue(all(v[1] == 20 for v in seen))
        self.assertEqual(sum(' verified=1 boot_verified=0' in row for row in output), 9)
        self.assertTrue(output[-1].startswith('V757_WINDOWS_PROGRESSION completed=9'))
        self.assertNotIn('main=1', '\n'.join(output))

    def test_first_failure_prevents_all_later_native_launches(self):
        for i in range(9):
            contents = list(FIXTURES)
            contents[i] = contents[i] + b'unexpected opaque private bytes\n'
            with self.subTest(stage=i):
                seen, output, failure = simulate(tuple(contents))
                self.assertEqual(failure, STAGES[i].name)
                self.assertEqual(len(seen), i + 1)
                self.assertTrue(output[-1].startswith('V757_WINDOWS_PROGRESSION stage='))
                self.assertNotIn('unexpected opaque private bytes', '\n'.join(output))
                self.assertFalse(any('completed=5' in r for r in output))

    def test_refuse_errors_and_timeout(self):
        for i in range(9):
            codes = list(EXIT)
            codes[i] = 126 if EXIT[i] == 0 else 0
            seen, _, failure = simulate(codes=tuple(codes))
            self.assertEqual((len(seen), failure), (i + 1, STAGES[i].name))
            seen, _, failure = simulate(timeouts={i: True})
            self.assertEqual((len(seen), failure), (i + 1, STAGES[i].name))

    def test_reject_stale_environment(self):
        for key in REQUIRED:
            for replacement in (None, '', '0', 'true'):
                e = dict(BASE)
                if replacement is None:
                    e.pop(key)
                else:
                    e[key] = replacement
                with self.subTest(key=key, replacement=replacement):
                    with self.assertRaises(ValueError):
                        stage_environment(e, STAGES[-1])
        for bad in (object(), True, None, STAGES[-1].name):
            with self.assertRaises(ValueError):
                stage_environment(BASE, bad)

    def test_reject_preexisting_output_and_bad_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            (folder/'progression-transfer-return.log').write_bytes(b'protected')
            with self.assertRaises(ProgressionFailure):
                run(Path('x'), Path('y'), Path('z'), folder, BASE,
                    lambda *_args, **_kwargs: 0, lambda s: None)
            with self.assertRaises(ValueError):
                run('exe', Path('y'), Path('z'), folder, BASE,
                    lambda *_args, **_kwargs: 0, lambda s: None)
            with self.assertRaises(ValueError):
                run(Path('x'), Path('y'), Path('z'), folder, BASE,
                    None, lambda s: None)

    def test_options_are_opt_in_and_mutually_exclusive(self):
        self.assertIn('owner_progression_matrix', inspect.signature(windows_build).parameters)
        runner = Path(__file__).with_name('windows_full_build_v426.py')
        p = subprocess.run([sys.executable, str(runner), '--help'],
                           capture_output=True, text=True, check=True)
        self.assertIn('--owner-progression-matrix', p.stdout)
        if os.name == 'nt':
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td)
                for extra in ([], ['--owner-transfer-return'],
                              ['--owner-callback-prefix']):
                    p = subprocess.run(
                        [sys.executable, str(runner), str(folder/'no-upstream'),
                         str(folder/'fresh'), '--owner-scope', 'os-si-handler-time',
                         '--owner-progression-matrix', *extra],
                        capture_output=True, text=True, check=False)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('V426_WINDOWS_FAILED reason=progression_scope',
                                  p.stdout)


if __name__ == '__main__':
    unittest.main()
