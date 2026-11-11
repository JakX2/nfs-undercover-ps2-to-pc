"""Synthetic ProcMon and original-free Carbon PC resource-read control tests."""
import csv
import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import carbon_pc_external_resource_read_gate as gate
from undercover_pc_geometry_bridge import convert_decoded_ps2_model
from test_texture_visual_pair_gate import make_pack


WIN_RESOURCE = r'C:\Carbon\MODS\External\KnownGoodPC.bin'
OTHER_RESOURCE = r'C:\Carbon\MODS\Other\KnownGoodPC.bin'
M = 0xA0B0C0D0
T = 0x12345678


def synthetic_carbon_geometry():
    xyz = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    uv = ((0., 0.), (1., 0.), (0., 1.))
    return convert_decoded_ps2_model(
        M, (T,), xyz, uv, ((0, 1, 2),), (0,))[0]


def row(op, *, pid='555', name='NFSC.exe', path=WIN_RESOURCE,
        result='SUCCESS', detail=''):
    return {'Process Name': name, 'PID': pid, 'Operation': op,
            'Path': path, 'Result': result, 'Detail': detail}


def csv_log(*rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=(
        'Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail'))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def log_for_file(size, pid='555', path=WIN_RESOURCE):
    half = size // 2
    return csv_log(
        row('CreateFile', pid=pid, path=path),
        row('ReadFile', pid=pid, path=path,
            detail=f'Offset: 0, Length: {half}, I/O Flags: Cached'),
        row('ReadFile', pid=pid, path=path,
            detail=f'Offset: {half}, Length: {size-half}, I/O Flags: Cached'))


class ExternalTraceTests(unittest.TestCase):
    def test_valid_full_read_same_pid_ordered(self):
        source = synthetic_carbon_geometry()
        result = gate.audit_external_resource_trace(
            log_for_file(len(source)), WIN_RESOURCE, len(source), 'geometry')
        self.assertTrue(result['same_pid_ordered_open_read_observed'])
        self.assertTrue(result['entire_file_read_by_one_process_observed'])
        self.assertEqual(result['verified_file_bytes_read_for_one_process'],
                         len(source))
        self.assertEqual(result['source_kind'], 'native_pc_geometry')
        self.assertEqual(result['evidence_level'],
                         'FULL_FILE_READ_OBSERVED_NOT_ASSET_REGISTRATION')
        for key in ('carbon_external_loader_abi_verified',
                    'carbon_asset_registration_verified',
                    'carbon_in_game_rendering_verified',
                    'undercover_resource_loading_verified'):
            self.assertFalse(result[key])

    def test_partial_read_is_not_full(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile'),
            row('ReadFile', detail='Offset: 4, Length: 16, I/O Flags: Cached')),
            WIN_RESOURCE, 4096, 'texture')
        self.assertEqual(out['evidence_level'],
                         'PARTIAL_FILE_READ_OBSERVED_NOT_ASSET_REGISTRATION')
        self.assertEqual(out['verified_file_bytes_read_for_one_process'], 16)

    def test_duplicate_overlapping_reads_do_not_inflate_coverage(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile'), row('ReadFile', detail='Offset: 0, Length: 70, A: b'),
            row('ReadFile', detail='Offset: 30, Length: 70, A: b'),
            row('ReadFile', detail='Offset: 30, Length: 70, A: b')),
            WIN_RESOURCE, 100, 'texture')
        self.assertEqual(out['verified_file_bytes_read_for_one_process'], 100)

    def test_read_before_open_not_an_ordered_access(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('ReadFile', detail='Offset: 0, Length: 100, A: b'),
            row('CreateFile')), WIN_RESOURCE, 100, 'geometry')
        self.assertFalse(out['same_pid_ordered_open_read_observed'])
        self.assertEqual(out['evidence_level'], 'EXACT_FILE_OPEN_ONLY')

    def test_read_from_different_pid_not_combined(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile', pid='555'),
            row('ReadFile', pid='556', detail='Offset: 0, Length: 100, A: b')),
            WIN_RESOURCE, 100, 'geometry')
        self.assertFalse(out['entire_file_read_by_one_process_observed'])
        self.assertFalse(out['same_pid_ordered_open_read_observed'])

    def test_split_coverage_from_different_processes_not_combined(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile', pid='555'), row('CreateFile', pid='556'),
            row('ReadFile', pid='555', detail='Offset: 0, Length: 50, A: b'),
            row('ReadFile', pid='556', detail='Offset: 50, Length: 50, A: b')),
            WIN_RESOURCE, 100, 'geometry')
        self.assertTrue(out['same_pid_ordered_open_read_observed'])
        self.assertEqual(out['verified_file_bytes_read_for_one_process'], 50)

    def test_exact_path_and_process_match_only(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile', path=OTHER_RESOURCE),
            row('ReadFile', path=OTHER_RESOURCE,
                detail='Offset: 0, Length: 100, A: b'),
            row('CreateFile', name='NotCarbon.exe'),
            row('ReadFile', name='NotCarbon.exe',
                detail='Offset: 0, Length: 100, A: b')),
            WIN_RESOURCE, 100, 'geometry')
        self.assertEqual(out['candidate_target_events'], 0)

    def test_windows_case_and_separator_normalization(self):
        lower = 'c:/carbon/mods/external/knowngoodpc.bin'
        out = gate.audit_external_resource_trace(
            log_for_file(100, path=lower), WIN_RESOURCE, 100, 'geometry')
        self.assertTrue(out['entire_file_read_by_one_process_observed'])

    def test_failure_not_counted_as_positive_io(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile', result='ACCESS DENIED'),
            row('ReadFile', detail='Offset: 0, Length: 100, A: b')),
            WIN_RESOURCE, 100, 'geometry')
        self.assertEqual(out['failed_target_events'], 1)
        self.assertFalse(out['same_pid_ordered_open_read_observed'])

    def test_out_of_range_read_and_unparseable_offsets_not_accepted(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile'),
            row('ReadFile', detail='Offset: 0, Length: 101, A: b'),
            row('ReadFile', detail='Offset: bad, Length: 50, A: b')),
            WIN_RESOURCE, 100, 'geometry')
        self.assertEqual(out['verified_file_bytes_read_for_one_process'], 0)
        self.assertEqual(out['evidence_level'],
                         'EXACT_FILE_OPEN_READ_OFFSETS_UNVERIFIED')

    def test_strict_windows_path_rejects_ambiguous_paths(self):
        for bad in ('Carbon.bin', r'.\test.bin', r'\RootOnly.bin',
                    r'\\server\share\resource.bin', 'C:relative.bin',
                    'C:\\Carbon\\file.csv', 'C:\\Carbon\\ab\x00.bin'):
            with self.subTest(path=repr(bad)), self.assertRaises(ValueError):
                gate._windows_bundle_path(bad)

    def test_invalid_inputs_fail_closed(self):
        for length in (True, 0, -1, 39, 32*1024*1024+1):
            with self.subTest(length=length), self.assertRaises(ValueError):
                gate.audit_external_resource_trace(csv_log(), WIN_RESOURCE,
                                                   length, 'geometry')
        with self.assertRaises(ValueError):
            gate.audit_external_resource_trace(csv_log(), WIN_RESOURCE,
                                               100, 'unknown')
        with self.assertRaises(ValueError):
            gate.audit_external_resource_trace('hello', WIN_RESOURCE,
                                               100, 'geometry')
        with self.assertRaises(ValueError):
            gate.audit_external_resource_trace(b'not csv', WIN_RESOURCE,
                                               100, 'geometry')

    def test_aggregate_does_not_expose_private_path_or_pid(self):
        data = gate.audit_external_resource_trace(
            log_for_file(100), WIN_RESOURCE, 100, 'texture')
        rendered = json.dumps(data)
        self.assertNotIn(WIN_RESOURCE, rendered)
        self.assertNotIn('KnownGoodPC', rendered)
        self.assertNotIn('555', rendered)

    def test_multiple_reads_and_bad_operation_ignored(self):
        out = gate.audit_external_resource_trace(csv_log(
            row('CreateFile'),
            row('QueryBasicInformationFile'),
            row('ReadFile', detail='Offset: 0, Length: 40, A: b')),
            WIN_RESOURCE, 100, 'texture')
        self.assertEqual(out['candidate_target_events'], 2)
        self.assertEqual(out['reads_with_valid_file_spans_after_open'], 1)


