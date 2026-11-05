"""Source-free Phase 39 regression tests for provenance triage and fail-closed I/O."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steering_state_triage import (
    ANCHOR_LABELS, REGIONS, compare_reports, label_regions,
    main, provenance_signature, unresolved_leaves,
)


ROOT_UNKNOWN = {'kind': 'block_live_in_unknown', 'register': 'r4',
                'block_start_pc': '0x00001000'}
ROOT_LUI = {'kind': 'lui', 'upper_immediate': 0x1234}


def row(pc, offset, label='', direction='read', mnemonic='lwc1', provenance=None):
    return {'pc': f'0x{pc:08X}', 'mnemonic': mnemonic,
            'signed_displacement': offset, 'evidence_label': label,
            'direction': direction, 'base_register': 'r4',
            'base_provenance': copy.deepcopy(ROOT_UNKNOWN if provenance is None else provenance)}


def fixture(build, extras=()):
    anchors = [
        row(0x1020, 0x8c, ANCHOR_LABELS[0]),
        row(0x1040, 0x8c, ANCHOR_LABELS[1]),
        row(0x1080, 0x19c, ANCHOR_LABELS[2], 'write', 'swc1'),
        row(0x10a0, 0x188, ANCHOR_LABELS[3], 'write', 'swc1'),
    ]
    return {'build': build, 'sha256': '0' * 64,
            'candidate_accesses': sorted(anchors + list(extras), key=lambda r: int(r['pc'], 16))}


class ProvenanceTests(unittest.TestCase):
    def test_live_in_unknown(self):
        self.assertEqual(provenance_signature(ROOT_UNKNOWN), ('block_live_in_unknown',))
        self.assertEqual(unresolved_leaves(ROOT_UNKNOWN), ['block_live_in_unknown'])

    def test_architectural_zero_not_unknown(self):
        self.assertEqual(unresolved_leaves({'kind': 'architectural_zero'}), [])

    def test_lui_ignores_relocation(self):
        a = {'kind': 'lui', 'upper_immediate': 0x1234}
        b = {'kind': 'lui', 'upper_immediate': 0x5678}
        self.assertEqual(provenance_signature(a), provenance_signature(b))

    def test_local_load_preserves_offset(self):
        a = {'kind': 'load', 'displacement': 0x24, 'address_base': ROOT_UNKNOWN}
        b = {'kind': 'load', 'displacement': 0x30, 'address_base': ROOT_UNKNOWN}
        self.assertNotEqual(provenance_signature(a), provenance_signature(b))

    def test_local_load_keeps_unknown_leaf(self):
        a = {'kind': 'load', 'displacement': 0x24, 'address_base': ROOT_UNKNOWN}
        self.assertEqual(unresolved_leaves(a), ['block_live_in_unknown'])

    def test_addiu_source_chain(self):
        a = {'kind': 'addiu', 'immediate': 12, 'source': ROOT_UNKNOWN}
        self.assertEqual(unresolved_leaves(a), ['block_live_in_unknown'])

    def test_two_input_binary(self):
        a = {'kind': 'binary', 'sources': [ROOT_UNKNOWN, {'kind': 'architectural_zero'}]}
        self.assertEqual(unresolved_leaves(a), ['block_live_in_unknown'])

    def test_binary_requires_two_sources(self):
        with self.assertRaises(ValueError):
            provenance_signature({'kind': 'binary', 'sources': [ROOT_UNKNOWN]})

    def test_unknown_opcode_rejected(self):
        with self.assertRaises(ValueError):
            unresolved_leaves({'kind': 'imaginary_trace'})

    def test_partial_load_is_unknown(self):
        a = {'kind': 'partial_load_unknown', 'register': 'r4'}
        self.assertEqual(unresolved_leaves(a), ['partial_load_unknown'])

    def test_bounded_recursion(self):
        a = ROOT_UNKNOWN
        for i in range(40):
            a = {'kind': 'move', 'source': a}
        with self.assertRaises(ValueError):
            provenance_signature(a)


class RegionTests(unittest.TestCase):
    def test_empty_regions(self):
        r = label_regions(fixture('undercover_ps2'))
        self.assertEqual(list(r), list(REGIONS))
        self.assertTrue(all(not v for v in r.values()))

    def test_all_five_regions(self):
        extras = [row(0x1010, 0x48), row(0x1030, 0x64), row(0x1070, 0x9c),
                  row(0x1090, 0xc0), row(0x10b0, 0xd8)]
        r = label_regions(fixture('undercover_ps2', extras))
        self.assertEqual([len(r[name]) for name in REGIONS], [1, 1, 1, 1, 1])

    def test_anchor_missing(self):
        r = fixture('undercover_ps2')
        r['candidate_accesses'].pop(0)
        with self.assertRaises(ValueError):
            label_regions(r)

    def test_wrong_anchor_offset(self):
        r = fixture('undercover_ps2')
        r['candidate_accesses'][0]['signed_displacement'] = 0x90
        with self.assertRaises(ValueError):
            label_regions(r)

    def test_wrong_anchor_direction(self):
        r = fixture('undercover_ps2')
        r['candidate_accesses'][2]['direction'] = 'read'
        with self.assertRaises(ValueError):
            label_regions(r)

    def test_duplicate_pc_fails(self):
        r = fixture('undercover_ps2', [row(0x1040, 0x48)])
        with self.assertRaises(ValueError):
            label_regions(r)

    def test_out_of_order_fails(self):
        r = fixture('undercover_ps2', [row(0x1010, 0x48)])
        r['candidate_accesses'][0], r['candidate_accesses'][1] = r['candidate_accesses'][1], r['candidate_accesses'][0]
        with self.assertRaises(ValueError):
            label_regions(r)


class TriageTests(unittest.TestCase):
    def test_identical_empty_reports_no_review(self):
        r = compare_reports(fixture('undercover_ps2'), fixture('carbon_ps2'))
        self.assertEqual(r['candidate_review_count'], 0)
        self.assertEqual(len(r['regions']), 5)

    def test_uc_only_shape(self):
        u = fixture('undercover_ps2', [row(0x1060, 0x48)])
        r = compare_reports(u, fixture('carbon_ps2'))
        self.assertEqual(r['manual_review_queue'][0]['classification'],
                         'instruction_shape_count_difference')
        self.assertEqual(r['manual_review_queue'][0]['undercover_pc'], ['0x00001060'])

    def test_carbon_only_shape(self):
        c = fixture('carbon_ps2', [row(0x1060, 0x48)])
        r = compare_reports(fixture('undercover_ps2'), c)
        self.assertEqual(r['manual_review_queue'][0]['carbon_count'], 1)

    def test_equal_shape_different_provenance(self):
        u = fixture('undercover_ps2', [row(0x1060, 0x48, provenance=ROOT_LUI)])
        c = fixture('carbon_ps2', [row(0x1060, 0x48)])
        r = compare_reports(u, c)
        self.assertEqual(r['manual_review_queue'][0]['classification'],
                         'local_provenance_shape_difference')

    def test_same_shape_unknown_register_names_ignored(self):
        u = fixture('undercover_ps2', [row(0x1060, 0x48)])
        c = fixture('carbon_ps2', [row(0x1060, 0x48)])
        c['candidate_accesses'][2]['base_provenance']['register'] = 'r27'
        self.assertEqual(compare_reports(u, c)['candidate_review_count'], 0)

    def test_repeated_shapes_flag_ambiguity(self):
        u = fixture('undercover_ps2', [row(0x1050, 0x48), row(0x1060, 0x48)])
        c = fixture('carbon_ps2', [row(0x1060, 0x48)])
        q = compare_reports(u, c)['manual_review_queue'][0]
        self.assertTrue(q['repeated_pattern_ambiguity'])

    def test_unresolved_aggregation(self):
        u = fixture('undercover_ps2', [row(0x1060, 0x48)])
        r = compare_reports(u, fixture('carbon_ps2'))
        self.assertEqual(r['regions'][2]['undercover_unresolved_bases'], 1)
        self.assertIn('block_live_in_unknown', r['manual_review_queue'][0]['undercover_unresolved_roots'])

    def test_wrong_build_order(self):
        with self.assertRaises(ValueError):
            compare_reports(fixture('carbon_ps2'), fixture('undercover_ps2'))

    def test_output_avoids_object_equivalence_claim(self):
        r = compare_reports(fixture('undercover_ps2'), fixture('carbon_ps2'))
        self.assertIn('NOT', r['scope_warning'])
        self.assertNotIn('same_object', json.dumps(r))


class CLITests(unittest.TestCase):
    def test_sha_failure_has_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / 'unsupported.elf'
            dst = Path(d) / 'phase39.json'
            exe.write_bytes(b'invalid PS2 binary')
            with self.assertRaises(SystemExit) as thrown:
                main(['--uc', str(exe), '--carbon', str(exe), '--output', str(dst)])
            self.assertEqual(thrown.exception.code, 1)
            self.assertFalse(dst.exists())

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / 'stub'
            dst = Path(d) / 'existing.json'
            exe.write_bytes(b'fixture')
            dst.write_text('existing', encoding='utf8')
            responses = [fixture('undercover_ps2'), fixture('carbon_ps2')]
            with patch('steering_state_triage.audit_source_file', side_effect=responses):
                with self.assertRaises(SystemExit):
                    main(['--uc', str(exe), '--carbon', str(exe), '--output', str(dst)])
            self.assertEqual(dst.read_text(encoding='utf8'), 'existing')

    def test_synthetic_cli_creates_json(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / 'stub'
            dst = Path(d) / 'new.json'
            exe.write_bytes(b'fixture')
            responses = [fixture('undercover_ps2'), fixture('carbon_ps2')]
            with patch('steering_state_triage.audit_source_file', side_effect=responses):
                self.assertEqual(main(['--uc', str(exe), '--carbon', str(exe), '--output', str(dst)]), 0)
            self.assertEqual(json.loads(dst.read_text(encoding='utf8'))['phase'], 39)


if __name__ == '__main__':
    unittest.main()
