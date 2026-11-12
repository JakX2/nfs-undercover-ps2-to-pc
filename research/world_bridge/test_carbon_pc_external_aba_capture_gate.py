"""Synthetic-only A/B/A Carbon external-resource ProcMon capture regressions.

No owner game binaries, files, ASI loader, processes or copyrighted assets.
"""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from carbon_pc_external_aba_capture_gate import (
    _capture_probe, audit_carbon_external_aba, audit_owner_aba_files,
)
from test_carbon_pc_external_resource_read_gate import csv_log, row
from test_carbon_pc_original_loader_control_chain import (
    WINDOWS_FILE, WINDOWS_GAME, MANIFEST, SOURCE,
)
from test_texture_visual_pair_gate import make_pack

SENTINEL = WINDOWS_GAME + r'\TRACKS\STREAML5RB.BUN'


def observed_stock(pid='555'):
    return [
        row('CreateFile', pid=pid, path=SENTINEL),
        row('ReadFile', pid=pid, path=SENTINEL,
            detail='Offset: 0, Length: 32, I/O Flags: Cached'),
    ]


def observed_external(pid='555', source=SOURCE, op='ReadFile'):
    return [
        row('CreateFile', pid=pid, path=WINDOWS_FILE),
        row(op, pid=pid, path=WINDOWS_FILE,
            detail=f'Offset: 0, Length: {len(source)}, I/O Flags: Cached'),
    ]


def baseline():
    return csv_log(*observed_stock('1001'))


def controlled(source=SOURCE):
    return csv_log(*(observed_stock('1002') +
                     observed_external('1002', source)))


def restored():
    return csv_log(*observed_stock('1003'))


def audit(base=None, control=None, restore=None, source=SOURCE,
          sentinel=SENTINEL, resource=WINDOWS_FILE):
    return audit_carbon_external_aba(
        MANIFEST, source,
        baseline() if base is None else base,
        controlled(source) if control is None else control,
        restored() if restore is None else restore,
        WINDOWS_GAME, resource, sentinel, 'geometry')


