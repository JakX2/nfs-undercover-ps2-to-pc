"""Phase 42 synthetic-only tests: no original executables or game assets."""
from __future__ import annotations

import io
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carbon_pc_esi_access_census as phase42


def ins(pc, mnemonic, operands, blob=b'\x90'):
    return {'pc': pc, 'mnemonic': mnemonic, 'operands': operands,
            'bytes': blob, 'length': len(blob)}


class AddressParsingTests(unittest.TestCase):
    def test_esi_plus_hex(self):
        row = phase42.parse_mem_operand('DWORD PTR [esi+0x104]')
        self.assertEqual(row, {'kind': 'simple', 'base_register': 'esi',
                               'signed_displacement': 0x104})

    def test_esi_negative_hex(self):
        self.assertEqual(phase42.parse_mem_operand('QWORD PTR [esi-0x20]')['signed_displacement'], -0x20)

    def test_esi_zero(self):
        self.assertEqual(phase42.parse_mem_operand('[esi]')['signed_displacement'], 0)

    def test_esi_decimal(self):
        self.assertEqual(phase42.parse_mem_operand('BYTE PTR [esi+16]')['signed_displacement'], 16)

    def test_ebp_not_esi(self):
        self.assertEqual(phase42.parse_mem_operand('DWORD PTR [ebp-0x8]')['base_register'], 'ebp')

    def test_upper_case(self):
        self.assertEqual(phase42.parse_mem_operand('DWORD PTR [ESI+0X104]')['signed_displacement'], 0x104)

    def test_scaled_index_complex(self):
        row = phase42.parse_mem_operand('DWORD PTR [esi+ecx*4+0x20]')
        self.assertEqual(row['kind'], 'complex')

    def test_esi_plus_other_register_complex(self):
        self.assertEqual(phase42.parse_mem_operand('[esi+eax]')['kind'], 'complex')

    def test_large_signed_displacement_complex(self):
        self.assertEqual(phase42.parse_mem_operand('[esi+0xffffffff]')['kind'], 'complex')

    def test_unsupported_segment_not_simplified(self):
        self.assertIsNone(phase42.parse_mem_operand('DWORD PTR fs:[esi+0x10]'))

    def test_register_not_memory(self):
        self.assertIsNone(phase42.parse_mem_operand('eax'))

    def test_invalid_bracket_excluded(self):
        self.assertIsNone(phase42.parse_mem_operand('[esi+0x10'))

    def test_other_pointer_width(self):
        self.assertEqual(phase42.parse_mem_operand('XMMWORD PTR [esi+0x20]')['kind'], 'simple')


class ClassificationTests(unittest.TestCase):
    def test_mov_destination_write(self):
        self.assertEqual(phase42.access_direction('mov', 0, 2), 'write')

    def test_mov_source_read(self):
        self.assertEqual(phase42.access_direction('mov', 1, 2), 'read')

    def test_lea_is_not_memory_access(self):
        self.assertEqual(phase42.access_direction('lea', 1, 2),
                         'address_only_no_memory_access')

    def test_cmp_memory_read(self):
        self.assertEqual(phase42.access_direction('cmp', 0, 2), 'read')

    def test_add_memory_read_write(self):
        self.assertEqual(phase42.access_direction('add', 0, 2), 'read_write')

    def test_fstp_write(self):
        self.assertEqual(phase42.access_direction('fstp', 0, 1), 'write')

    def test_fld_read(self):
        self.assertEqual(phase42.access_direction('fld', 0, 1), 'read')

    def test_unmodelled_operation_unknown(self):
        self.assertEqual(phase42.access_direction('weirdop', 0, 2), 'unknown')

    def test_push_memory_read(self):
        self.assertEqual(phase42.access_direction('push', 0, 1), 'read')

    def test_pop_memory_write(self):
        self.assertEqual(phase42.access_direction('pop', 0, 1), 'write')

    def test_xchg_read_write(self):
        self.assertEqual(phase42.access_direction('xchg', 0, 2), 'read_write')


