"""Phase 45 source-free regression tests for one-pass Carbon PC evidence bundle."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carbon_pc_steering_evidence_bundle as p45


def inst(pc, raw: bytes, mnemonic: str, operands: str = '') -> dict:
    return {'pc': pc, 'length': len(raw), 'bytes': raw,
            'mnemonic': mnemonic, 'operands': operands}


def fixture_instructions():
    """Synthetic instructions precisely at original *documented* store PCs."""
    return [
        inst(0x6ef7b3, bytes.fromhex('8b8604010000'), 'mov',
             'eax,DWORD PTR [esi+0x104]'),
        inst(0x6ef7b9, bytes.fromhex('898604010000'), 'mov',
             'DWORD PTR [esi+0x104],eax'),
        inst(0x6ef7bf, b'\x90', 'nop'),
        inst(0x6ef7c0, bytes.fromhex('899618010000'), 'mov',
             'DWORD PTR [esi+0x118],edx'),
    ]


def verified_fixture():
    return {
        'exe_sha256': 'SYNTHETIC_FIXTURE_NOT_ORIGINAL',
        'steering_function_va': '0x006EF540',
        'phase31_verified_checks': 17,
        'known_steering_store_instructions': [
            p45.decode_mov_store(bytes.fromhex(p45.BYTES[address]), address)
            for address in p45.ANCHOR_ADDRESSES
        ],
    }


def dummy_full_function():
    """Synthetic NOP code, not copied from any game source."""
    data = bytearray(b'\x90' * (p45.STEERING_END - p45.STEERING_START))
    for addr in p45.ANCHOR_ADDRESSES:
        offset = addr - p45.STEERING_START
        data[offset:offset + 6] = bytes.fromhex(p45.BYTES[addr])
    return bytes(data)


class AnchorGateTests(unittest.TestCase):
    def test_exact_two_store_anchors(self):
        anchors = p45.verify_anchor_disassembly(fixture_instructions(), verified_fixture())
        self.assertEqual([r['source_register'] for r in anchors], ['eax', 'edx'])

    def test_anchor_offsets_are_syntax_only(self):
        anchors = p45.verify_anchor_disassembly(fixture_instructions(), verified_fixture())
        self.assertEqual([r['signed_displacement'] for r in anchors], [0x104, 0x118])
        self.assertTrue(all(r['field_identity'] == 'unverified' for r in anchors))

    def test_reject_wrong_anchor_bytes(self):
        rows = fixture_instructions()
        rows[1]['bytes'] = b'\x90' * 6
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(rows, verified_fixture())

    def test_reject_missing_first_store(self):
        rows = fixture_instructions()
        rows[1]['pc'] = 0x6ef7ba
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(rows, verified_fixture())

    def test_reject_missing_second_store(self):
        rows = fixture_instructions()[:-1]
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(rows, verified_fixture())

    def test_reject_wrong_stored_register_metadata(self):
        verified = verified_fixture()
        verified['known_steering_store_instructions'][0]['source_register'] = 'edi'
        with self.assertRaisesRegex(ValueError, 'metadata mismatch'):
            p45.verify_anchor_disassembly(fixture_instructions(), verified)

    def test_reject_wrong_offset_metadata(self):
        verified = verified_fixture()
        verified['known_steering_store_instructions'][1]['signed_displacement'] = 0x500
        with self.assertRaisesRegex(ValueError, 'metadata mismatch'):
            p45.verify_anchor_disassembly(fixture_instructions(), verified)

    def test_reject_swapped_store_metadata(self):
        verified = verified_fixture()
        verified['known_steering_store_instructions'].reverse()
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(fixture_instructions(), verified)

    def test_reject_missing_phase40_report(self):
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(fixture_instructions(),
                                          {'known_steering_store_instructions': []})

    def test_reject_overlapping_decode(self):
        rows = fixture_instructions()
        rows[2]['pc'] = 0x6ef7b9
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(rows, verified_fixture())

    def test_reject_bad_source_length(self):
        rows = fixture_instructions()
        rows[3]['length'] = 7
        with self.assertRaises(ValueError):
            p45.verify_anchor_disassembly(rows, verified_fixture())


class ReportTests(unittest.TestCase):
    def test_phase_and_schema(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertEqual((report['phase'], report['schema_version']), (45, 1))

    def test_verified_source_metadata_preserved(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertEqual(report['source']['sha256'], 'SYNTHETIC_FIXTURE_NOT_ORIGINAL')
        self.assertEqual(report['source']['verified_phase31_checks'], 17)

    def test_first_register_reads_synthetic_memory(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        trace = report['register_origin_evidence'][0]['source_register_local_trace']
        self.assertEqual(trace['status'], 'memory_load_unknown_value')

    def test_second_register_stays_unknown(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        trace = report['register_origin_evidence'][1]['source_register_local_trace']
        self.assertEqual(trace['status'], 'block_live_in_unknown')

    def test_static_access_counts(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        summary = report['overview']['candidate_offsets']
        self.assertEqual([(x['candidate_offset'], x['static_read_occurrences'],
                           x['static_write_occurrences']) for x in summary],
                         [(0x104, 1, 1), (0x118, 0, 1)])

    def test_anchor_to_anchor_cfg_is_clean_only_syntactically(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        span = report['candidate_path_evidence']['anchor_to_anchor']
        self.assertTrue(span['route_with_no_detected_esi_write'])
        self.assertFalse(span['same_runtime_object_proven'])

    def test_report_preserves_uncertainty_flags(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertFalse(report['verification']['runtime_gameplay_execution_observed'])
        self.assertFalse(report['verification']['ps2_to_pc_field_equivalence_verified'])
        self.assertFalse(report['verification']['steering_handling_patch_produced'])

    def test_no_guessed_ps2_mapping(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertTrue(all(x['matching_ps2_offset'] is None
                            for x in report['overview']['candidate_offsets']))

    def test_no_opcode_bytes_in_json(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        text = json.dumps(report)
        self.assertNotIn('898604010000', text)
        self.assertNotIn('899618010000', text)

    def test_json_round_trip(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertEqual(json.loads(json.dumps(report))['phase'], 45)

    def test_derived_offsets_are_not_semantic_names(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertTrue(all(x['semantic_role'] == 'unverified'
                            for x in report['overview']['candidate_offsets']))

    def test_only_one_esi_census_is_used(self):
        with patch.object(p45, 'find_accesses',
                          wraps=p45.find_accesses) as census:
            p45.review_from_decoded(fixture_instructions(), verified_fixture())
        # phase43 independently cross-checks the same instructions once more.
        self.assertEqual(census.call_count, 1)

    def test_synthetic_real_binutils_works(self):
        raw = b''.join(r['bytes'] for r in fixture_instructions())
        instructions = p45.disassemble(raw, 0x6ef7b3)
        report = p45.review_from_decoded(instructions, verified_fixture())
        self.assertEqual(report['overview']['known_store_anchor_count'], 2)

    def test_no_modified_game_artifacts(self):
        report = p45.review_from_decoded(fixture_instructions(), verified_fixture())
        self.assertFalse(report['verification']['steering_handling_patch_produced'])
        self.assertFalse(report['verification']['source_binary_embedded_in_report'])


class ExactSourceTests(unittest.TestCase):
    def test_real_authenticator_rejects_fake(self):
        with self.assertRaises(ValueError):
            p45.audit_exact_source(dummy_full_function())

    def test_verify_before_disassembly(self):
        with patch.object(p45, 'extract_from_verified_image',
                          side_effect=ValueError('wrong SHA')), \
             patch.object(p45, 'disassemble') as disassembler:
            with self.assertRaisesRegex(ValueError, 'wrong SHA'):
                p45.audit_exact_source(b'fake')
            disassembler.assert_not_called()

    def test_mocked_gate_synthetic_whole_function(self):
        raw = dummy_full_function()
        with patch.object(p45, 'extract_from_verified_image',
                          return_value=verified_fixture()), \
             patch.object(p45, 'sections', return_value=[]), \
             patch.object(p45, 'at', return_value=raw):
            report = p45.audit_exact_source(b'synthetic')
        self.assertEqual(report['overview']['known_store_anchor_count'], 2)
        self.assertGreater(report['overview']['decoded_function_instructions'], 600)

    def test_incomplete_function_rejected(self):
        with patch.object(p45, 'extract_from_verified_image',
                          return_value=verified_fixture()), \
             patch.object(p45, 'sections', return_value=[]), \
             patch.object(p45, 'at', return_value=b'\x90'), \
             patch.object(p45, 'disassemble',
                          return_value=fixture_instructions()):
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                p45.audit_exact_source(b'synthetic')

    def test_corrupt_anchor_rejected_after_mocked_gate(self):
        raw = bytearray(dummy_full_function())
        raw[p45.ANCHOR_ADDRESSES[0] - p45.STEERING_START] = 0x90
        with patch.object(p45, 'extract_from_verified_image',
                          return_value=verified_fixture()), \
             patch.object(p45, 'sections', return_value=[]), \
             patch.object(p45, 'at', return_value=bytes(raw)):
            with self.assertRaises(ValueError):
                p45.audit_exact_source(b'synthetic')

    def test_cli_rejects_invalid_exe_without_report(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / 'NFSC.exe'
            output = Path(folder) / 'phase45.json'
            exe.write_bytes(b'not Carbon PC')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                p45.main([str(exe), '--output', str(output)])
            self.assertEqual(err.exception.code, 1)
            self.assertFalse(output.exists())

    def test_cli_missing_file_without_report(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / 'missing'
            output = Path(folder) / 'result.json'
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                p45.main([str(exe), '--output', str(output)])
            self.assertFalse(output.exists())

    def test_output_does_not_replace_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / 'NFSC.exe'
            exe.write_bytes(b'preserve')
            with self.assertRaises(ValueError):
                p45.save_report(exe, '{}', True, exe)
            self.assertEqual(exe.read_bytes(), b'preserve')

    def test_output_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / 'NFSC.exe'
            output = Path(folder) / 'report.json'
            exe.write_bytes(b'preserve')
            output.write_text('old', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                p45.save_report(output, '{}', False, exe)
            self.assertEqual(output.read_text(encoding='utf-8'), 'old')


if __name__ == '__main__':
    unittest.main()
