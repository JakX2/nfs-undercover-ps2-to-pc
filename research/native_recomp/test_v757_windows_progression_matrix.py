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
from test_v762_windows_combined_callback import sample as combined_sample, getter as combined_getter, S as COMBINED_SUFFIX, I as COMBINED_INVALID
from test_v763_windows_handler_return import sample as handler_sample
from test_v922_windows_scheduler_entry import sample as scheduler_sample
from test_v923_windows_scheduler_return import sample as scheduler_return_sample
from test_v924_windows_reschedule_entry import sample as reschedule_sample
from test_v925_windows_reschedule_return import sample as reschedule_return_sample
from test_windows_native_rfi_audit_v926 import sample as native_rfi_sample
from windows_progression_matrix_v757 import (
    REQUIRED, OPTIONAL, DEEP_ONLY, STAGES, ProgressionFailure, stage_environment, full_image_environment, run, run_native_rfi,
)
from windows_full_build_v426 import build as windows_build,progression_contract,BuildError

FIXTURES = (transfer_sample(), suffix_sample(CALL), owner_log(),
            alarm_suffix_sample(), callback_sample(), time_sample(), frontier_sample(), wireless_sample(), write_sample(), combined_sample(), handler_sample(), scheduler_sample(), scheduler_return_sample(), reschedule_sample(), reschedule_return_sample())
