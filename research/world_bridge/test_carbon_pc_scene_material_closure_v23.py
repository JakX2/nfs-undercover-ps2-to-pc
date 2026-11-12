"""Synthetic Carbon PC source-format model→material→texture closure tests."""
import json
import struct
import unittest
from unittest.mock import patch

from carbon_pc_scene_material_closure_v23 import (
    _pc_model_materials, audit_pc_scene_material_closure,
)
from carbon_pc_first_model_scene_rebind import rebind_one_pc_scene_model
from carbon_pc_native_postscene_layout_gate import _children
from scenery_model_hash_bridge import FIRST_HASH_OFFSET, INFO_ID
from test_carbon_pc_first_model_stream_assembly import (
    MODEL, IMG1, geometry, dxt5,
)
from test_carbon_pc_first_model_scene_rebind import (
    CANDIDATE, ORIGINAL_SCENE,
)
from test_carbon_pc_native_postscene_layout_gate import scene
from undercover_pc_geometry_bridge import convert_decoded_ps2_model

NATIVE_MODEL = 101
NATIVE_TEXTURE = 0x11223344
OTHER_TEXTURE = 0x11223345
OTHER_MODEL = 0x12344321


def native_geometry(model=NATIVE_MODEL, materials=(NATIVE_TEXTURE,)):
    xyz = ((0.,0.,0.), (1.,0.,0.), (0.,1.,0.))
    uv = ((0.,0.), (1.,0.), (0.,1.))
    return convert_decoded_ps2_model(
        model, tuple(materials), xyz, uv, ((0,1,2),), (0,), None)[0]


def bound_scene(original=ORIGINAL_SCENE, index=0):
    return rebind_one_pc_scene_model(original, CANDIDATE, index)[0]


def change_lod(scene_blob, info_index, lod_slot, model_hash):
    original = bytearray(scene_blob)
    ranges = {tag: (start, stop) for tag,start,stop in
              _children(original, 8, len(original))}
    info_at = ranges[INFO_ID][0]
    struct.pack_into('<I', original,
                     info_at + info_index*72 + FIRST_HASH_OFFSET + lod_slot*4,
                     model_hash)
    return bytes(original)


def audit(scene_root=None, geometry_roots=None, texture_roots=None):
    return audit_pc_scene_material_closure(
        bound_scene() if scene_root is None else scene_root,
        CANDIDATE, 0,
        (native_geometry(),) if geometry_roots is None else geometry_roots,
        (dxt5(NATIVE_TEXTURE),) if texture_roots is None else texture_roots,
    )


