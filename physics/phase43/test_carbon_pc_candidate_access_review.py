"""Phase 43 asset-free tests: syntactic local evidence, no game executable."""
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
import carbon_pc_candidate_access_review as phase43
from physics.phase42.carbon_pc_esi_access_census import find_accesses


def ins(pc, data, mnemonic, operands):
    return {'pc': pc, 'length': len(data), 'bytes': data,
            'mnemonic': mnemonic, 'operands': operands}


def example():
    """Three real-encoding synthetic x86 instructions with local adjacency."""
    return [
        ins(0x1000, bytes.fromhex('898604010000'), 'mov',
            'DWORD PTR [esi+0x104],eax'),
        ins(0x1006, bytes.fromhex('8b8604010000'), 'mov',
            'eax,DWORD PTR [esi+0x104]'),
        ins(0x100c, bytes.fromhex('899618010000'), 'mov',
            'DWORD PTR [esi+0x118],edx'),
    ]


def fixture(rows=None):
    rows = example() if rows is None else rows
    evidence = find_accesses(rows)
    return {'source_sha256': 'synthetic-not-an-executable',
            'simple_esi_accesses': evidence['simple_esi_accesses'],
            'simple_esi_access_count': evidence['simple_esi_access_count'],
            'complex_esi_operand_count': evidence['complex_esi_operand_count']}


class InstructionTests(unittest.TestCase):
    def test_valid_contiguous(self):
        index = phase43.validate_instructions(example())
        self.assertEqual(len(index), 3)
        self.assertEqual(index[0x100c]['mnemonic'], 'mov')

    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            phase43.validate_instructions([])

    def test_reject_gap(self):
        rows = example()
        rows[1]['pc'] += 1
        with self.assertRaises(ValueError):
            phase43.validate_instructions(rows)

    def test_reject_duplicate(self):
        rows = [example()[0], example()[0]]
        with self.assertRaises(ValueError):
            phase43.validate_instructions(rows)

    def test_reject_invalid_length(self):
        rows = example()
        rows[0]['length'] = 0
        with self.assertRaises(ValueError):
            phase43.validate_instructions(rows)

    def test_reject_oversized_instruction(self):
        rows = example()
        rows[0]['length'] = 16
        with self.assertRaises(ValueError):
            phase43.validate_instructions(rows)

    def test_span_requires_real_instruction_boundaries(self):
        with self.assertRaises(ValueError):
            phase43.span_evidence(example(), 0x1001, 0x100c)

    def test_span_requires_ordered_endpoints(self):
        with self.assertRaises(ValueError):
            phase43.span_evidence(example(), 0x100c, 0x1000)


class SpanTests(unittest.TestCase):
    def test_same_block_no_detected_esi_write(self):
        result = phase43.span_evidence(example(), 0x1000, 0x1006)
        self.assertEqual(result['status'], 'no_detected_esi_write_in_same_linear_region')
        self.assertFalse(result['same_runtime_object_proven'])

    def test_nearby_mov_to_esi_causes_barrier(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('89fe'), 'mov', 'esi,edi'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]'),
                ins(0x100e, bytes.fromhex('899618010000'), 'mov',
                    'DWORD PTR [esi+0x118],edx')]
        result = phase43.span_evidence(rows, 0x1000, 0x1008)
        self.assertEqual(result['status'], 'esi_definition_or_implicit_effect')
        self.assertEqual(result['effect'], 'register_copy')

    def test_opaque_xchg_between_barrier(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('87fe'), 'xchg', 'esi,edi'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]')]
        self.assertEqual(phase43.span_evidence(rows, 0x1000, 0x1008)['status'],
                         'unknown_instruction_effect')

    def test_branch_between_accesses_barrier(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('7400'), 'je', '0x1008'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]')]
        result = phase43.span_evidence(rows, 0x1000, 0x1008)
        self.assertEqual(result['status'], 'control_flow_boundary')

    def test_branch_target_into_middle_rejected(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('eb01'), 'jmp', '0x1009'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]')]
        with self.assertRaises(ValueError):
            phase43.span_evidence(rows, 0x1000, 0x1008)

    def test_cmp_in_between_is_safe(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('39d0'), 'cmp', 'eax,edx'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]')]
        self.assertEqual(phase43.span_evidence(rows, 0x1000, 0x1008)['status'],
                         'no_detected_esi_write_in_same_linear_region')

    def test_memory_store_not_esi_register_write(self):
        result = phase43.span_evidence(example(), 0x1000, 0x100c)
        self.assertEqual(result['status'], 'no_detected_esi_write_in_same_linear_region')

    def test_if_branch_target_is_second_access_barrier(self):
        rows = [example()[0],
                ins(0x1006, bytes.fromhex('7400'), 'je', '0x1008'),
                ins(0x1008, bytes.fromhex('8b8604010000'), 'mov',
                    'eax,DWORD PTR [esi+0x104]')]
        self.assertEqual(phase43.span_evidence(rows, 0x1000, 0x1008)['status'],
                         'control_flow_boundary')

    def test_raw_disassembled_synthetic_instructions(self):
        raw = b''.join(x['bytes'] for x in example())
        decoded = phase43.disassemble(raw, 0x1000)
        self.assertEqual(phase43.span_evidence(decoded, 0x1000, 0x1006)['status'],
                         'no_detected_esi_write_in_same_linear_region')