class OriginalCarbonSourceTests(unittest.TestCase):
    def test_genuine_pc_framing_synthetic_geometry(self):
        info = gate._verify_native_resource(synthetic_carbon_geometry(), 'geometry')
        self.assertEqual(info['resource_kind'], 'native_pc_geometry')
        self.assertEqual(info['source_resource_records'], 1)

    def test_genuine_pc_framing_synthetic_texture(self):
        image = make_pack('pc', hashes=(T,))
        info = gate._verify_native_resource(image, 'texture')
        self.assertEqual(info['source_resource_records'], 1)
        self.assertEqual(info['resource_kind'], 'native_pc_texture')

    def test_reject_ps2_texture_and_corrupt_source(self):
        with self.assertRaises(ValueError):
            gate._verify_native_resource(make_pack('ps2', hashes=(T,)),
                                         'texture')
        with self.assertRaises(ValueError):
            gate._verify_native_resource(make_pack('pc', hashes=(T,)) + b'junk',
                                         'texture')
        with self.assertRaises(ValueError):
            gate._verify_native_resource(b'UNSUPPORTED GEOMETRY', 'geometry')

    def test_read_only_owner_files_and_private_output(self):
        with tempfile.TemporaryDirectory() as td:
            resource = Path(td) / 'owner-carbon-root.bin'
            procmon = Path(td) / 'capture.csv'
            content = synthetic_carbon_geometry()
            resource.write_bytes(content)
            procmon.write_text(log_for_file(len(content)), encoding='utf-8')
            before = resource.stat()
            with patch.object(gate, 'audit_external_resource_trace',
                              wraps=gate.audit_external_resource_trace) as tracer, \
                 patch.object(gate, '_windows_bundle_path',
                              return_value=gate._windows_bundle_path(WIN_RESOURCE)):
                report = gate.audit_original_files(resource, 'geometry', procmon)
            self.assertTrue(tracer.called)
            self.assertTrue(report['original_pc_resource_framing_verified'])
            self.assertFalse(report['local_files_modified'])
            self.assertEqual(report['source_resource_records'], 1)
            self.assertNotIn(str(resource), json.dumps(report))
            after = resource.stat()
            self.assertEqual((before.st_size, before.st_mtime_ns),
                             (after.st_size, after.st_mtime_ns))

    def test_missing_capture_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            resource = Path(td) / 'owner-carbon-root.bin'
            resource.write_bytes(synthetic_carbon_geometry())
            with self.assertRaises(ValueError):
                gate.audit_original_files(resource, 'geometry',
                                          Path(td) / 'missing.csv')


if __name__ == '__main__':
    unittest.main()
