"""Source-free tests; fake PE fixture is NEVER treated as authenticated game data."""
from __future__ import annotations

import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carbon_pc_store_audit as phase40


def fake_pe32(anchor_bytes=True):
    """Tiny deliberately non-game PE32 section for mapping tests only."""
    blob = bytearray(0x1800)
    blob[:2] = b'MZ'
    struct.pack_into('<I', blob, 0x3c, 0x80)
    blob[0x80:0x84] = b'PE\x00\x00'
    struct.pack_into('<H', blob, 0x80 + 6, 1)
    struct.pack_into('<H', blob, 0x80 + 20, 0xe0)
    struct.pack_into('<H', blob, 0x80 + 24, 0x10b)
    struct.pack_into('<I', blob, 0x80 + 52, 0x400000)
    sh = 0x80 + 24 + 0xe0
    struct.pack_into('<IIII', blob, sh + 8, 0x1000, 0x2ef000, 0x1000, 0x200)
    if anchor_bytes:
        for pc in phase40.ANCHOR_ADDRESSES:
            off = 0x200 + pc - 0x6ef000
            b = bytes.fromhex(phase40.BYTES[pc])
            blob[off:off + len(b)] = b
    return bytes(blob)


class DecodeTests(unittest.TestCase):
    def test_first_verified_esi_store(self):
        row = phase40.decode_mov_store(bytes.fromhex('898604010000'), 0x6ef7b9)
        self.assertEqual((row['base_register'], row['source_register'], row['signed_displacement']),
                         ('esi', 'eax', 0x104))

    def test_second_verified_esi_store(self):
        row = phase40.decode_mov_store(bytes.fromhex('899618010000'), 0x6ef7c0)
        self.assertEqual((row['base_register'], row['source_register'], row['signed_displacement']),
                         ('esi', 'edx', 0x118))

    def test_relative_instruction_positions(self):
        row = phase40.decode_mov_store(bytes.fromhex('898604010000'), 0x6ef7b9)
        self.assertEqual(row['relative_steering_address'], '+0x279')

    def test_syntactic_not_semantic_destination(self):
        row = phase40.decode_mov_store(bytes.fromhex('898604010000'), 0x6ef7b9)
        self.assertEqual(row['syntactic_destination'], '[esi+0x104]')
        self.assertEqual(row['field_identity'], 'unverified')

    def test_signed_negative_displacement(self):
        word = b'\x89\x85' + struct.pack('<i', -8)
        row = phase40.decode_mov_store(word, 0x1000)
        self.assertEqual((row['base_register'], row['signed_displacement']), ('ebp', -8))

    def test_signed_high_displacement(self):
        row = phase40.decode_mov_store(b'\x89\x86' + struct.pack('<i', 0x7fffffff), 0x1000)
        self.assertEqual(row['signed_displacement'], 0x7fffffff)

    def test_reject_wrong_opcode(self):
        with self.assertRaises(ValueError):
            phase40.decode_mov_store(b'\x8b\x86\x04\x01\x00\x00', 0x1000)

    def test_reject_sib(self):
        with self.assertRaises(ValueError):
            phase40.decode_mov_store(b'\x89\x84\x04\x01\x00\x00', 0x1000)

    def test_reject_register_only(self):
        with self.assertRaises(ValueError):
            phase40.decode_mov_store(b'\x89\xc6\x04\x01\x00\x00', 0x1000)

    def test_reject_disp8(self):
        with self.assertRaises(ValueError):
            phase40.decode_mov_store(b'\x89\x46\x04\x00\x00\x00', 0x1000)

    def test_reject_truncated(self):
        with self.assertRaises(ValueError):
            phase40.decode_mov_store(b'\x89\x86\x04\x01\x00', 0x1000)

    def test_width_and_direction(self):
        row = phase40.decode_mov_store(bytes.fromhex('899618010000'), 0x6ef7c0)
        self.assertEqual((row['width_bits'], row['direction']), (32, 'write'))