class ReviewTests(unittest.TestCase):
    def test_candidate_reports_read_and_write(self):
        result = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        a, b = result['candidate_offsets']
        self.assertEqual(a['signed_displacement'], 0x104)
        self.assertEqual(a['static_read_occurrences'], 1)
        self.assertEqual(a['static_write_occurrences'], 1)
        self.assertTrue(a['static_read_and_write_shapes_both_present'])
        self.assertEqual(b['static_write_occurrences'], 1)
        self.assertEqual(b['static_read_occurrences'], 0)

    def test_anchor_pair_never_proves_identity(self):
        report = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        self.assertFalse(report['known_anchor_linear_span']['same_runtime_object_proven'])
        self.assertFalse(report['runtime_path_or_object_identity_verified'])

    def test_nearby_context_preserves_other_offset(self):
        result = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        near = result['candidate_offsets'][0]['nearby_esi_access_context'][0]['nearby_explicit_esi_operands']
        self.assertIn(0x118, [r['signed_displacement'] for r in near])

    def test_consecutive_offset_span_uses_esi_evidence(self):
        result = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        span = result['candidate_offsets'][0]['consecutive_same_offset_spans'][0]
        self.assertEqual(span['static_span']['status'],
                         'no_detected_esi_write_in_same_linear_region')

    def test_wrong_census_rejected(self):
        evidence = fixture()
        evidence['simple_esi_accesses'][0]['signed_displacement'] = 0x900
        with self.assertRaisesRegex(ValueError, 'disagree'):
            phase43.build_review(example(), evidence, anchors=(0x1000, 0x100c))

    def test_missing_anchor_rejected(self):
        rows = example()[:2]
        with self.assertRaisesRegex(ValueError, 'anchor'):
            phase43.build_review(rows, fixture(rows), anchors=(0x1000, 0x100c))

    def test_anchor_different_offset_rejected(self):
        rows = example()
        with self.assertRaisesRegex(ValueError, 'anchor'):
            phase43.build_review(rows, fixture(rows), anchors=(0x1000, 0x1006))

    def test_unknown_direction_not_silent_read_or_write(self):
        rows = [example()[0],
                ins(0x1006, b'\x90', 'unknownop', 'DWORD PTR [esi+0x104]'),
                ins(0x1007, example()[2]['bytes'], 'mov',
                    'DWORD PTR [esi+0x118],edx')]
        result = phase43.build_review(rows, fixture(rows), anchors=(0x1000, 0x1007))
        entry = result['candidate_offsets'][0]
        self.assertEqual(entry['unknown_direction_occurrences'], 1)
        self.assertEqual(entry['static_read_occurrences'], 0)

    def test_json_contains_no_executable_bytes(self):
        result = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        payload = json.dumps(result)
        self.assertNotIn('898604010000', payload)
        self.assertFalse(result['gameplay_patch_created'])
        self.assertFalse(result['field_names_verified'])
        self.assertFalse(result['ps2_pc_field_equivalence_verified'])

    def test_instruction_addresses_not_field_names(self):
        result = phase43.build_review(example(), fixture(), anchors=(0x1000, 0x100c))
        self.assertEqual(result['candidate_offsets'][0]['accesses'][0]['pc'], '0x00001000')


class SourceGateTests(unittest.TestCase):
    def test_real_gate_rejects_unknown_bytes(self):
        with self.assertRaises(ValueError):
            phase43.audit_verified_image(b'unsupported version')

    def test_fake_cli_fails_without_report(self):
        with tempfile.TemporaryDirectory() as d:
            exe, output = Path(d) / 'NFSC.exe', Path(d) / 'out.json'
            exe.write_bytes(b'invalid source file')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                phase43.main([str(exe), '--output', str(output)])
            self.assertEqual(ctx.exception.code, 1)
            self.assertFalse(output.exists())

    def test_synthetic_gate_rechecked_against_disassembly(self):
        fixture_report = fixture()
        with patch.object(phase43, 'audit_verified_pc', return_value=fixture_report), \
             patch.object(phase43, 'at', return_value=b'synthetic'), \
             patch.object(phase43, 'sections', return_value=[]), \
             patch.object(phase43, 'disassemble', return_value=example()):
            with self.assertRaisesRegex(ValueError, 'anchor'):
                phase43.audit_verified_image(b'synthetic')

    def test_no_source_access_before_failed_verification(self):
        with patch.object(phase43, 'audit_verified_pc', side_effect=ValueError('bad hash')), \
             patch.object(phase43, 'disassemble') as disassemble:
            with self.assertRaisesRegex(ValueError, 'bad hash'):
                phase43.audit_verified_image(b'invalid')
            disassemble.assert_not_called()


if __name__ == '__main__':
    unittest.main()
