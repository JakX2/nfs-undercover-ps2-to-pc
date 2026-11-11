"""Synthetic-only PC resource namespace compatibility tests.

No retail Carbon/Undercover IDs, binaries or game assets.
"""
import unittest
from unittest.mock import patch

from carbon_pc_resource_namespace_gate import audit_carbon_registration_namespace
from undercover_pc_geometry_bridge import convert_decoded_ps2_model
from test_texture_visual_pair_gate import make_pack
from texture_metadata_pixel_bridge import parse_pack

CANDIDATE_MODEL = 0xAABBCC01
NATIVE_MODEL = 0xAABBCC02
CANDIDATE_TEX = 0x12340001
NATIVE_TEX = 0x12340002


def geometry(model, materials):
    points = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    uv = ((0., 0.), (1., 0.), (0., 1.))
    root, _stats = convert_decoded_ps2_model(
        model, tuple(materials), points, uv, ((0, 1, 2),), (0,), None)
    return root


def images(*ids):
    return make_pack('pc', hashes=tuple(sorted(ids)))


def check(candidate_model=CANDIDATE_MODEL, candidate_materials=(CANDIDATE_TEX,),
          candidate_images=(CANDIDATE_TEX,), native_models=(NATIVE_MODEL,),
          native_materials=(NATIVE_TEX,), native_images=(NATIVE_TEX,)):
    return audit_carbon_registration_namespace(
        geometry(candidate_model, candidate_materials),
        images(*candidate_images),
        tuple(geometry(mid, native_materials) for mid in native_models),
        (images(*native_images),),
    )


