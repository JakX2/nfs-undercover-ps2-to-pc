"""Synthetic-only correlation tests for Carbon PC original external control.

No retail assets, original loader, game process or installed binaries used.
"""
import json
from pathlib import Path
import tempfile
import unittest

from carbon_pc_original_loader_control_chain import (
    audit_carbon_original_external_control,
    audit_owner_carbon_control_files,
)
from test_carbon_pc_external_resource_read_gate import (
    synthetic_carbon_geometry, csv_log, row, log_for_file,
)
from test_texture_visual_pair_gate import make_pack


WINDOWS_GAME = r'C:\Carbon-Test'
WINDOWS_FILE = r'C:\Carbon-Test\MODS\KnownGoodPC.BUN'
MANIFEST = b'1,1,MODS\\KnownGoodPC.BUN\r\n'
SOURCE = synthetic_carbon_geometry()
CAPTURE = log_for_file(len(SOURCE), path=WINDOWS_FILE)


def verify(*, manifest=MANIFEST, source=SOURCE, csv=CAPTURE,
           game=WINDOWS_GAME, resource=WINDOWS_FILE, kind='geometry'):
    return audit_carbon_original_external_control(
        manifest, source, csv, game, resource, kind)


class InMemoryControlTests(unittest.TestCase):
    def test_real_original_free_source_and_full_observed_read(self):
        result = verify()
        self.assertEqual(result['control_evidence'],
                         'EXACT_ORIGINAL_PC_FILE_READ_FULL_NOT_REGISTRATION')
        self.assertTrue(result['source_compatible_with_native_pc_parser'])
        self.assertTrue(result['configured_path_matches_original_file'])
        self.assertTrue(result['captured_exact_target_events_observed'])
        self.assertTrue(result['entire_original_file_read_by_one_process_observed'])
        self.assertEqual(result['source_resource_records'], 1)
        self.assertEqual(result['read_bytes_covered_by_one_process'], len(SOURCE))
        self.assertEqual(result['original_file_bytes'], len(SOURCE))
        self.assertEqual(result['loader_stage'], 'postinit')
        self.assertEqual(result['loader_resource_type'], 1)
        for name in ('original_retail_provenance_verified',
                     'xnfsmodfiles_asi_loaded_verified',
                     'resource_create_begin_loading_invoked_verified',
                     'native_carbon_resource_registered_verified',
                     'in_game_visual_change_verified',
                     'undercover_model_loaded_verified', 'files_modified'):
            self.assertFalse(result[name], name)

    def test_partial_read_keeps_unverified_registration(self):
        partial = csv_log(
            row('CreateFile', path=WINDOWS_FILE),
            row('ReadFile', path=WINDOWS_FILE,
                detail='Offset: 8, Length: 20, I/O Flags: Cached'))
        out = verify(csv=partial)
        self.assertEqual(out['control_evidence'],
                         'EXACT_ORIGINAL_PC_FILE_READ_PARTIAL_OR_UNKNOWN_NOT_REGISTRATION')
        self.assertEqual(out['read_bytes_covered_by_one_process'], 20)

    def test_open_without_read_not_marked_read(self):
        result = verify(csv=csv_log(row('CreateFile', path=WINDOWS_FILE)))
        self.assertEqual(result['control_evidence'],
                         'ORIGINAL_PC_FILE_OPEN_OBSERVED_NO_READ')
        self.assertFalse(result['same_pid_ordered_open_read_observed'])

    def test_no_exact_access_is_inconclusive(self):
        result = verify(csv=csv_log(row('CreateFile',
                                         path=r'C:\Carbon-Test\MODS\Other.BUN')))
        self.assertEqual(result['control_evidence'],
                         'NO_POSITIVE_ORIGINAL_PC_FILE_IO_EVIDENCE')
        self.assertFalse(result['same_pid_ordered_open_read_observed'])
        self.assertFalse(result['captured_exact_target_events_observed'])

    def test_wrong_manifest_filename_rejected_even_with_positive_io(self):
        with self.assertRaises(ValueError):
            verify(manifest=b'1,1,MODS\\Other.BUN\n')

    def test_manifest_and_source_must_share_same_root(self):
        for path in (r'C:\Other-Test\MODS\KnownGoodPC.BUN',
                     r'C:\Carbon-Test\Other\KnownGoodPC.BUN',
                     r'C:\Carbon-Test\MODS\..\Outside.BUN',
                     r'D:\Carbon-Test\MODS\KnownGoodPC.BUN'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                verify(resource=path)

    def test_bad_drive_root_rejected(self):
        for root in ('', r'C:', 'C:\\', r'\\server\share',
                     r'\Carbon-Test', 'C:relative'):
            with self.subTest(root=root), self.assertRaises(ValueError):
                verify(game=root)

    def test_wrong_pc_format_blocked_before_runtime_claim(self):
        with self.assertRaises(ValueError):
            verify(source=make_pack('ps2', hashes=(0x12345678,)),
                   kind='texture')
        with self.assertRaises(ValueError):
            verify(source=SOURCE[:-1])
        with self.assertRaises(ValueError):
            verify(source=bytearray(SOURCE))

    def test_original_pc_texture_control_is_supported(self):
        texture = make_pack('pc', hashes=(0x12345678,))
        report = verify(source=texture, kind='texture',
                        csv=log_for_file(len(texture), path=WINDOWS_FILE))
        self.assertEqual(report['source_kind'], 'native_pc_texture')
        self.assertEqual(report['source_resource_records'], 1)
        self.assertTrue(report['entire_original_file_read_by_one_process_observed'])

    def test_redacted_report_contains_no_private_identity_or_pid(self):
        report = verify()
        serialized = json.dumps(report)
        for secret in (WINDOWS_GAME, WINDOWS_FILE, 'KnownGoodPC',
                       '555', '0xA0B0C0D0', '0x12345678'):
            self.assertNotIn(secret, serialized)

    def test_same_pid_required_not_two_separate_processes(self):
        csv = csv_log(
            row('CreateFile', path=WINDOWS_FILE, pid='555'),
            row('ReadFile', path=WINDOWS_FILE, pid='556',
                detail=f'Offset: 0, Length: {len(SOURCE)}, I/O Flags: Cached'))
        report = verify(csv=csv)
        self.assertEqual(report['control_evidence'],
                         'ORIGINAL_PC_FILE_OPEN_OBSERVED_NO_READ')

    def test_nonpc_or_malformed_procmon_rejected(self):
        with self.assertRaises(ValueError):
            verify(csv='not a csv')
        with self.assertRaises(ValueError):
            verify(kind='unknown')


class OwnerLocalFileChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'Carbon'
        self.scripts = self.root / 'scripts'
        self.mods = self.root / 'MODS'
        self.scripts.mkdir(parents=True)
        self.mods.mkdir(parents=True)
        self.manifest = self.scripts / 'XNFSModFiles.txt'
        self.source = self.mods / 'KnownGoodPC.BUN'
        self.procmon = Path(self.tmp.name) / 'capture.csv'
        self.manifest.write_bytes(MANIFEST)
        self.source.write_bytes(SOURCE)
        self.procmon.write_text(CAPTURE, encoding='utf-8')

    def audit(self, **kwargs):
        arguments = dict(game_directory=self.root, manifest_path=self.manifest,
                         original_resource_path=self.source,
                         procmon_csv=self.procmon, kind='geometry',
                         windows_root_override_for_tests=WINDOWS_GAME)
        arguments.update(kwargs)
        return audit_owner_carbon_control_files(**arguments)

    def test_file_audit_uses_actual_mods_root_and_no_changes(self):
        files = (self.manifest, self.source, self.procmon)
        before = [p.read_bytes() for p in files]
        timestamps = [p.stat().st_mtime_ns for p in files]
        report = self.audit()
        self.assertEqual(report['control_evidence'],
                         'EXACT_ORIGINAL_PC_FILE_READ_FULL_NOT_REGISTRATION')
        self.assertEqual([p.read_bytes() for p in files], before)
        self.assertEqual([p.stat().st_mtime_ns for p in files], timestamps)
        self.assertFalse(report['files_modified'])

    def test_config_in_root_is_allowed_if_scripts_not_shadowing(self):
        top = self.root / 'XNFSModFiles.txt'
        self.manifest.rename(top)
        self.assertEqual(self.audit(manifest_path=top)['loader_stage'], 'postinit')

    def test_two_manifests_rejected_to_avoid_loader_shadowing(self):
        (self.root / 'XNFSModFiles.txt').write_bytes(MANIFEST)
        with self.assertRaises(ValueError):
            self.audit()

    def test_manifest_outside_loader_search_paths_rejected(self):
        third = self.root / 'other' / 'XNFSModFiles.txt'
        third.parent.mkdir()
        third.write_bytes(MANIFEST)
        with self.assertRaises(ValueError):
            self.audit(manifest_path=third)

    def test_resource_outside_mods_rejected(self):
        outside = self.root / 'KnownGoodPC.BUN'
        outside.write_bytes(SOURCE)
        with self.assertRaises(ValueError):
            self.audit(original_resource_path=outside)

    def test_resource_with_different_name_from_config_rejected(self):
        other = self.mods / 'NotConfigured.BUN'
        other.write_bytes(SOURCE)
        with self.assertRaises(ValueError):
            self.audit(original_resource_path=other)

    def test_rejects_source_symlink(self):
        target = self.mods / 'Original.BUN'
        target.write_bytes(SOURCE)
        alias = self.mods / 'KnownGoodPCLink.BUN'
        try:
            alias.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink unavailable on host')
        with self.assertRaises(ValueError):
            self.audit(original_resource_path=alias)

    def test_rejects_missing_capture(self):
        with self.assertRaises(ValueError):
            self.audit(procmon_csv=self.root / 'missing.csv')

    def test_rejects_source_outside_game_even_if_valid_pc(self):
        outside = Path(self.tmp.name) / 'Other.BUN'
        outside.write_bytes(SOURCE)
        with self.assertRaises(ValueError):
            self.audit(original_resource_path=outside)

    def test_rejects_ambiguous_or_missing_local_game(self):
        with self.assertRaises(ValueError):
            self.audit(game_directory=self.root / 'nonexistent')

    def test_rejects_misplaced_manifest_with_valid_bytes(self):
        duplicate = Path(self.tmp.name) / 'XNFSModFiles.txt'
        duplicate.write_bytes(MANIFEST)
        with self.assertRaises(ValueError):
            self.audit(manifest_path=duplicate)

    def test_test_override_only_creates_offline_evidence(self):
        report = self.audit()
        self.assertFalse(report['original_retail_provenance_verified'])
        self.assertFalse(report['xnfsmodfiles_asi_loaded_verified'])
        self.assertFalse(report['native_carbon_resource_registered_verified'])


if __name__ == '__main__':
    unittest.main()
