"""Phase 37 tests use synthetic access lists; no original game data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from physics.phase37.steering_access_alignment import (
    EXPECTED_ANCHORS, anchor_indices, compare, fingerprint, lcs_pairs,
    main, _segment,
)


def row(label='', op='lwc1', offset=0x8c, pc=0x1000, direction='read'):
    return {'pc': f'0x{pc:08X}', 'relative_pc': f'+0x{pc-0x1000:03X}',
            'mnemonic': op, 'direction': direction, 'signed_displacement': offset,
            'candidate_offset': f'+0x{offset:X}', 'evidence_label': label,
            'base_register': 'r4', 'target_register': 'f1'}


def report(build, extras=()):
    labels = [row('chassis_input', pc=0x1000),
              row('chassis_input', pc=0x1010),
              row('racer_shaped_input_write', 'swc1', 0x19c, 0x1020, 'write'),
              row('racer_steering_write', 'swc1', 0x188, 0x1030, 'write')]
    # Additional access rows inserted before the first verified anchor.
    return {'build': build, 'source_sha256': '0'*64,
            'accesses': [*extras, *labels]}


class AlignmentTests(unittest.TestCase):
    def test_exact_equal(self):
        self.assertEqual(lcs_pairs([row()], [row()]), [(0, 0)])

    def test_mnemonic_difference_unmatched(self):
        self.assertEqual(lcs_pairs([row(op='lw')], [row(op='lwc1')]), [])

    def test_displacement_difference_unmatched(self):
        self.assertEqual(lcs_pairs([row(offset=8)], [row(offset=16)]), [])

    def test_registers_ignored_for_shape(self):
        other = row()
        other['base_register'] = 'r28'
        self.assertEqual(fingerprint(row()), fingerprint(other))

    def test_subsequence(self):
        a = [row(offset=1), row(offset=2), row(offset=3)]
        b = [row(offset=1), row(offset=3)]
        self.assertEqual(lcs_pairs(a, b), [(0, 0), (2, 1)])

    def test_cross_order_does_not_align_both(self):
        a = [row(offset=1), row(offset=2)]
        b = [row(offset=2), row(offset=1)]
        self.assertEqual(len(lcs_pairs(a, b)), 1)

    def test_repeats_flagged(self):
        a = [row(offset=1), row(offset=1)]
        b = [row(offset=1)]
        self.assertTrue(_segment(a, b, 'synthetic')['paired_static_shapes'][0]['repeated_shape'])

    def test_input_bounds(self):
        with self.assertRaises(ValueError):
            lcs_pairs([row()] * 1025, [])

    def test_empty_sequences(self):
        self.assertEqual(lcs_pairs([], []), [])
        self.assertEqual(lcs_pairs([row()], []), [])

    def test_no_anchors_rejected(self):
        with self.assertRaises(ValueError):
            anchor_indices({'build': 'uc', 'accesses': [row()]})

    def test_anchor_order_rejected(self):
        r = report('undercover_ps2')
        r['accesses'].reverse()
        with self.assertRaises(ValueError):
            anchor_indices(r)

    def test_missing_candidate_anchor_rejected(self):
        r = report('undercover_ps2')
        r['accesses'][0]['candidate_offset'] = ''
        with self.assertRaises(ValueError):
            anchor_indices(r)

    def test_labels_order(self):
        r = report('undercover_ps2')
        ix = anchor_indices(r)
        self.assertEqual([r['accesses'][x]['evidence_label'] for x in ix], list(EXPECTED_ANCHORS))

    def test_base_comparison_four_anchors(self):
        out = compare(report('undercover_ps2'), report('carbon_ps2'))
        self.assertEqual(out['total_static_shape_pairs'], 4)
        self.assertEqual(len(out['known_anchor_pairs']), 4)
        self.assertEqual(len(out['regions']), 5)

    def test_unpaired_added_uc_instruction(self):
        out = compare(report('undercover_ps2', [row(offset=0x60)]), report('carbon_ps2'))
        self.assertEqual(out['unpaired_undercover'], 1)
        self.assertEqual(out['unpaired_carbon'], 0)

    def test_base_register_mismatch_not_semantic(self):
        u, c = report('undercover_ps2'), report('carbon_ps2')
        for r in c['accesses']:
            r['base_register'] = 'r23'
        out = compare(u, c)
        self.assertIn('Register numbers', out['limitations'][2])

    def test_wrong_build_rejected(self):
        with self.assertRaises(ValueError):
            compare(report('wii'), report('carbon_ps2'))

    def test_changed_anchor_shape_rejected(self):
        u, c = report('undercover_ps2'), report('carbon_ps2')
        c['accesses'][0]['signed_displacement'] = 0x90
        with self.assertRaises(ValueError):
            compare(u, c)

    def test_changed_anchor_direction_rejected(self):
        u, c = report('undercover_ps2'), report('carbon_ps2')
        c['accesses'][0]['direction'] = 'write'
        with self.assertRaises(ValueError):
            compare(u, c)

    def test_output_json_no_raw_words(self):
        out = compare(report('undercover_ps2'), report('carbon_ps2'))
        data = json.dumps(out)
        self.assertNotIn('instruction_word', data)
        self.assertIn('limitations', out)

    def test_original_audit_rejects_unsupported_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fake_elf'
            path.write_bytes(b'unrecognized')
            with self.assertRaises(SystemExit) as ctx:
                main(['--uc', str(path), '--carbon', str(path)])
            self.assertEqual(ctx.exception.code, 1)

    def test_cli_no_output_on_failed_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / 'bad'
            dst = Path(directory) / 'report.json'
            bad.write_bytes(b'not-game-data')
            with self.assertRaises(SystemExit):
                main(['--uc', str(bad), '--carbon', str(bad), '--output', str(dst)])
            self.assertFalse(dst.exists())


if __name__ == '__main__':
    unittest.main()
