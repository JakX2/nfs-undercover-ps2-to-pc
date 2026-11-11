"""Synthetic-only tests for the read-only first Undercover scene-model gate.

No original game archive, proprietary model or texture is embedded.
"""
import copy
import json
import unittest
from unittest.mock import patch

from undercover_pc_first_model_gate import (
    SOURCE_SECTIONS, MAX_TRIANGLES, rank_candidates,
    verify_single_model, audit_original)
from undercover_pc_geometry_bridge import _new_header
from test_texture_visual_pair_gate import make_pack

A, B, MISSING = 0x11111111, 0x22222222, 0x33333333
MODEL = 0xA0B0C0D0
POSITIONS = ((0., 0., 0.), (1., 0., 0.), (1., 1., 0.), (0., 1., 0.))
UV = ((0., 0.), (1., 0.), (1., 1.), (0., 1.))
FACES = ((0, 1, 2), (0, 2, 3))
LABELS = (0, 1)


def row(identity, table=(A,), triangles=5):
    return (identity, b'SYNTHETIC_HEADER', tuple(table), ((0, triangles),))


def packs(*rows):
    if len(rows) > 4:
        raise ValueError('Too many synthetic groups')
    default = tuple(row(0x1000 + i, (A,), i + 4) for i in range(4))
    return tuple((rows[i] if i < len(rows) else default[i],) for i in range(4))


def budget(platform, texture_count):
    return {'per_texture': {0: platform[0][1]}, 'triangles': platform[0][1]}


_DEFAULT = object()


def rank(data=None, images=_DEFAULT, refs=_DEFAULT, **kwargs):
    g = data if data is not None else packs(
        row(0x1001, (A, B), 7),
        row(0x1002, (A,), 5),
        row(0x1003, (A,), 9),
        row(0x1004, (A,), 6))
    return rank_candidates(g, {A, B} if images is _DEFAULT else images,
                           (0x1001, 0x1002, 0x1003, 0x1004) if refs is _DEFAULT else refs,
                           241, budget_fn=budget, **kwargs)


def selected():
    return {
        'identity': MODEL, 'header': _new_header(MODEL, 2),
        'table': (A, B), 'platform': ((0, 2),),
        'section': 241, 'pack_ordinal': 2, 'model_ordinal': 0,
        'triangles': 2, 'source_material_budget': {0: 1, 1: 1},
        'scene_reference_count': 1,
    }


