"""V22 original-free Carbon PC active-scene model identity closure tests."""
import json
import struct
import unittest
from unittest.mock import patch

from carbon_pc_scene_model_closure_v22 import audit_pc_scene_model_closure
from carbon_pc_first_model_scene_rebind import rebind_one_pc_scene_model
from scenery_model_hash_bridge import INFO_ID, FIRST_HASH_OFFSET
from carbon_pc_native_postscene_layout_gate import _children
from test_carbon_pc_first_model_scene_rebind import ORIGINAL_SCENE, CANDIDATE
from test_carbon_pc_first_model_stream_assembly import MODEL, IMG1, geometry
from test_carbon_pc_native_postscene_layout_gate import scene
from undercover_pc_geometry_bridge import convert_decoded_ps2_model

# Original Carbon PC synthetic fixture scene uses model hashes 100,101...
NATIVE_A = 100
NATIVE_B = 101
NATIVE_C = 102
EXTRA_LOD = 0x98761234


def native_model(identity):
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    uv = ((0., 0.), (1., 0.), (0., 1.))
    blob, _ = convert_decoded_ps2_model(
        identity, (IMG1,), positions, uv, ((0, 1, 2),), (0,), None)
    return blob


def patched(original=ORIGINAL_SCENE, index=0):
    return rebind_one_pc_scene_model(original, CANDIDATE, index)[0]


def patch_hash(scene_blob, index, slot, value):
    result = bytearray(scene_blob)
    info_start = {tag: (start, end) for tag,start,end in
                  _children(scene_blob, 8, len(scene_blob))}[INFO_ID][0]
    struct.pack_into('<I', result,
                     info_start+index*72+FIRST_HASH_OFFSET+slot*4, value)
    return bytes(result)


