"""Source-free, synthetic-only game stream byte and ProcMon trace tests."""
import csv
from io import StringIO
from pathlib import Path
import struct
import tempfile
import unittest

from carbon_pc_runtime_span_attestation import (
    _normalized_windows_file, _read_span, _interval_coverage, analyze_trace,
    existing_image_span, verify_private_copy, attest)
from synthetic_pc_dxt1_pack_envelope import build_synthetic_pc_dxt1_pack
from test_undercover_to_pc_dxt5_bridge import dxt5_pc_fixture
from test_synthetic_pc_dxt1_pack_envelope import fixture
from texture_metadata_pixel_bridge import parse_pack
from pc_texture_header_overlay_gate import _source_image_span

WIN = r'C:\Games\Carbon\TRACKS\STREAML5RB.BUN'
OTHER = r'D:\Other\Carbon\TRACKS\STREAML5RB.BUN'
HEADER = ['Time of Day', 'Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail']


def trace(*events):
    out = StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(HEADER)
    for args in events:
        writer.writerow(['12:00:00', *args])
    return out.getvalue()


def row(operation, path=WIN, pid='100', result='SUCCESS', detail='', process='NFSC.exe'):
    return (process, pid, operation, path, result, detail)


def make_sources(folder, codec='DXT1', sid=141):
    section = (build_synthetic_pc_dxt1_pack([fixture(0x12345678, b'SYNTH_SLOT',
                  width=8, height=8)]) if codec == 'DXT1' else dxt5_pc_fixture())
    table = bytearray(92)
    struct.pack_into('<h', table, 8, sid)
    struct.pack_into('<II', table, 0x14, 2048, len(section))
    bundle = struct.pack('<II', 0x34110, len(table)) + table
    original = bytes(2048) + section + b'EOF'
    fp = folder / 'L5RB.BUN'
    old = folder / 'pristine.bun'
    stage = folder / 'stage.bun'
    game = folder / 'game.bun'
    fp.write_bytes(bundle)
    old.write_bytes(original)
    meta = parse_pack(section, 'pc')['records']
    key = sorted(k for k, m in meta.items() if m['codec'] == (34 if codec == 'DXT1' else 38))[0]
    low, high = _source_image_span(section, meta[key])
    start, size = 2048 + low, high - low
    staged = bytearray(original)
    staged[start:start + size] = bytes(v ^ 0x5a for v in staged[start:start + size])
    stage.write_bytes(staged)
    game.write_bytes(staged)
    return fp, old, stage, game, start, size