class SourceGateTests(unittest.TestCase):
    def test_real_phase31_verifier_rejects_fake(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            phase40.extract_from_verified_image(fake_pe32())

    def test_missing_pe_bytes_rejected_after_synthetic_gate(self):
        with patch.object(phase40, 'verify', return_value={
            'sha256': 'SYNTHETIC_NOT_REAL', 'function': '0x006EF540', 'passed_checks': 17,
        }):
            with self.assertRaisesRegex(ValueError, 'anchored instruction mismatch'):
                phase40.extract_from_verified_image(fake_pe32(False))

    def test_synthetic_end_to_end_decode_with_explicit_mock(self):
        # Verifier mocked ONLY for synthetic decoder tests. Real CLI is not mocked.
        with patch.object(phase40, 'verify', return_value={
            'sha256': 'SYNTHETIC_NOT_REAL', 'function': '0x006EF540', 'passed_checks': 17,
        }):
            result = phase40.extract_from_verified_image(fake_pe32())
        self.assertEqual(result['anchor_count'], 2)
        self.assertEqual(result['known_steering_store_instructions'][0]['signed_displacement'], 0x104)
        self.assertEqual(result['known_steering_store_instructions'][1]['signed_displacement'], 0x118)
        self.assertFalse(result['ps2_field_equivalence_verified'])
        self.assertFalse(result['semantic_field_names_verified'])
        self.assertFalse(result['gameplay_patch_created'])

    def test_synthetic_pe_section_corruption_rejected(self):
        raw = bytearray(fake_pe32())
        raw[0x80:0x84] = b'BAD!'
        with patch.object(phase40, 'verify', return_value={
            'sha256': 'SYNTHETIC_NOT_REAL', 'function': '0x006EF540', 'passed_checks': 17,
        }):
            with self.assertRaises(ValueError):
                phase40.extract_from_verified_image(bytes(raw))

    def test_anchors_inside_verified_function(self):
        self.assertTrue(all(phase40.STEERING_START <= p
                            and p + 6 <= phase40.STEERING_END
                            for p in phase40.ANCHOR_ADDRESSES))

    def test_source_bytes_independently_match_decoder(self):
        for pc in phase40.ANCHOR_ADDRESSES:
            with self.subTest(pc=pc):
                row = phase40.decode_mov_store(bytes.fromhex(phase40.BYTES[pc]), pc)
                self.assertEqual(row['base_register'], 'esi')


class CLISafetyTests(unittest.TestCase):
    def test_bad_exe_no_report(self):
        with tempfile.TemporaryDirectory() as d:
            source, report = Path(d) / 'NFSC.exe', Path(d) / 'report.json'
            source.write_bytes(fake_pe32())
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                phase40.main([str(source), '--output', str(report)])
            self.assertEqual(cm.exception.code, 1)
            self.assertFalse(report.exists())

    def test_missing_exe_no_report(self):
        with tempfile.TemporaryDirectory() as d:
            source, report = Path(d) / 'nonexistent', Path(d) / 'report.json'
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                phase40.main([str(source), '--output', str(report)])
            self.assertFalse(report.exists()

    def test_output_cannot_replace_source(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'NFSC.exe'
            source.write_bytes(b'do-not-overwrite')
            with self.assertRaisesRegex(ValueError, 'must not equal'):
                phase40.save_report(source, '{}', True, source)
            self.assertEqual(source.read_bytes(), b'do-not-overwrite')

    def test_symlink_to_source_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'NFSC.exe'
            link = Path(d) / 'alias.json'
            source.write_bytes(b'precious')
            link.symlink_to(source)
            with self.assertRaises(ValueError):
                phase40.save_report(link, '{}', True, source)
            self.assertEqual(source.read_bytes(), b'precious')

    def test_exclusive_output_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'NFSC.exe'
            output = Path(d) / 'report.json'
            source.write_bytes(b'local')
            output.write_text('old', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                phase40.save_report(output, '{}', False, source)
            self.assertEqual(output.read_text(), 'old')

    def test_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'NFSC.exe'
            output = Path(d) / 'report.json'
            source.write_bytes(b'local')
            output.write_text('old', encoding='utf-8')
            phase40.save_report(output, '{}', True, source)
            self.assertEqual(output.read_text(), '{}')

    def test_json_schema_serializable(self):
        with patch.object(phase40, 'verify', return_value={
            'sha256': 'SYNTHETIC_NOT_REAL', 'function': '0x006EF540', 'passed_checks': 17,
        }):
            report = phase40.extract_from_verified_image(fake_pe32())
        self.assertEqual(json.loads(json.dumps(report))['phase'], 40)


if __name__ == '__main__':
    unittest.main()