class SceneClosureTests(unittest.TestCase):
    def test_one_rebound_model_plus_original_carbon_model_is_closed_offline(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0, (native_model(NATIVE_B),))
        self.assertEqual(report['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')
        self.assertEqual(report['scenery_info_records'], 2)
        self.assertEqual(report['scenery_instance_records'], 2)
        self.assertEqual(report['referenced_info_records'], 2)
        self.assertEqual(report['referenced_nonzero_model_slot_occurrences'], 4)
        self.assertEqual(report['referenced_distinct_model_identities'], 2)
        self.assertEqual(report['source_native_models_referenced_by_instances'], 1)
        self.assertEqual(report['referenced_model_identities_unresolved_in_supplied_roots'], 0)
        self.assertTrue(report['all_scene_info_model_slots_backed_in_supplied_roots'])
        self.assertTrue(report['converted_undercover_model_referenced_by_instances'])
        for false_claim in (
            'all_carbon_global_model_resources_enumerated',
            'native_material_texture_closure_verified',
            'native_postscene_control_dependencies_verified',
            'native_carbon_stream_sector_complete',
            'external_loader_model_registration_verified',
            'undercover_object_rendered_in_game',
            'game_files_modified',
            'private_model_ids_original_names_coordinates_disclosed',
        ):
            self.assertFalse(report[false_claim], false_claim)

    def test_missing_original_carbon_model_stays_incomplete_not_unsafe_success(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0, (native_model(777),))
        self.assertEqual(report['local_model_reference_gate'],
                         'INCOMPLETE_REFERENCES_IN_SUPPLIED_NATIVE_GEOMETRY')
        self.assertEqual(report['referenced_model_identities_unresolved_in_supplied_roots'], 1)
        self.assertFalse(report['all_referenced_instance_model_slots_backed_in_supplied_roots'])

    def test_wrong_selected_info_rebind_fails(self):
        with self.assertRaisesRegex(ValueError, 'does not match'):
            audit_pc_scene_model_closure(
                patched(index=1), CANDIDATE, 0, (native_model(NATIVE_A),))

    def test_missing_instance_reference_fails(self):
        root = scene(pc=True, infos=3, inst=1)
        modified = patched(root, index=0)
        with self.assertRaisesRegex(ValueError, 'not referenced'):
            audit_pc_scene_model_closure(
                modified, CANDIDATE, 2, (native_model(NATIVE_B),))

    def test_native_model_id_collision_is_blocker(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0,
            (native_model(MODEL), native_model(NATIVE_B)))
        self.assertTrue(report['converted_model_collision_with_native'])
        self.assertEqual(report['local_model_reference_gate'],
                         'BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID')

    def test_duplicate_native_root_model_id_is_ambiguous(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0,
            (native_model(NATIVE_B), native_model(NATIVE_B)))
        self.assertEqual(report['source_native_repeated_model_identities'], 1)
        self.assertEqual(report['local_model_reference_gate'],
                         'BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID')

    def test_additional_lod_slot_is_included_in_active_references(self):
        changed = patch_hash(patched(), 1, 2, EXTRA_LOD)
        absent = audit_pc_scene_model_closure(
            changed, CANDIDATE, 0, (native_model(NATIVE_B),))
        self.assertEqual(absent['referenced_distinct_model_identities'], 3)
        self.assertEqual(absent['referenced_model_identities_unresolved_in_supplied_roots'], 1)
        resolved = audit_pc_scene_model_closure(
            changed, CANDIDATE, 0,
            (native_model(NATIVE_B), native_model(EXTRA_LOD)))
        self.assertEqual(resolved['referenced_model_identities_unresolved_in_supplied_roots'], 0)
        self.assertEqual(resolved['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')

    def test_unreferenced_scene_info_still_counted_without_fake_runtime_claims(self):
        original = scene(pc=True, infos=3, inst=1)
        reb = patched(original, index=0)
        report = audit_pc_scene_model_closure(
            reb, CANDIDATE, 0, (native_model(NATIVE_A),))
        self.assertEqual(report['referenced_info_records'], 1)
        self.assertEqual(report['unreferenced_info_records'], 2)
        self.assertEqual(report['referenced_model_identities_unresolved_in_supplied_roots'], 0)
        self.assertEqual(report['all_scene_model_identities_unresolved_in_supplied_roots'], 2)
        self.assertEqual(report['local_model_reference_gate'],
                         'INCOMPLETE_REFERENCES_IN_SUPPLIED_NATIVE_GEOMETRY')

    def test_extra_native_model_does_not_affect_reference_closure(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0,
            (native_model(NATIVE_B), native_model(EXTRA_LOD)))
        self.assertEqual(report['source_native_distinct_indexed_models'], 2)
        self.assertEqual(report['source_native_models_referenced_by_instances'], 1)
        self.assertEqual(report['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')

    def test_candidate_cannot_appear_in_unmodified_other_slot(self):
        with self.assertRaisesRegex(ValueError, 'another scene LOD slot'):
            audit_pc_scene_model_closure(
                patch_hash(patched(), 1, 3, MODEL), CANDIDATE, 0,
                (native_model(NATIVE_B),))
        with self.assertRaisesRegex(ValueError, 'another scene LOD slot'):
            audit_pc_scene_model_closure(
                patch_hash(patched(), 0, 2, MODEL), CANDIDATE, 0,
                (native_model(NATIVE_B),))

    def test_bad_native_platform_or_geometry_data_refused(self):
        with self.assertRaises(ValueError):
            audit_pc_scene_model_closure(
                patched(), CANDIDATE, 0, (b'NOT A PC MODEL PACK',))
        with patch('carbon_pc_scene_model_closure_v22.parse_geometry_root',
                   return_value={'platform': 0x00134A00,
                                 'solid_count': 1,
                                 'hashes': frozenset({NATIVE_B})}):
            with self.assertRaises(ValueError):
                audit_pc_scene_model_closure(
                    patched(), CANDIDATE, 0, (native_model(NATIVE_B),))

    def test_reference_list_fail_closed(self):
        for roots in ((), None, (bytearray(native_model(NATIVE_B)),),
                      tuple(native_model(NATIVE_B) for _ in range(33))):
            with self.subTest(roots_type=str(type(roots))):
                with self.assertRaises(ValueError):
                    audit_pc_scene_model_closure(
                        patched(), CANDIDATE, 0, roots)

    def test_invalid_candidate_order_and_trailing_bytes_refused(self):
        g, _ = geometry(), None
        with self.assertRaises(ValueError):
            audit_pc_scene_model_closure(
                patched(), g + CANDIDATE, 0, (native_model(NATIVE_B),))
        with self.assertRaises(ValueError):
            audit_pc_scene_model_closure(
                patched(), CANDIDATE + b'X', 0, (native_model(NATIVE_B),))

    def test_invalid_info_index_types_refused(self):
        for idx in (-1, True, '0', 0.0, None):
            with self.subTest(value=repr(idx)):
                with self.assertRaises(ValueError):
                    audit_pc_scene_model_closure(
                        patched(), CANDIDATE, idx, (native_model(NATIVE_B),))

    def test_scene_profile_rejects_corrupt_instance_index(self):
        root = bytearray(patched())
        positions = {tag: (a, b) for tag, a,b in
                     _children(root, 8, len(root))}
        ia = positions[0x34103][0]
        struct.pack_into('<h', root, ia + 4 + 0x54, -1)
        with self.assertRaises(ValueError):
            audit_pc_scene_model_closure(
                bytes(root), CANDIDATE, 0, (native_model(NATIVE_B),))

    def test_report_contains_no_retail_or_fixture_model_identities(self):
        report = audit_pc_scene_model_closure(
            patched(), CANDIDATE, 0, (native_model(NATIVE_B),))
        payload = json.dumps(report)
        for value in (MODEL, IMG1, NATIVE_A, NATIVE_B, EXTRA_LOD):
            self.assertNotIn(hex(value), payload)
            # Tiny values like 101 may also appear as digits in text;
            # require no raw machine-sized integer model identities.
            if value > 255:
                self.assertNotIn(str(value), payload)
        self.assertTrue(all(type(value) in (bool, int, str)
                            for value in report.values()))


if __name__ == '__main__':
    unittest.main()