class CapturedComparisonTests(unittest.TestCase):
    def test_full_isolated_original_free_control(self):
        report = audit()
        self.assertEqual(report['evidence_level'],
                         'ISOLATED_EXTERNAL_FILE_READ_OBSERVED_NOT_REGISTRATION')
        self.assertTrue(report['all_captures_calibrated'])
        self.assertTrue(report['external_access_isolated_to_control_capture'])
        self.assertTrue(report['control_external_and_sentinel_same_pid'])
        self.assertTrue(report['control_full_external_file_read_observed'])
        self.assertEqual(report['control_external_file_bytes_covered'], len(SOURCE))
        self.assertTrue(report['original_source_native_pc_chunk_framing_valid'])
        self.assertTrue(report['manifest_matches_exact_control_file'])
        self.assertEqual(report['original_file_bytes'], len(SOURCE))
        self.assertFalse(report['carbon_engine_resource_registration_verified'])
        self.assertFalse(report['carbon_asi_loaded_verified'])
        self.assertFalse(report['owner_run_order_or_loader_toggle_verified'])

    def test_composite_control_source_full_file_not_first_root(self):
        additional = make_pack('pc', hashes=(0x12345678,))
        unknown = struct.pack('<II', 0x12340001, 4) + b'abcd'
        whole = unknown + SOURCE + additional
        report = audit(source=whole)
        self.assertEqual(report['original_file_bytes'], len(whole))
        self.assertEqual(report['control_external_file_bytes_covered'], len(whole))
        self.assertTrue(report['control_full_external_file_read_observed'])

    def test_no_baseline_calibration_is_inconclusive(self):
        report = audit(base=csv_log())
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_CAPTURE_CALIBRATION_MISSING')
        self.assertFalse(report['baseline_calibrated'])
        self.assertFalse(report['all_captures_calibrated'])

    def test_no_control_calibration_is_inconclusive_even_with_external_read(self):
        report = audit(control=csv_log(*observed_external('2001')))
        self.assertFalse(report['control_calibrated'])
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_CAPTURE_CALIBRATION_MISSING')

    def test_no_restore_calibration_is_inconclusive(self):
        report = audit(restore=csv_log())
        self.assertFalse(report['restore_calibrated'])
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_CAPTURE_CALIBRATION_MISSING')

    def test_baseline_external_positive_access_is_not_isolated(self):
        before = csv_log(*(observed_stock('1001') +
                           observed_external('1001')))
        report = audit(base=before)
        self.assertFalse(report['external_access_isolated_to_control_capture'])
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_EXTERNAL_TARGET_NOT_ISOLATED_TO_CONTROL')

    def test_restore_external_positive_access_is_not_isolated(self):
        after = csv_log(*(observed_stock('1003') +
                          observed_external('1003')))
        report = audit(restore=after)
        self.assertTrue(report['restore_external_file_events_observed'])
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_EXTERNAL_TARGET_NOT_ISOLATED_TO_CONTROL')

    def test_capture_from_different_pid_is_not_calibrated_same_process(self):
        control = csv_log(*(observed_stock('1002') +
                            observed_external('2222')))
        report = audit(control=control)
        self.assertTrue(report['control_same_pid_open_read_observed'])
        self.assertFalse(report['control_external_and_sentinel_same_pid'])
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_CONTROL_TARGET_ACCESS_WITHOUT_CALIBRATED_READ')

    def test_control_open_only_is_not_successful_read(self):
        control = csv_log(*(observed_stock('1002') +
                            [row('CreateFile', path=WINDOWS_FILE, pid='1002')]))
        report = audit(control=control)
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_CONTROL_TARGET_ACCESS_WITHOUT_CALIBRATED_READ')
        self.assertFalse(report['control_same_pid_open_read_observed'])

    def test_control_no_external_access_is_inconclusive(self):
        report = audit(control=csv_log(*observed_stock('1002')))
        self.assertEqual(report['evidence_level'],
                         'INCONCLUSIVE_NO_CONTROL_FILE_READ')
        self.assertFalse(report['control_external_file_events_observed'])

    def test_source_path_mismatch_or_bad_format_fails(self):
        with self.assertRaises(ValueError):
            audit(resource=r'C:\Carbon-Test\MODS\Other.BUN')
        with self.assertRaises(ValueError):
            audit(source=b'not a native PC resource root')

    def test_sentinel_must_be_different_and_inside_game(self):
        for stock in (WINDOWS_FILE, r'C:\Outside\TRACKS\OTHER.BUN',
                      r'D:\Carbon-Test\TRACKS\STREAML5RB.BUN'):
            with self.subTest(stock=stock), self.assertRaises(ValueError):
                audit(sentinel=stock)

    def test_missing_and_malformed_capture_fails(self):
        with self.assertRaises(ValueError):
            audit(base='')
        with self.assertRaises(ValueError):
            audit(restore='not a csv')
        with self.assertRaises(ValueError):
            audit(control=b'bad csv')

    def test_redacted_status_contains_no_paths_pids_or_hashes(self):
        output = json.dumps(audit())
        for value in (WINDOWS_GAME, WINDOWS_FILE, SENTINEL,
                      '1001', '1002', '1003', '0xA0B0C0D0'):
            self.assertNotIn(value, output)

    def test_target_read_before_open_does_not_qualify(self):
        control = csv_log(*(observed_stock('1002') + [
            row('ReadFile', pid='1002', path=WINDOWS_FILE,
                detail=f'Offset: 0, Length: {len(SOURCE)}, I/O Flags: Cached'),
            row('CreateFile', pid='1002', path=WINDOWS_FILE),
        ]))
        report = audit(control=control)
        self.assertFalse(report['control_same_pid_open_read_observed'])

    def test_failed_stock_read_does_not_calibrate_capture(self):
        control = csv_log(
            row('CreateFile', pid='1002', path=SENTINEL),
            row('ReadFile', pid='1002', path=SENTINEL, result='ACCESS DENIED'),
            *observed_external('1002'))
        report = audit(control=control)
        self.assertFalse(report['control_calibrated'])

    def test_stock_file_read_from_wrong_process_ignored(self):
        control = csv_log(
            row('CreateFile', pid='1002', name='NonCarbon.exe', path=SENTINEL),
            row('ReadFile', pid='1002', name='NonCarbon.exe', path=SENTINEL),
            *observed_external('1002'))
        report = audit(control=control)
        self.assertFalse(report['control_calibrated'])

    def test_duplicate_columns_rejected(self):
        header = 'Process Name,Process Name,PID,Operation,Path,Result,Detail\n'
        with self.assertRaises(ValueError):
            audit(base=header)

    def test_bounded_csv_and_invalid_private_inputs(self):
        with self.assertRaises(ValueError):
            _capture_probe('A' * (24*1024*1024+1), WINDOWS_FILE, SENTINEL)
        with self.assertRaises(ValueError):
            _capture_probe('', WINDOWS_FILE, SENTINEL)


class OwnerLocalComparisonTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.game = Path(self.folder.name) / 'Carbon-Test'
        (self.game / 'scripts').mkdir(parents=True)
        (self.game / 'MODS').mkdir()
        (self.game / 'TRACKS').mkdir()
        self.manifest = self.game / 'scripts' / 'XNFSModFiles.txt'
        self.external = self.game / 'MODS' / 'KnownGoodPC.BUN'
        self.sentinel = self.game / 'TRACKS' / 'STREAML5RB.BUN'
        self.a = Path(self.folder.name) / 'baseline.csv'
        self.b = Path(self.folder.name) / 'control.csv'
        self.c = Path(self.folder.name) / 'restore.csv'
        self.manifest.write_bytes(MANIFEST)
        self.external.write_bytes(SOURCE)
        self.sentinel.write_bytes(b'STOCK Carbon PC sentinel fixture (synthetic) ')
        self.a.write_text(baseline(), encoding='utf-8')
        self.b.write_text(controlled(), encoding='utf-8')
        self.c.write_text(restored(), encoding='utf-8')

    def run_audit(self, **kwargs):
        inputs = dict(
            game_directory=self.game, manifest_path=self.manifest,
            original_resource_path=self.external,
            sentinel_game_file=self.sentinel, baseline_csv=self.a,
            control_csv=self.b, restore_csv=self.c, kind='geometry',
            windows_root_override_for_tests=WINDOWS_GAME)
        inputs.update(kwargs)
        return audit_owner_aba_files(**inputs)

    def test_owner_private_inputs_are_unchanged(self):
        inputs = (self.manifest, self.external, self.sentinel,
                  self.a, self.b, self.c)
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in inputs]
        report = self.run_audit()
        after = [(p.read_bytes(), p.stat().st_mtime_ns) for p in inputs]
        self.assertEqual(report['evidence_level'],
                         'ISOLATED_EXTERNAL_FILE_READ_OBSERVED_NOT_REGISTRATION')
        self.assertEqual(before, after)
        self.assertFalse(report['files_modified'])

    def test_detects_duplicate_capture_paths(self):
        with self.assertRaises(ValueError):
            self.run_audit(restore_csv=self.a)

    def test_detects_sentinel_outside_root(self):
        outside = Path(self.folder.name) / 'STOCK.BUN'
        outside.write_bytes(b'STOCK mock owner sentinel')
        with self.assertRaises(ValueError):
            self.run_audit(sentinel_game_file=outside)

    def test_rejects_shadowing_loader_manifests(self):
        (self.game / 'XNFSModFiles.txt').write_bytes(MANIFEST)
        with self.assertRaises(ValueError):
            self.run_audit()

    def test_rejects_missing_capture(self):
        with self.assertRaises(ValueError):
            self.run_audit(baseline_csv=self.game / 'missing.csv')

    def test_rejects_symlinked_sentinel(self):
        original = self.game / 'TRACKS' / 'ORIGINAL.BUN'
        original.write_bytes(b'private synthetic sentinel root')
        alias = self.game / 'TRACKS' / 'ALIAS.BUN'
        try:
            alias.symlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest('Host cannot create symlinks')
        with self.assertRaises(ValueError):
            self.run_audit(sentinel_game_file=alias)


if __name__ == '__main__':
    unittest.main()