EXIT = (0, 126, 0, 126, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
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
    def test_host_prepares_deep_flags_only_for_progression(self):
        from windows_transfer_prefix_v751 import plan
        standalone=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V922_SCHEDULER_ENTRY', standalone.env)
        self.assertNotIn('UNDERCOVER_V923_SCHEDULER_RETURN', standalone.env)
        self.assertNotIn('UNDERCOVER_V924_RESCHEDULE_ENTRY', standalone.env)
        self.assertNotIn('UNDERCOVER_V925_RESCHEDULE_RETURN', standalone.env)
        prepared=full_image_environment(standalone.env)
        self.assertEqual(prepared, BASE)
        self.assertEqual(len(prepared), len(standalone.env)+4)
        for stage in STAGES[:-4]:
            env=stage_environment(prepared,stage)
            self.assertNotIn('UNDERCOVER_V922_SCHEDULER_ENTRY',env)
            self.assertNotIn('UNDERCOVER_V923_SCHEDULER_RETURN',env)
            self.assertNotIn('UNDERCOVER_V924_RESCHEDULE_ENTRY',env)
            self.assertNotIn('UNDERCOVER_V925_RESCHEDULE_RETURN',env)
        for corrupted in ({}, {'UNDERCOVER_V922_SCHEDULER_ENTRY':'0'},
                          {'UNDERCOVER_V923_SCHEDULER_RETURN':'wrong'},
                          {'UNDERCOVER_V924_RESCHEDULE_ENTRY':'0'},
                          {'UNDERCOVER_V925_RESCHEDULE_RETURN':'wrong'}):
            candidate=dict(standalone.env)
            candidate.update(corrupted)
            if not corrupted: candidate.pop('UNDERCOVER_V920_HANDLER_RETURN')
            with self.assertRaises(ValueError):
                full_image_environment(candidate)

    def test_host_preflight_refuses_invalid_matrix_before_native_build(self):
        from windows_transfer_prefix_v751 import plan
        base=plan('os-si-handler-time',False,False,False,handler_return=True).env
        prepared=progression_contract(base)
        self.assertEqual(prepared,BASE)
        for key in base:
            faulty=dict(base);faulty.pop(key)
            with self.subTest(key=key),self.assertRaises(BuildError) as caught:
                progression_contract(faulty)
            self.assertEqual(str(caught.exception),'progression_environment')
        for change in ({'UNDERCOVER_V922_SCHEDULER_ENTRY':'true'},
                       {'UNDERCOVER_V925_RESCHEDULE_RETURN':'0'}):
            with self.assertRaises(BuildError) as caught:
                progression_contract({**base,**change})
            self.assertEqual(str(caught.exception),'progression_environment')

    def test_exact_stage_progression(self):
        self.assertEqual(tuple(s.name for s in STAGES),
                         ('transfer-return', 'transfer-suffix', 'alarm-return',
                          'alarm-suffix', 'callback-prefix', 'callback-time', 'callback-frontier', 'wireless-wrapper', 'wireless-write', 'combined-callback', 'handler-return', 'scheduler-entry', 'scheduler-return', 'reschedule-entry', 'reschedule-return'))
        self.assertEqual(tuple(len(s.enable) for s in STAGES), (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16))
        for i, stage in enumerate(STAGES):
            env = stage_environment(BASE, stage)
            self.assertEqual({key for key in OPTIONAL if key in env},
                             set(stage.enable))
            self.assertEqual(env[REQUIRED[0]], '1')
            self.assertEqual(env[REQUIRED[1]], '1')
            self.assertEqual(BASE, {key: '1' for key in REQUIRED})

    def test_full_progression_uses_one_executable(self):
        seen, output, failure = simulate()
        self.assertIsNone(failure)
        self.assertEqual(len(seen), 15)
        self.assertEqual(len({tuple(map(str, v[0])) for v in seen}), 1)
        self.assertTrue(all(v[1] == 20 for v in seen))
        self.assertEqual(sum(' verified=1 boot_verified=0' in row for row in output), 15)
        self.assertTrue(output[-1].startswith('V757_WINDOWS_PROGRESSION completed=15'))
        self.assertNotIn('main=1', '\n'.join(output))

    def test_early_callback_stop_never_completes_progression(self):
        # Both legitimate bounded stops remain available to the diagnostic
        # inspector, but cannot masquerade as an original ABI return.
        from windows_combined_callback_v762 import inspect, inspect_completed
        for earlier in (
            combined_sample(True, (COMBINED_SUFFIX, COMBINED_INVALID)),
            combined_sample(False, (COMBINED_SUFFIX, COMBINED_INVALID)),
            combined_getter(),
        ):
            with self.subTest(stop=earlier.splitlines()[-1]):
                _, observed = inspect(earlier, 0)
                self.assertTrue(observed)
                row, completed = inspect_completed(earlier, 0)
                self.assertFalse(completed)
                self.assertIn('callback_return=0 outer_dispatch=0', row)
                contents = list(FIXTURES)
                contents[9] = earlier
                seen, output, failure = simulate(contents=tuple(contents))
                self.assertEqual(len(seen), 10)
                self.assertEqual(failure, 'combined-callback')
                self.assertIn('callback_return=0 outer_dispatch=0',
                              '\\n'.join(output))
                self.assertFalse(any('completed=15' in r for r in output))

        for changed in (True, False):
            with self.subTest(returned=changed):
                row, completed = inspect_completed(combined_sample(changed), 0)
                self.assertTrue(completed, row)
                self.assertIn('callback_return=1 outer_dispatch=1', row)

    def test_first_failure_prevents_all_later_native_launches(self):
        for i in range(15):
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
        for i in range(15):
            codes = list(EXIT)
            codes[i] = 126 if EXIT[i] == 0 else 0
            seen, _, failure = simulate(codes=tuple(codes))
            self.assertEqual((len(seen), failure), (i + 1, STAGES[i].name))
            seen, _, failure = simulate(timeouts={i: True})
            self.assertEqual((len(seen), failure), (i + 1, STAGES[i].name))

    def test_missing_handler_return_fails_before_scheduler(self):
        contents = list(FIXTURES)
        contents[10] = combined_sample()
        seen, output, failure = simulate(contents=tuple(contents))
        self.assertEqual(len(seen), 11)
        self.assertEqual(failure, 'handler-return')
        self.assertTrue(any('handler_return=0' in r for r in output))
        self.assertFalse(any('completed=15' in r for r in output))

    def test_missing_scheduler_entry_fails_before_return(self):
        contents = list(FIXTURES)
        contents[11] = handler_sample()
        seen, output, failure = simulate(contents=tuple(contents))
        self.assertEqual(len(seen), 12)
        self.assertEqual(failure, 'scheduler-entry')
        self.assertTrue(any('scheduler_entry=0' in r for r in output))
        self.assertFalse(any('completed=15' in r for r in output))

    def test_missing_scheduler_return_fails_before_reschedule(self):
        contents = list(FIXTURES)
        contents[12] = scheduler_sample()
        seen, output, failure = simulate(contents=tuple(contents))
        self.assertEqual(len(seen), 13)
        self.assertEqual(failure, 'scheduler-return')
        self.assertTrue(any('scheduler_return=0' in r for r in output))
        self.assertFalse(any('completed=15' in r for r in output))

    def test_missing_reschedule_entry_fails_before_return(self):
        contents = list(FIXTURES)
        contents[13] = scheduler_return_sample()
        seen, output, failure = simulate(contents=tuple(contents))
        self.assertEqual(len(seen), 14)
        self.assertEqual(failure, 'reschedule-entry')
        self.assertTrue(any('reschedule_entry=0' in r for r in output))
        self.assertFalse(any('completed=15' in r for r in output))

    def test_missing_reschedule_return_fails_last_stage(self):
        contents = list(FIXTURES)
        contents[-1] = reschedule_sample()
        seen, output, failure = simulate(contents=tuple(contents))
        self.assertEqual(len(seen), 15)
        self.assertEqual(failure, 'reschedule-return')
        self.assertTrue(any('reschedule_return=0' in r for r in output))
        self.assertFalse(any('completed=15' in r for r in output))

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


    def test_native_rfi_reuses_matrix_image_without_early_capture(self):
        # RFI is an extra owner-original process after the existing 15
        # verified boundaries. It never substitutes for scheduler proof.
        called = []
        output = []

        def fake(args, log, seconds, *, env, cwd, timeout_status):
            i = len(called)
            called.append((tuple(args), dict(env), seconds))
            timeout_status['expired'] = False
            log.write_bytes(FIXTURES[i] if i < 15 else native_rfi_sample())
            return EXIT[i] if i < 15 else 0

        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            exe, dol, config = Path('original.exe'), Path('owner.dol'), Path('config.toml')
            run(exe, dol, config, folder, BASE, fake, output.append)
            run_native_rfi(exe, dol, config, folder, BASE, fake, output.append)
        self.assertEqual(len(called), 16)
        self.assertEqual(len({entry[0] for entry in called}), 1)
        self.assertTrue(all(entry[2] == 20 for entry in called))
        for _, env, _ in called[:15]:
            for key in ('UNDERCOVER_V751_CAPTURE', 'UNDERCOVER_V926_WINDOWS_RFI',
                        'UNDERCOVER_V932_PENDING_RFI'):
                self.assertNotIn(key, env)
        for key in ('UNDERCOVER_V751_CAPTURE', 'UNDERCOVER_V926_WINDOWS_RFI',
                    'UNDERCOVER_V932_PENDING_RFI'):
            self.assertEqual(called[-1][1][key], '1')
            self.assertNotIn(key, BASE)
        # The incremental scheduler-entry and nested-return observers need
        # scheduler_start(), which the authentic V926 route intentionally
        # replaces with v922::begin() at the original dispatcher return.
        # They must be present in their own matrix stages but absent in RFI.
        self.assertEqual(tuple(DEEP_ONLY), tuple(REQUIRED[-4:]))
        self.assertEqual({key for key in DEEP_ONLY if key in BASE},
                         set(DEEP_ONLY))
        for index, key in enumerate(DEEP_ONLY, start=11):
            self.assertEqual(called[index][1][key], '1')
            self.assertNotIn(key, called[-1][1])
        self.assertIn('stage=native-rfi verified=1 boot_verified=0', output[-1])
        self.assertTrue(any('native_rfi=1 second_vector=1' in x for x in output))

    def test_post_matrix_native_rfi_refuses_forgery_without_success(self):
        output = []

        def fake(args, log, seconds, *, env, cwd, timeout_status):
            timeout_status['expired'] = False
            log.write_bytes(native_rfi_sample().replace(
                b'V932_RFI_REENTRY restored_integer=1 native_rfi=1',
                b'V932_RFI_REENTRY restored_integer=0 native_rfi=1'))
            return 0

        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            with self.assertRaises(ProgressionFailure) as result:
                run_native_rfi(Path('native.exe'), Path('owner.dol'),
                               Path('config.toml'), folder, BASE, fake,
                               output.append)
            self.assertEqual(str(result.exception), 'native-rfi')
            self.assertIn('stage=native-rfi verified=0 boot_verified=0', output[-1])
            self.assertFalse(any('stage=native-rfi verified=1' in s for s in output))

    def test_post_matrix_native_rfi_environment_and_output_guards(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            args = (Path('native.exe'), Path('owner.dol'), Path('config.toml'),
                    folder)
            def unused(*a, **k):
                raise AssertionError('must fail before launching native code')
            for invalid in ({}, {**BASE, 'UNDERCOVER_V751_CAPTURE': '1'},
                            {**BASE, 'UNDERCOVER_V926_WINDOWS_RFI': '0'},
                            {**BASE, 'UNDERCOVER_V932_PENDING_RFI': '1'}):
                with self.assertRaises(ValueError):
                    run_native_rfi(*args, invalid, unused)
            (folder/'progression-native-rfi.log').write_bytes(b'protected')
            with self.assertRaises(ProgressionFailure):
                run_native_rfi(*args, BASE, unused)

    def test_windows_ci_replaces_stale_pushes_but_preserves_manual_rfi(self):
        # The owner-private build is lengthy. New source commits must reach
        # native execution without waiting for obsolete branch jobs.
        # Manual native-RFI investigations should not be cancelled by pushes.
        workflow = (Path(__file__).resolve().parents[2] /
                    '.github/workflows/wii-windows-si-continuous.yml'
                    ).read_text(encoding='utf-8')
        self.assertRegex(
            workflow,
            r"(?m)^concurrency:\n"
            r"  # Replace stale push builds so the latest owner-original code is tested\.\n"
            r"  # Preserve separately dispatched RFI experiments across ordinary pushes\.\n"
            r"  group: wii-windows-continuous-si-\$\{\{ github\.ref \}\}-\$\{\{ github\.event_name \}\}\n"
            r"  cancel-in-progress: \$\{\{ github\.event_name == 'push' \}\}\n"
        )
        self.assertIn('if: always()', workflow)
        self.assertIn('--owner-progression-matrix', workflow)
        self.assertIn('--owner-native-rfi', workflow)

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