class RankingTests(unittest.TestCase):
    def test_sorts_smallest_first(self):
        rows, stats = rank()
        self.assertEqual([r['triangles'] for r in rows], [5, 6, 7, 9])
        self.assertEqual(stats['indexed_model_occurrences'], 4)
        self.assertEqual(stats['eligible_candidate_models'], 4)

    def test_stable_order_under_equal_triangle_count(self):
        g = packs(row(0x1001, (A,), 5), row(0x1002, (A,), 5),
                  row(0x1003, (A,), 9), row(0x1004, (A,), 6))
        got, _ = rank(data=g, refs=(0x1001, 0x1001, 0x1002, 0x1003, 0x1004))
        self.assertEqual(got[0]['identity'], 0x1001)
        self.assertEqual(got[0]['scene_reference_count'], 2)

    def test_full_material_table_required_even_if_some_slots_unused(self):
        g = packs(row(0x1000, (A, MISSING), 5))
        got, stats = rank(data=g, images={A}, refs=(0x1000,))
        self.assertFalse(any(r['identity'] == 0x1000 for r in got))
        self.assertEqual(stats['unbacked_full_material_tables'], 1)

    def test_unreferenced_models_excluded(self):
        got, stats = rank(refs=(0x1002,))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]['identity'], 0x1002)
        self.assertEqual(stats['not_primary_scenery_referenced'], 3)

    def test_ambiguous_same_section_model_excluded(self):
        g = packs(row(0x1001), row(0x1001), row(0x1003), row(0x1004))
        got, stats = rank(data=g, refs=(0x1001, 0x1003))
        self.assertEqual([x['identity'] for x in got], [0x1003])
        self.assertEqual(stats['ambiguous_local_model_occurrences'], 2)

    def test_max_triangles_window(self):
        got, stats = rank(max_triangles=6)
        self.assertEqual([x['triangles'] for x in got], [5, 6])
        self.assertEqual(stats['outside_candidate_triangle_window'], 2)

    def test_min_triangles_window(self):
        got, _ = rank(min_triangles=8)
        self.assertEqual([x['triangles'] for x in got], [9])

    def test_full_pack_count_required(self):
        with self.assertRaisesRegex(ValueError, 'four original'):
            rank(data=(tuple([row(3)]),) * 3)

    def test_empty_pack_rejected(self):
        with self.assertRaises(ValueError):
            rank(data=((), (row(2),), (row(3),), (row(4),)))

    def test_reject_bad_source_section(self):
        with self.assertRaises(ValueError):
            rank_candidates(packs(), {A}, (0x1001,), 142, budget_fn=budget)

    def test_reject_bad_image_sets(self):
        for bad in (None, [], {}, {True}, {0}, {0x100000000}, set()):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                rank(images=bad)

    def test_reject_bad_scene_references(self):
        for bad in (None, [], {0x1001}, (True,), (0,), (0x100000000,)):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                rank(refs=bad)

    def test_invalid_triangle_windows(self):
        for kw in ({'min_triangles': 0}, {'min_triangles': True},
                   {'max_triangles': 0}, {'max_triangles': MAX_TRIANGLES + 1},
                   {'min_triangles': 100, 'max_triangles': 10}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                rank(**kw)

    def test_invalid_model_row_shape(self):
        g = ([(1, b'short')], [row(2)], [row(3)], [row(4)])
        with self.assertRaises(ValueError):
            rank(data=g)

    def test_boolean_model_hash_rejected(self):
        with self.assertRaises(ValueError):
            rank(data=packs(row(True)))

    def test_invalid_material_hash_rejected(self):
        with self.assertRaises(ValueError):
            rank(data=packs(row(0x1001, (True,))))

    def test_source_budget_mismatch_rejected(self):
        def wrong(platform, count):
            return {'per_texture': {0: 4}, 'triangles': 3}
        with self.assertRaisesRegex(ValueError, 'totals disagree'):
            rank_candidates(packs(), {A}, (0x1000,), 241,
                            budget_fn=wrong)

    def test_material_index_out_of_range_rejected(self):
        def wrong(platform, count):
            return {'per_texture': {count: 5}, 'triangles': 5}
        with self.assertRaisesRegex(ValueError, 'material index'):
            rank_candidates(packs(), {A}, (0x1000,), 241, budget_fn=wrong)

    def test_zero_face_candidate_rejected(self):
        def zero(platform, count):
            return {'per_texture': {0: 0}, 'triangles': 0}
        with self.assertRaisesRegex(ValueError, 'totals disagree'):
            rank_candidates(packs(), {A}, (0x1000,), 241, budget_fn=zero)

    def test_candidate_stats_do_not_print_hashes(self):
        _, stats = rank()
        encoded = json.dumps(stats)
        for hidden in ('286331153', '572662306', '4097', '4098'):
            self.assertNotIn(hidden, encoded)


class SingleModelRoundtripTests(unittest.TestCase):
    def run_valid(self, rowdata=None, source=None, mip_levels=3,
                  native_geo=None, native_tex=None):
        with patch('triangle_corner_uv_control.ps2_geometry_attributes',
                   return_value=(POSITIONS, UV, FACES, LABELS)):
            return verify_single_model(
                selected() if rowdata is None else rowdata,
                make_pack('ps2', bits=8, hashes=(A, B)) if source is None else source,
                mip_levels=mip_levels,
                native_carbon_geometry_roots=native_geo,
                native_carbon_texture_roots=native_tex)

    def test_full_PC_geometry_and_two_dxt5_images(self):
        out = self.run_valid()
        self.assertTrue(out['native_geometry_and_material_budget_passed'])
        self.assertEqual(out['pc_dxt5_image_records'], 2)
        self.assertEqual(out['original_triangle_count'], 2)
        self.assertEqual(out['generated_pc_triangle_count'], 2)
        self.assertGreater(out['pc_candidate_geometry_bytes_in_memory'], 0)
        self.assertGreater(out['pc_candidate_texture_bytes_in_memory'], 0)

    def test_material_reference_order_preserved(self):
        x = selected()
        x['table'] = (B, A)
        out = self.run_valid(x)
        self.assertTrue(out['all_source_table_image_identities_backed'])

    def test_repeat_source_texture_entry_preserved(self):
        x = selected()
        x['table'] = (A, A)
        out = self.run_valid(x)
        self.assertEqual(out['local_material_table_entries'], 2)
        self.assertEqual(out['distinct_required_image_identities'], 1)
        self.assertEqual(out['pc_dxt5_image_records'], 1)

    def test_no_private_hashes_or_names_in_report(self):
        out = self.run_valid()
        data = json.dumps(out)
        for private in (str(MODEL), str(A), str(B), 'SYNTH_'):
            self.assertNotIn(private, data)
        self.assertEqual(out['native_scene_registration'], 'UNVERIFIED')
        self.assertFalse(out['safe_for_game_install'])
        self.assertFalse(out['game_files_written'])


    def native_roots(self, collision_model=False, collision_texture=False):
        from undercover_pc_geometry_bridge import convert_decoded_ps2_model
        model = MODEL if collision_model else 0xAAAA5678
        native_tex = A if collision_texture else 0xBBBB5678
        native_geometry = convert_decoded_ps2_model(
            model, (native_tex,), POSITIONS, UV, FACES, (0, 0))[0]
        native_textures = make_pack('pc', hashes=(native_tex,))
        return (native_geometry,), (native_textures,)

    def test_optional_carbon_namespace_is_absent_by_default(self):
        self.assertIsNone(self.run_valid()['carbon_pc_namespace_preflight'])

    def test_optional_namespace_checks_real_converted_model_and_dxt5(self):
        g, t = self.native_roots()
        result = self.run_valid(native_geo=g, native_tex=t)
        report = result['carbon_pc_namespace_preflight']
        self.assertEqual(report['namespace_gate'],
                         'ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF')
        self.assertEqual(report['candidate_model_count'], 1)
        self.assertEqual(report['candidate_texture_count'], 2)
        self.assertEqual(report['candidate_materials_unresolved'], 0)
        self.assertFalse(result['safe_for_game_install'])
        self.assertFalse(report['in_game_rendering_verified'])

    def test_optional_namespace_reports_model_collision_without_disclosing_id(self):
        g, t = self.native_roots(collision_model=True)
        result = self.run_valid(native_geo=g, native_tex=t)
        report = result['carbon_pc_namespace_preflight']
        self.assertEqual(report['namespace_gate'], 'BLOCKED')
        self.assertEqual(report['candidate_models_colliding_with_native'], 1)
        self.assertNotIn(str(MODEL), json.dumps(report))

    def test_optional_namespace_reports_texture_collision(self):
        g, t = self.native_roots(collision_texture=True)
        report = self.run_valid(native_geo=g, native_tex=t)['carbon_pc_namespace_preflight']
        self.assertEqual(report['namespace_gate'], 'BLOCKED')
        self.assertEqual(report['candidate_textures_colliding_with_native'], 1)
        self.assertEqual(report['candidate_materials_unresolved'], 0)

    def test_optional_namespace_requires_both_carbon_roots(self):
        g, t = self.native_roots()
        with self.assertRaises(ValueError):
            self.run_valid(native_geo=g)
        with self.assertRaises(ValueError):
            self.run_valid(native_tex=t)

    def test_wrong_source_faces_refused(self):
        x = selected()
        x['triangles'] = 3
        with self.assertRaisesRegex(ValueError, 'preselected strip budget'):
            self.run_valid(x)

    def test_vif_material_budget_mismatch_refused(self):
        x = selected()
        x['source_material_budget'] = {0: 2}
        with self.assertRaisesRegex(ValueError, 'VIF face labels'):
            self.run_valid(x)

    def test_source_image_missing_refused(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.run_valid(source=make_pack('ps2', bits=8, hashes=(A, MISSING)))

    def test_bad_source_bytes_refused(self):
        with self.assertRaises(ValueError):
            self.run_valid(source=b'bad')

    def test_bool_mip_policy_rejected(self):
        for bad in (0, True, 17, -1, 'four'):
            with self.subTest(mips=bad), self.assertRaises(ValueError):
                self.run_valid(mip_levels=bad)

    def test_missing_candidate_fields_refused(self):
        with self.assertRaises(ValueError):
            self.run_valid(rowdata={'identity': MODEL})

    def test_private_source_bytes_required(self):
        with self.assertRaises(ValueError):
            self.run_valid(source=bytearray(b'fake'))

    def test_unmodified_original_not_required_for_synthetic(self):
        source = make_pack('ps2', bits=8, hashes=(A, B))
        self.run_valid(source=source)
        self.assertEqual(source, make_pack('ps2', bits=8, hashes=(A, B)))

    def test_read_only_missing_owner_zip(self):
        with self.assertRaises(ValueError):
            audit_original('/missing/owner/undercover.zip')

    def test_source_section_allowlist(self):
        with self.assertRaises(ValueError):
            audit_original('/missing/owner/undercover.zip', section=123)

    def test_documented_supported_source_sections(self):
        self.assertEqual(SOURCE_SECTIONS, (241, 3401))


if __name__ == '__main__':
    unittest.main()
