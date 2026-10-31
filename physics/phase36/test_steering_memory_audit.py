"""Synthetic tests for Phase 36. No proprietary game files required."""
import csv
import io
import unittest
from unittest.mock import patch

try:
    from .steering_memory_audit import (
        ANCHORS, audit_original, compare_reports, decode_memory_word,
        output_csv, scan_function,
    )
except ImportError:
    from steering_memory_audit import (
        ANCHORS, audit_original, compare_reports, decode_memory_word,
        output_csv, scan_function,
    )


def iword(opcode, base, target, displacement):
    return ((opcode & 63) << 26) | ((base & 31) << 21) | (
        (target & 31) << 16) | (displacement & 0xffff)


class DecoderTests(unittest.TestCase):
    def test_lwc1_read(self):
        row = decode_memory_word(iword(0x31, 19, 24, 0x8c), 0x408304)
        self.assertEqual((row['mnemonic'], row['direction']), ('lwc1', 'read'))
        self.assertEqual((row['base_register'], row['target_register']),
                         ('r19', 'f24'))

    def test_swc1_write(self):
        row = decode_memory_word(iword(0x39, 19, 24, 0x19c), 0x408708)
        self.assertEqual((row['direction'], row['signed_displacement']),
                         ('write', 0x19c))

    def test_negative_disp(self):
        self.assertEqual(decode_memory_word(iword(0x23, 29, 2, -16), 0)['signed_displacement'], -16)

    def test_zero_disp(self):
        self.assertEqual(decode_memory_word(iword(0x23, 29, 2, 0), 0)['signed_displacement'], 0)

    def test_signed_limit(self):
        self.assertEqual(decode_memory_word(iword(0x23, 29, 2, -32768), 0)['signed_displacement'], -32768)

    def test_unsigned_limit(self):
        self.assertEqual(decode_memory_word(iword(0x23, 29, 2, 32767), 0)['signed_displacement'], 32767)

    def test_non_memory(self):
        self.assertIsNone(decode_memory_word(0x00000000, 0))
        self.assertIsNone(decode_memory_word(0x03e00008, 0))

    def test_invalid_values(self):
        for word, pc in [(-1, 0), (0x100000000, 0), (0, -1)]:
            with self.subTest(word=word, pc=pc), self.assertRaises(ValueError):
                decode_memory_word(word, pc)

    def test_byte_load(self):
        self.assertEqual(decode_memory_word(iword(0x24, 4, 3, 7), 0)['mnemonic'], 'lbu')


class InventoryTests(unittest.TestCase):
    def test_anchor_success(self):
        start = 0x1000
        words = {
            start: iword(0x31, 4, 7, 0x8c),
            start + 4: iword(0x39, 5, 8, 0x188),
        }
        with patch('physics.phase36.steering_memory_audit.word_at',
                   side_effect=lambda data, segments, pc: words[pc]):
            rows = scan_function(b'', [], start, start + 8, {
                start: ('source_input', 0x8c, 'read'),
                start + 4: ('destination', 0x188, 'write'),
            })
        self.assertEqual(len(rows), 2)
        self.assertEqual([x['evidence_label'] for x in rows],
                         ['source_input', 'destination'])

    def test_anchor_wrong_displacement(self):
        with patch('physics.phase36.steering_memory_audit.word_at', return_value=iword(0x31, 4, 7, 0x90)):
            with self.assertRaises(ValueError):
                scan_function(b'', [], 0x1000, 0x1004,
                              {0x1000: ('input', 0x8c, 'read')})

    def test_anchor_wrong_direction(self):
        with patch('physics.phase36.steering_memory_audit.word_at', return_value=iword(0x39, 4, 7, 0x8c)):
            with self.assertRaises(ValueError):
                scan_function(b'', [], 0x1000, 0x1004,
                              {0x1000: ('input', 0x8c, 'read')})

    def test_anchor_non_memory(self):
        with patch('physics.phase36.steering_memory_audit.word_at', return_value=0):
            with self.assertRaises(ValueError):
                scan_function(b'', [], 0x1000, 0x1004,
                              {0x1000: ('input', 0x8c, 'read')})

    def test_bad_bounds(self):
        for start, end in [(0, 0), (4, 0), (1, 8), (0, 5)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                scan_function(b'', [], start, end)

    def test_no_anchors_not_labeled(self):
        with patch('physics.phase36.steering_memory_audit.word_at', return_value=iword(0x31, 4, 7, 0x8c)):
            rows = scan_function(b'', [], 0x1000, 0x1004)
        self.assertEqual(rows[0]['candidate_offset'], '+0x8C')
        self.assertEqual(rows[0]['evidence_label'], '')

    def test_unknown_build_fails(self):
        with self.assertRaises(ValueError):
            audit_original(b'', 'wrong')

    def test_sha_mismatch_fails(self):
        with self.assertRaises(ValueError):
            audit_original(b'not a PS2 executable', 'undercover_ps2')


class ReportTests(unittest.TestCase):
    @staticmethod
    def row(pc, disp, label=''):
        return dict(pc=pc, relative_pc='+0x000', mnemonic='lwc1',
                    direction='read', base_register='r4', target_register='f1',
                    signed_displacement=disp, candidate_offset='',
                    evidence_label=label)

    def reports(self):
        return (
            {'build': 'undercover_ps2', 'accesses': [self.row('0x1', 0x8c, 'chassis_input')], 'static_memory_operations': 1},
            {'build': 'carbon_ps2', 'accesses': [self.row('0x2', 0x8c)], 'static_memory_operations': 1}
        )

    def test_compare_counts(self):
        a, b = self.reports()
        comparison = compare_reports(a, b)
        item = next(x for x in comparison['offset_comparison']
                    if x['numeric_displacement'] == '+0x8C')
        self.assertEqual(item['undercover_ps2']['anchored_count'], 1)
        self.assertEqual(item['carbon_ps2']['anchored_count'], 0)

    def test_comparison_rejects_wrong_order(self):
        a, b = self.reports()
        with self.assertRaises(ValueError):
            compare_reports(b, a)

    def test_csv_parseable(self):
        a, b = self.reports()
        rows = list(csv.DictReader(io.StringIO(output_csv({'builds': [a, b]}))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['evidence_label'], 'chassis_input')

    def test_comparison_preserves_unseen(self):
        a, b = self.reports()
        item = next(x for x in compare_reports(a, b)['offset_comparison']
                    if x['numeric_displacement'] == '+0x160')
        self.assertEqual(item['undercover_ps2']['count'], 0)

    def test_expected_anchors_present(self):
        self.assertEqual(len(ANCHORS['undercover_ps2']), 4)
        self.assertEqual(len(ANCHORS['carbon_ps2']), 4)


if __name__ == '__main__':
    unittest.main()