class InventoryTests(unittest.TestCase):
    def test_two_known_anchor_stores(self):
        rows = [
            ins(0x6ef7b9, 'mov', 'DWORD PTR [esi+0x104],eax'),
            ins(0x6ef7c0, 'mov', 'DWORD PTR [esi+0x118],edx'),
        ]
        result = phase42.find_accesses(rows)
        self.assertEqual(result['simple_esi_access_count'], 2)
        self.assertEqual([x['signed_displacement'] for x in result['simple_esi_accesses']],
                         [0x104, 0x118])
        self.assertTrue(all(x['known_phase40_anchor'] for x in result['simple_esi_accesses']))

    def test_lea_excluded(self):
        result = phase42.find_accesses([ins(0x1000, 'lea', 'eax,[esi+0x20]')])
        self.assertEqual(result['simple_esi_access_count'], 0)

    def test_other_base_excluded(self):
        result = phase42.find_accesses([ins(0x1000, 'mov', 'eax,DWORD PTR [edi+0x104]')])
        self.assertEqual(result['simple_esi_access_count'], 0)

    def test_complex_esi_counted_separately(self):
        result = phase42.find_accesses([ins(0x1000, 'mov', 'eax,DWORD PTR [esi+ecx*4+0x10]')])
        self.assertEqual(result['simple_esi_access_count'], 0)
        self.assertEqual(result['complex_esi_operand_count'], 1)

    def test_complex_other_base_excluded(self):
        result = phase42.find_accesses([ins(0x1000, 'mov', 'eax,DWORD PTR [edi+ecx*4+0x10]')])
        self.assertEqual(result['complex_esi_operand_count'], 0)

    def test_unparsed_segment_visible(self):
        result = phase42.find_accesses([ins(0x1000, 'mov', 'eax,DWORD PTR fs:[esi]')])
        self.assertEqual(result['unknown_memory_operand_form_count'], 1)

    def test_unknown_opcode_retained(self):
        result = phase42.find_accesses([ins(0x1000, 'foo', 'DWORD PTR [esi+0x34],eax')])
        self.assertEqual(result['simple_esi_accesses'][0]['direction'], 'unknown')

    def test_groups_static_counts_not_dynamic(self):
        rows = [
            ins(0x1000, 'mov', 'eax,DWORD PTR [esi+0x10]'),
            ins(0x1003, 'mov', 'DWORD PTR [esi+0x10],eax'),
        ]
        result = phase42.find_accesses(rows)
        self.assertEqual(result['by_displacement'][0]['static_instruction_count'], 2)
        self.assertEqual(result['by_displacement'][0]['directions'], ['read', 'write'])

    def test_real_objdump_roundtrip_synthetic(self):
        data = bytes.fromhex('8b46100146108d5610')
        decoded = phase42.disassemble(data, 0x1000)
        result = phase42.find_accesses(decoded)
        self.assertEqual(result['simple_esi_access_count'], 2)
        self.assertEqual(result['by_displacement'][0]['directions'], ['read', 'read_write'])


class VerificationTests(unittest.TestCase):
    def test_real_phase40_gate_rejects_fake_binary(self):
        with self.assertRaises(ValueError):
            phase42.audit_verified_pc(b'not an executable')

    def test_synthetic_mocked_extraction_requires_two_decoded_anchors(self):
        synthetic = [ins(0x6ef7b9, 'mov', 'DWORD PTR [esi+0x104],eax',
                         bytes.fromhex('898604010000'))]
        with patch.object(phase42, 'extract_from_verified_image', return_value={
            'exe_sha256': 'SYNTHETIC_ONLY', 'steering_function_va': '0x006EF540',
            'phase31_verified_checks': 17,
        }), patch.object(phase42, 'sections', return_value=[]), \
                patch.object(phase42, 'at', return_value=b'\x90'), \
                patch.object(phase42, 'disassemble', return_value=synthetic):
            with self.assertRaisesRegex(ValueError, 'anchor'):
                phase42.audit_verified_pc(b'synthetic')

    def test_synthetic_mocked_two_anchors_schema(self):
        synthetic = [
            ins(0x6ef7b9, 'mov', 'DWORD PTR [esi+0x104],eax',
                bytes.fromhex('898604010000')),
            ins(0x6ef7c0, 'mov', 'DWORD PTR [esi+0x118],edx',
                bytes.fromhex('899618010000')),
        ]
        with patch.object(phase42, 'extract_from_verified_image', return_value={
            'exe_sha256': 'SYNTHETIC_ONLY', 'steering_function_va': '0x006EF540',
            'phase31_verified_checks': 17,
        }), patch.object(phase42, 'sections', return_value=[]), \
                patch.object(phase42, 'at', return_value=b'\x90'), \
                patch.object(phase42, 'disassemble', return_value=synthetic):
            report = phase42.audit_verified_pc(b'synthetic')
        self.assertEqual(report['phase'], 42)
        self.assertEqual(report['simple_esi_access_count'], 2)
        self.assertFalse(report['semantic_field_equivalence_established'])
        self.assertFalse(report['runtime_values_observed'])
        self.assertFalse(report['gameplay_patch_created'])

    def test_version_failure_does_not_write_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source, report = Path(directory) / 'NFSC.exe', Path(directory) / 'report.json'
            source.write_bytes(b'unsupported version')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                phase42.main([str(source), '--output', str(report)])
            self.assertFalse(report.exists())


if __name__ == '__main__':
    unittest.main()