class NativePcMaterialClosureTests(unittest.TestCase):
    def test_full_scene_model_material_texture_closure(self):
        r = audit()
        self.assertEqual(r['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')
        self.assertEqual(r['referenced_distinct_scene_models'], 2)
        self.assertEqual(r['referenced_models_backed_in_supplied_geometry'], 2)
        self.assertEqual(r['referenced_distinct_material_identities_from_backed_models'], 2)
        self.assertEqual(r['referenced_native_model_material_identities'], 1)
        self.assertEqual(r['native_distinct_texture_identities_supplied'], 1)
        self.assertEqual(r['converted_distinct_DXT5_texture_identities'], 1)
        self.assertEqual(r['referenced_material_identities_backed_by_native_textures'], 1)
        self.assertEqual(r['referenced_material_identities_backed_by_candidate_DXT5'], 1)
        self.assertEqual(r['referenced_material_identities_unresolved_in_supplied_textures'], 0)
        self.assertTrue(r['all_active_scene_model_materials_have_supplied_images'])
        self.assertTrue(r['all_scene_info_model_materials_have_supplied_images'])
        for flag in ('entire_carbon_global_texture_registry_examined',
                     'postscene_372xx_texture_dependencies_verified',
                     'native_carbon_sector_complete',
                     'carbon_loader_registered_resources_verified',
                     'undercover_model_rendered_inside_carbon_verified',
                     'stock_game_files_modified',
                     'private_model_texture_ids_names_pixels_disclosed'):
            self.assertFalse(r[flag])

    def test_per_model_material_table_extracts_actual_indexed_solid(self):
        r = _pc_model_materials(native_geometry())
        self.assertEqual(r, {NATIVE_MODEL: frozenset({NATIVE_TEXTURE})})
        multi = _pc_model_materials(native_geometry(materials=(NATIVE_TEXTURE, OTHER_TEXTURE)))
        self.assertEqual(len(multi[NATIVE_MODEL]), 2)

    def test_native_material_absent_in_supplied_texture_root(self):
        r = audit(texture_roots=(dxt5(OTHER_TEXTURE),))
        self.assertEqual(r['local_material_closure_gate'],
                         'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES')
        self.assertEqual(r['referenced_material_identities_unresolved_in_supplied_textures'], 1)
        self.assertFalse(r['all_active_scene_model_materials_have_supplied_images'])

    def test_extra_native_material_slot_is_not_ignored(self):
        native = native_geometry(materials=(NATIVE_TEXTURE, OTHER_TEXTURE))
        r = audit(geometry_roots=(native,))
        self.assertEqual(r['referenced_native_model_material_identities'], 2)
        self.assertEqual(r['referenced_material_identities_unresolved_in_supplied_textures'], 1)
        complete = audit(
            geometry_roots=(native,),
            texture_roots=(dxt5(NATIVE_TEXTURE, OTHER_TEXTURE),))
        self.assertEqual(complete['referenced_material_identities_unresolved_in_supplied_textures'], 0)
        self.assertEqual(complete['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')

    def test_unresolved_model_does_not_claim_unknown_materials_are_backed(self):
        r = audit(geometry_roots=(native_geometry(OTHER_MODEL),))
        self.assertEqual(r['referenced_models_backed_in_supplied_geometry'], 1)
        self.assertFalse(r['all_active_scene_model_materials_have_supplied_images'])
        self.assertEqual(r['local_material_closure_gate'],
                         'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES')

    def test_third_detail_lod_model_and_its_materials_are_included(self):
        scene_blob = change_lod(bound_scene(), 1, 2, OTHER_MODEL)
        r = audit(scene_root=scene_blob)
        self.assertEqual(r['referenced_models_backed_in_supplied_geometry'], 2)
        self.assertEqual(r['local_material_closure_gate'],
                         'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES')
        r = audit(scene_root=scene_blob,
                  geometry_roots=(native_geometry(), native_geometry(OTHER_MODEL, (OTHER_TEXTURE,))),
                  texture_roots=(dxt5(NATIVE_TEXTURE, OTHER_TEXTURE),))
        self.assertEqual(r['referenced_distinct_scene_models'], 3)
        self.assertEqual(r['referenced_models_backed_in_supplied_geometry'], 3)
        self.assertEqual(r['referenced_material_identities_unresolved_in_supplied_textures'], 0)
        self.assertEqual(r['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')

    def test_unreferenced_scene_row_dependencies_still_separately_audited(self):
        source = scene(pc=True, infos=3, inst=1)
        rebound = bound_scene(source, 0)
        r = audit(scene_root=rebound,
                  geometry_roots=(native_geometry(),))
        self.assertEqual(r['referenced_distinct_scene_models'], 1)
        self.assertTrue(r['all_active_scene_model_materials_have_supplied_images'])
        self.assertFalse(r['all_scene_info_model_materials_have_supplied_images'])
        self.assertEqual(r['local_material_closure_gate'],
                         'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES')

    def test_duplicate_native_texture_hash_is_not_assumed_safe(self):
        r = audit(texture_roots=(dxt5(NATIVE_TEXTURE), dxt5(NATIVE_TEXTURE)))
        self.assertEqual(r['native_texture_identities_repeated_across_roots'], 1)
        self.assertEqual(r['local_material_closure_gate'],
                         'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY')

    def test_native_and_candidate_image_collision_blocked(self):
        r = audit(texture_roots=(dxt5(NATIVE_TEXTURE, IMG1),))
        self.assertEqual(r['candidate_texture_identities_colliding_with_native'], 1)
        self.assertEqual(r['local_material_closure_gate'],
                         'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY')

    def test_duplicate_native_model_hash_blocked(self):
        r = audit(geometry_roots=(native_geometry(), native_geometry()))
        self.assertEqual(r['native_model_identities_repeated_across_roots'], 1)
        self.assertEqual(r['local_material_closure_gate'],
                         'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY')

    def test_converted_model_hash_colliding_with_native_blocked(self):
        r = audit(geometry_roots=(native_geometry(), native_geometry(MODEL, (OTHER_TEXTURE,))))
        self.assertEqual(r['local_material_closure_gate'],
                         'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY')

    def test_native_image_with_other_unreferenced_identity_allowed(self):
        r = audit(texture_roots=(dxt5(NATIVE_TEXTURE, OTHER_TEXTURE),))
        self.assertEqual(r['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')
        self.assertEqual(r['native_distinct_texture_identities_supplied'], 2)

    def test_corrupt_native_texture_index_fails_closed(self):
        for bad in (b'not a root',
                    dxt5(NATIVE_TEXTURE)[:-1],
                    bytearray(dxt5(NATIVE_TEXTURE))):
            with self.subTest(root_type=type(bad).__name__):
                with self.assertRaises(ValueError):
                    audit(texture_roots=(bad,))

    def test_corrupt_native_geometry_or_platform_rejected(self):
        with self.assertRaises(ValueError):
            audit(geometry_roots=(b'not geometry',))
        with patch('carbon_pc_scene_material_closure_v23.parse_geometry_root',
                   return_value={'platform':0x134a00, 'hashes':frozenset({NATIVE_MODEL})}):
            with self.assertRaises(ValueError):
                audit()

    def test_untrusted_raw_hash_set_cannot_pass_as_source(self):
        with self.assertRaises(ValueError):
            audit(geometry_roots=(frozenset({NATIVE_MODEL}),))
        with self.assertRaises(ValueError):
            audit(texture_roots=({NATIVE_TEXTURE},))

    def test_missing_native_texture_or_geometry_sources_are_invalid(self):
        for roots in ((), None):
            with self.subTest(roots=repr(roots)), self.assertRaises(ValueError):
                audit(texture_roots=roots)
            with self.subTest(roots=repr(roots)), self.assertRaises(ValueError):
                audit(geometry_roots=roots)

    def test_invalid_private_scene_and_candidate_inputs_fail(self):
        with self.assertRaises(ValueError):
            audit_pc_scene_material_closure(bytearray(bound_scene()),
                                             CANDIDATE, 0,
                                             (native_geometry(),), (dxt5(NATIVE_TEXTURE),))
        with self.assertRaises(ValueError):
            audit_pc_scene_material_closure(bound_scene(),
                                             CANDIDATE + b'X', 0,
                                             (native_geometry(),), (dxt5(NATIVE_TEXTURE),))
        with self.assertRaises(ValueError):
            audit_pc_scene_material_closure(bound_scene(), CANDIDATE, True,
                                             (native_geometry(),), (dxt5(NATIVE_TEXTURE),))

    def test_report_is_redacted_and_only_scalars(self):
        r = audit()
        raw = json.dumps(r)
        for private in (MODEL, IMG1, NATIVE_MODEL, NATIVE_TEXTURE, OTHER_TEXTURE):
            if private > 255:
                self.assertNotIn(str(private), raw)
                self.assertNotIn(hex(private), raw)
        self.assertTrue(all(type(value) in (bool,int,str) for value in r.values()))


if __name__ == '__main__':
    unittest.main()