class TraceParserTests(unittest.TestCase):
    def test_decimal_and_comma_offsets(self):
        self.assertEqual(_read_span('Offset: 1,024, Length: 4,096, I/O Flags: Paging I/O'), (1024, 5120))

    def test_hex_offsets(self):
        self.assertEqual(_read_span('Offset: 0x100, Length: 0x40'), (256, 320))

    def test_malformed_and_zero_length_rejected(self):
        for s in ('Offset: -1, Length: 3', 'Offset: 20, Length: 0',
                  'Offset: 10, Length: nope', 'Offset: 1, Length: 3,000,000,000'):
            self.assertIsNone(_read_span(s), s)

    def test_interval_union_counts_unique_bytes(self):
        self.assertEqual(_interval_coverage([(10, 18), (12, 18), (17, 25)], 12, 23), 11)

    def test_nonabsolute_expected_path_rejected(self):
        for x in ('TRACKS\\STREAML5RB.BUN', r'C:\Games\TRACKS\STREAML5RB.BUNX', ''):
            with self.assertRaises(ValueError):
                _normalized_windows_file(x)

    def test_path_case_normalization(self):
        self.assertEqual(_normalized_windows_file(WIN),
                         _normalized_windows_file(r'c:/games/CARBON/tracks/streaml5rb.bun'))

    def test_exact_path_open_then_overlapping_read(self):
        text = trace(row('CreateFile'), row('ReadFile', detail='Offset: 500, Length: 800'))
        got = analyze_trace(text, WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'full_image_span_read_observed_not_rendering')
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 100)
        self.assertNotIn(r'C:\Games', repr(got))
        self.assertNotIn("'PID':", repr(got))

    def test_read_overlap_partial(self):
        got = analyze_trace(trace(row('CreateFile'), row('ReadFile', detail='Offset: 760, Length: 20')), WIN, 700, 100)
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 20)
        self.assertEqual(got['evidence_level'], 'some_image_bytes_read_observed_not_rendering')

    def test_read_outside_image(self):
        got = analyze_trace(trace(row('CreateFile'), row('ReadFile', detail='Offset: 100, Length: 200')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'exact_stream_open_and_read_without_proven_image_overlap')

    def test_read_before_open_does_not_count(self):
        got = analyze_trace(trace(row('ReadFile', detail='Offset: 700, Length: 100'), row('CreateFile')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'exact_stream_open_only')

    def test_different_pids_cannot_be_combined(self):
        got = analyze_trace(trace(row('CreateFile', pid='100'), row('ReadFile', pid='101', detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertFalse(got['same_pid_ordered_open_read_observed'])

    def test_different_paths_cannot_be_combined(self):
        got = analyze_trace(trace(row('CreateFile'), row('ReadFile', path=OTHER, detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'exact_stream_open_only')

    def test_windows_path_case_insensitive(self):
        got = analyze_trace(trace(row('CreateFile', path=r'c:/games/carbon/tracks/streaml5rb.bun'),
                                  row('ReadFile', detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 100)

    def test_error_events_do_not_count(self):
        got = analyze_trace(trace(row('CreateFile', result='NAME NOT FOUND'),
                                  row('ReadFile', detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'no_positive_exact_stream_open')
        self.assertEqual(got['failed_target_events'], 1)

    def test_partial_read_info_not_overclaim(self):
        got = analyze_trace(trace(row('CreateFile'), row('ReadFile', detail='Length: 100')), WIN, 700, 100)
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 0)
        self.assertTrue(got['same_pid_ordered_open_read_observed'])

    def test_adjacent_ranges_cover_whole_span(self):
        got = analyze_trace(trace(row('CreateFile'), row('ReadFile', detail='Offset: 700, Length: 40'),
                                  row('ReadFile', detail='Offset: 740, Length: 60')), WIN, 700, 100)
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 100)

    def test_multiple_processes_cannot_sum_partial_coverage(self):
        got = analyze_trace(trace(row('CreateFile', pid='100'), row('ReadFile', pid='100', detail='Offset: 700, Length: 50'),
                                  row('CreateFile', pid='200'), row('ReadFile', pid='200', detail='Offset: 750, Length: 50')), WIN, 700, 100)
        self.assertEqual(got['matched_image_bytes_covered_for_one_process'], 50)

    def test_wrong_executable_ignored(self):
        got = analyze_trace(trace(row('CreateFile', process='not_nfsc.exe'),
                                  row('ReadFile', process='not_nfsc.exe', detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'no_positive_exact_stream_open')

    def test_invalid_pid_ignored(self):
        got = analyze_trace(trace(row('CreateFile', pid=''), row('ReadFile', pid='0', detail='Offset: 700, Length: 100')), WIN, 700, 100)
        self.assertEqual(got['evidence_level'], 'no_positive_exact_stream_open')

    def test_missing_columns_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'columns'):
            analyze_trace('Process Name,Path\nNFSC.exe,bad\n', WIN, 700, 100)

    def test_bad_image_span_rejected(self):
        with self.assertRaisesRegex(ValueError, 'span'):
            analyze_trace(trace(), WIN, -1, 1)

    def test_event_limit_rejected(self):
        raw = ','.join(HEADER) + '\n' + ('12,NFSC.exe,1,X,Y,SUCCESS,Z\n' * 200001)
        with self.assertRaisesRegex(ValueError, 'limit'):
            analyze_trace(raw, WIN, 700, 100)


class StreamIntegrityTests(unittest.TestCase):
    def test_existing_dxt1_slot_span_from_header(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            self.assertEqual(existing_image_span(a, b, 141, 'DXT1', 0), (start, size))

    def test_existing_dxt5_slot_span_from_header(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d), 'DXT5', sid=142)
            self.assertEqual(existing_image_span(a, b, 142, 'DXT5', 0), (start, size))

    def test_file_three_way_digests_match_and_replacement_confined(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            got = verify_private_copy(b, c, e, start, size)
            self.assertTrue(got['installed_stream_currently_matches_stage'])
            self.assertGreater(got['changed_image_bytes'], 0)
            self.assertNotIn('sha256', str(got))

    def test_modified_neighbor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            raw = bytearray(c.read_bytes()); raw[100] ^= 0x7f; c.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'outside'):
                verify_private_copy(b, c, e, start, size)

    def test_installed_stream_different_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            e.write_bytes(b.read_bytes())
            with self.assertRaisesRegex(ValueError, 'does not match'):
                verify_private_copy(b, c, e, start, size)

    def test_source_same_stage_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            c.write_bytes(b.read_bytes())
            with self.assertRaisesRegex(ValueError, 'No valid'):
                verify_private_copy(b, c, e, start, size)

    def test_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            alias = Path(d) / 'alias.bun'
            try:
                alias.hardlink_to(c)
            except (OSError, NotImplementedError):
                self.skipTest('Hardlinks not available')
            with self.assertRaisesRegex(ValueError, 'Hard-linked'):
                verify_private_copy(b, c, alias, start, size)

    def test_bad_ordinal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            with self.assertRaisesRegex(ValueError, 'slot'):
                existing_image_span(a, b, 141, 'DXT1', 100)

    def test_unsupported_codec_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            with self.assertRaisesRegex(ValueError, 'DXT1/DXT5'):
                existing_image_span(a, b, 141, 'DXT3', 0)

    def test_end_to_end_true_but_not_rendering(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            csvfile = Path(d) / 'trace.csv'
            csvfile.write_text(trace(row('CreateFile'),
                                     row('ReadFile', detail=f'Offset: {start}, Length: {size}')))
            got = attest(a, b, c, e, csvfile, 141, 'DXT1', 0, WIN)
            self.assertEqual(got['procmon']['evidence_level'], 'full_image_span_read_observed_not_rendering')
            self.assertEqual(got['scope'], 'READ_ONLY_POST_CAPTURE_ATTESTATION_NOT_RUNTIME_RENDERING')
            self.assertTrue(got['copy_integrity']['stage_edits_confined_to_one_original_image'])
            self.assertNotIn(r'C:\Games', repr(got))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c, e, start, size = make_sources(Path(d))
            link = Path(d) / 'link.bun'
            try:
                link.symlink_to(c)
            except (OSError, NotImplementedError):
                self.skipTest('Symlinks not available')
            with self.assertRaisesRegex(ValueError, 'symlinked'):
                verify_private_copy(b, link, e, start, size)


if __name__ == '__main__':
    unittest.main()