class CarbonNamespaceGateTests(unittest.TestCase):
    def test_disjoint_complete_candidate_is_only_offline_eligible(self):
        report = check()
        self.assertEqual(
            report['namespace_gate'],
            'ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF')
        self.assertFalse(any(report['blockers'].values()))
        self.assertEqual(report['candidate_model_count'], 1)
        self.assertEqual(report['candidate_texture_count'], 1)
        self.assertEqual(report['candidate_distinct_material_id_count'], 1)
        self.assertEqual(report['candidate_materials_unresolved'], 0)
        for field in ('runtime_registration_verified',
                      'carbon_loader_abi_verified',
                      'full_carbon_registry_coverage_verified',
                      'in_game_rendering_verified'):
            self.assertFalse(report[field])

    def test_native_model_hash_collision_blocks(self):
        report = check(native_models=(CANDIDATE_MODEL,))
        self.assertEqual(report['namespace_gate'], 'BLOCKED')
        self.assertEqual(report['candidate_models_colliding_with_native'], 1)
        self.assertTrue(report['blockers']['model_identity_collision'])

    def test_native_texture_hash_collision_blocks_even_if_material_resolved(self):
        report = check(native_images=(CANDIDATE_TEX, NATIVE_TEX))
        self.assertEqual(report['namespace_gate'], 'BLOCKED')
        self.assertTrue(report['blockers']['texture_identity_collision'])
        self.assertEqual(report['candidate_textures_colliding_with_native'], 1)
        self.assertEqual(report['candidate_materials_unresolved'], 0)

    def test_missing_full_material_entry_blocks(self):
        report = check(candidate_materials=(CANDIDATE_TEX, 0x12340003))
        self.assertEqual(report['namespace_gate'], 'BLOCKED')
        self.assertEqual(report['candidate_materials_unresolved'], 1)
        self.assertTrue(report['blockers']['unresolved_candidate_materials'])

    def test_can_use_existing_carbon_texture_without_candidate_collision(self):
        report = check(candidate_materials=(NATIVE_TEX,))
        self.assertEqual(report['namespace_gate'],
                         'ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF')
        self.assertEqual(report['candidate_materials_resolved_by_native'], 1)
        self.assertEqual(report['candidate_materials_resolved_by_candidate'], 0)

    def test_count_source_identities_not_names(self):
        # Model and texture IDs are separate namespaces; same numeric value
        # across namespaces must not trigger a false collision.
        report = check(candidate_model=NATIVE_TEX)
        self.assertEqual(report['candidate_models_colliding_with_native'], 0)
        self.assertEqual(report['namespace_gate'],
                         'ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF')

    def test_no_private_identifiers_leak_to_report(self):
        report = check()
        raw = repr(report)
        for value in (CANDIDATE_MODEL, NATIVE_MODEL,
                      CANDIDATE_TEX, NATIVE_TEX):
            self.assertNotIn(hex(value), raw)
            self.assertNotIn(str(value), raw)
        self.assertTrue(all(type(v) in (int, bool, str, dict)
                            for v in report.values()))

    def test_repeated_native_model_identity_counts_as_one(self):
        report = check(native_models=(NATIVE_MODEL, NATIVE_MODEL))
        self.assertEqual(report['native_model_count_in_supplied_roots'], 1)
        self.assertEqual(report['candidate_models_colliding_with_native'], 0)

    def test_root_inputs_required_and_bounded(self):
        candidate = geometry(CANDIDATE_MODEL, (CANDIDATE_TEX,))
        texture = images(CANDIDATE_TEX)
        native = geometry(NATIVE_MODEL, (NATIVE_TEX,))
        ntex = images(NATIVE_TEX)
        for geo, tex in (((), (ntex,)), ((native,), ()),
                         (None, (ntex,)), ((native,), None),
                         ((native,)*33, (ntex,))):
            with self.subTest(geo=type(geo).__name__), self.assertRaises(ValueError):
                audit_carbon_registration_namespace(candidate, texture,
                                                    geo, tex)

    def test_rejects_non_pc_or_corrupt_geometry(self):
        candidate = geometry(CANDIDATE_MODEL, (CANDIDATE_TEX,))
        native = geometry(NATIVE_MODEL, (NATIVE_TEX,))
        with self.assertRaises(ValueError):
            audit_carbon_registration_namespace(candidate[:-1],
                                               images(CANDIDATE_TEX),
                                               (native,), (images(NATIVE_TEX),))
        with patch('carbon_pc_resource_namespace_gate.parse_geometry_root',
                   return_value={'platform': 0x00134A00}):
            with self.assertRaises(ValueError):
                audit_carbon_registration_namespace(candidate,
                                                   images(CANDIDATE_TEX),
                                                   (native,), (images(NATIVE_TEX),))

    def test_rejects_trailing_texture_data(self):
        candidate = geometry(CANDIDATE_MODEL, (CANDIDATE_TEX,))
        native = geometry(NATIVE_MODEL, (NATIVE_TEX,))
        with self.assertRaises(ValueError):
            audit_carbon_registration_namespace(candidate,
                images(CANDIDATE_TEX) + b'EXTRA',
                (native,), (images(NATIVE_TEX),))

    def test_rejects_wrong_platform_texture(self):
        candidate = geometry(CANDIDATE_MODEL, (CANDIDATE_TEX,))
        native = geometry(NATIVE_MODEL, (NATIVE_TEX,))
        with self.assertRaises(ValueError):
            audit_carbon_registration_namespace(candidate,
                make_pack('ps2', hashes=(CANDIDATE_TEX,)),
                (native,), (images(NATIVE_TEX),))

    def test_cannot_silently_skip_native_pack_parse_failure(self):
        candidate = geometry(CANDIDATE_MODEL, (CANDIDATE_TEX,))
        with self.assertRaises(ValueError):
            audit_carbon_registration_namespace(
                candidate, images(CANDIDATE_TEX),
                (b'NOT_PC_GEOMETRY',), (images(NATIVE_TEX),))

    def test_sorted_multi_texture_and_shared_material_counts(self):
        report = check(
            candidate_materials=(CANDIDATE_TEX, NATIVE_TEX),
            candidate_images=(CANDIDATE_TEX,),
            native_images=(NATIVE_TEX,))
        self.assertEqual(report['candidate_materials_unresolved'], 0)
        self.assertEqual(report['candidate_materials_resolved_by_candidate'], 1)
        self.assertEqual(report['candidate_materials_resolved_by_native'], 1)


if __name__ == '__main__':
    unittest.main()
