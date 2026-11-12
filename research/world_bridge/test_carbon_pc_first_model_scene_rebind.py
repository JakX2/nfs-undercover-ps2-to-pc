"""Synthetic-only Carbon PC scenery model rebind regression controls.

Checks real first-model PC geometry and image serializers against a genuine
Carbon-shaped 0x80034100 scenery tree fixture. No retail data distributed.
"""
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from carbon_pc_first_model_scene_rebind import (
    rebind_one_pc_scene_model, inspect_private_scene_and_candidate,
)
from carbon_pc_native_postscene_layout_gate import _children, SCENE_CHILDREN, scene_profile
from scenery_model_hash_bridge import FIRST_HASH_OFFSET, INFO_ID, INSTANCE_ID
from test_carbon_pc_first_model_stream_assembly import (
    MODEL, IMG1, geometry, dxt5,
)
from carbon_pc_first_model_stream_assembly import build_private_pc_first_model_stream
from test_carbon_pc_native_postscene_layout_gate import scene

CANDIDATE = build_private_pc_first_model_stream(geometry(), dxt5(IMG1))[0]
ORIGINAL_SCENE = scene(pc=True, infos=2, inst=2)


def scene_positions(original):
    return {tag: (a, b) for tag, a, b in
            _children(original, 8, len(original))}


class InMemorySceneRebindTests(unittest.TestCase):
    def test_one_info_row_two_hash_slots_only_and_source_links_preserved(self):
        modified, audit = rebind_one_pc_scene_model(
            ORIGINAL_SCENE, CANDIDATE, 0)
        self.assertEqual(len(modified), len(ORIGINAL_SCENE))
        a, b = scene_positions(modified)[INFO_ID]
        old = scene_positions(ORIGINAL_SCENE)
        self.assertEqual((a, b), old[INFO_ID])
        hash_at = a + FIRST_HASH_OFFSET
        self.assertEqual(struct.unpack_from('<II', modified, hash_at),
                         (MODEL, MODEL))
        self.assertEqual(modified[:hash_at], ORIGINAL_SCENE[:hash_at])
        self.assertEqual(modified[hash_at+8:],
                         ORIGINAL_SCENE[hash_at+8:])
        xa, xb = scene_positions(modified)[INSTANCE_ID]
        self.assertEqual(modified[xa:xb], ORIGINAL_SCENE[xa:xb])
        self.assertEqual(scene_profile(modified, 'pc'),
                         scene_profile(ORIGINAL_SCENE, 'pc'))
        self.assertEqual(audit['selected_info_instances_preserved'], 1)
        self.assertEqual(audit['scene_info_entries_rebound'], 1)
        self.assertEqual(audit['hash_fields_rebound'], 2)
        self.assertEqual(audit['other_scene_model_ids_still_referenced'], 1)
        self.assertFalse(audit['all_other_native_model_references_resolved'])
        self.assertFalse(audit['native_carbon_stream_sector_complete'])
        self.assertFalse(audit['pc_external_loader_registration_verified'])

    def test_second_row_rebind_preserves_first(self):
        modified, report = rebind_one_pc_scene_model(
            ORIGINAL_SCENE, CANDIDATE, 1)
        a, _ = scene_positions(modified)[INFO_ID]
        self.assertEqual(modified[a:a+72], ORIGINAL_SCENE[a:a+72])
        self.assertEqual(struct.unpack_from('<II',
            modified, a + 72 + FIRST_HASH_OFFSET), (MODEL, MODEL))
        self.assertEqual(report['selected_info_instances_preserved'], 1)

    def test_multiple_instances_referencing_same_info_remain_unchanged(self):
        original = scene(pc=True, infos=2, inst=5)
        patched, report = rebind_one_pc_scene_model(original, CANDIDATE, 0)
        self.assertEqual(report['selected_info_instances_preserved'], 3)
        a, b = scene_positions(original)[INSTANCE_ID]
        self.assertEqual(patched[a:b], original[a:b])

    def test_selected_row_must_be_referenced(self):
        original = scene(pc=True, infos=3, inst=1)
        with self.assertRaisesRegex(ValueError, 'no instance reference'):
            rebind_one_pc_scene_model(original, CANDIDATE, 2)

    def test_bad_index_or_types_refused(self):
        for bad in (-1, True, 2, 1.0, '0', None):
            with self.subTest(index=repr(bad)), self.assertRaises(ValueError):
                rebind_one_pc_scene_model(ORIGINAL_SCENE, CANDIDATE, bad)
        for bad in (bytearray(ORIGINAL_SCENE), None, b'bad'):
            with self.subTest(scene_type=type(bad).__name__), self.assertRaises(ValueError):
                rebind_one_pc_scene_model(bad, CANDIDATE, 0)
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(ORIGINAL_SCENE, bytearray(CANDIDATE), 0)

    def test_legacy_geometry_first_v19_candidate_refused(self):
        geom, tex = geometry(), dxt5(IMG1)
        with self.assertRaisesRegex(ValueError, 'texture-first'):
            rebind_one_pc_scene_model(ORIGINAL_SCENE, geom + tex, 0)

    def test_noop_same_hash_refused(self):
        src = bytearray(ORIGINAL_SCENE)
        a, _ = scene_positions(src)[INFO_ID]
        struct.pack_into('<II', src, a+FIRST_HASH_OFFSET, MODEL, MODEL)
        with self.assertRaisesRegex(ValueError, 'cannot be rebound'):
            rebind_one_pc_scene_model(bytes(src), CANDIDATE, 0)

    def test_new_model_colliding_with_other_info_row_refused(self):
        src = bytearray(ORIGINAL_SCENE)
        a, _ = scene_positions(src)[INFO_ID]
        struct.pack_into('<II', src, a+72+FIRST_HASH_OFFSET, MODEL, MODEL)
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            rebind_one_pc_scene_model(bytes(src), CANDIDATE, 0)

    def test_original_scene_profile_must_be_native_pc(self):
        src = bytearray(ORIGINAL_SCENE)
        a, _ = scene_positions(src)[INFO_ID]
        struct.pack_into('<I', src, a+FIRST_HASH_OFFSET, 0)
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(bytes(src), CANDIDATE, 0)
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(ORIGINAL_SCENE[:-1], CANDIDATE, 0)

    def test_corrupt_instance_links_refused(self):
        src = bytearray(ORIGINAL_SCENE)
        a, _ = scene_positions(src)[INSTANCE_ID]
        struct.pack_into('<h', src, a+4+0x54, -1)
        with self.assertRaisesRegex(ValueError, 'index'):
            rebind_one_pc_scene_model(bytes(src), CANDIDATE, 0)

    def test_invalid_candidate_resource_closure_fails(self):
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(ORIGINAL_SCENE,
                dxt5(IMG1) + geometry((0xDEADBEEF,)), 0)
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(ORIGINAL_SCENE,
                CANDIDATE + b'\x00' * 8, 0)

    def test_rebind_does_not_export_private_names_ids_coordinates(self):
        _, report = rebind_one_pc_scene_model(
            ORIGINAL_SCENE, CANDIDATE, 0)
        output = json.dumps(report)
        for private in (str(MODEL), hex(MODEL),
                        str(IMG1), hex(IMG1)):
            self.assertNotIn(private, output)
        self.assertFalse(report['private_ids_coordinates_and_scene_bytes_disclosed'])
        self.assertFalse(report['game_files_modified'])

    def test_missing_unknown_subchunk_refused(self):
        src = bytearray(ORIGINAL_SCENE)
        first = scene_positions(src)[SCENE_CHILDREN[0]][0] - 8
        struct.pack_into('<I', src, first, 0x99999999)
        with self.assertRaises(ValueError):
            rebind_one_pc_scene_model(bytes(src), CANDIDATE, 0)

    def test_reparse_failure_in_modified_scene_is_fatal(self):
        with patch('carbon_pc_first_model_scene_rebind.scene_profile',
                   side_effect=[scene_profile(ORIGINAL_SCENE, 'pc'),
                                ValueError('forced synthetic parser disagreement')]):
            with self.assertRaises(ValueError):
                rebind_one_pc_scene_model(ORIGINAL_SCENE, CANDIDATE, 0)


class OwnerLocalReadOnlyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.scene_file = self.root / 'carbon-original.pcscene'
        self.candidate_file = self.root / 'undercover-candidate.pcchunk'
        self.scene_file.write_bytes(ORIGINAL_SCENE)
        self.candidate_file.write_bytes(CANDIDATE)

    def test_private_files_remain_unchanged_and_no_output_created(self):
        old_scene = self.scene_file.read_bytes()
        old_candidate = self.candidate_file.read_bytes()
        stamps = (self.scene_file.stat().st_mtime_ns,
                  self.candidate_file.stat().st_mtime_ns)
        report = inspect_private_scene_and_candidate(
            self.scene_file, self.candidate_file, 0)
        self.assertTrue(report['original_instance_indices_unchanged'])
        self.assertEqual(old_scene, self.scene_file.read_bytes())
        self.assertEqual(old_candidate, self.candidate_file.read_bytes())
        self.assertEqual(stamps, (
            self.scene_file.stat().st_mtime_ns,
            self.candidate_file.stat().st_mtime_ns))
        self.assertEqual(list(self.root.iterdir()).__len__(), 2)
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_refuse_missing_or_wrong_extension(self):
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(
                self.root / 'missing.pcscene', self.candidate_file, 0)
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(
                self.candidate_file, self.scene_file, 0)

    def test_refuse_symlink_scene_root(self):
        alias = self.root / 'alias.pcscene'
        try:
            alias.symlink_to(self.scene_file)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(alias, self.candidate_file, 0)

    def test_refuse_alias_hardlinked_sources(self):
        alias = self.root / 'model.pcchunk'
        try:
            os.link(self.scene_file, alias)
        except (OSError, NotImplementedError):
            self.skipTest('Hardlinks unsupported')
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(self.scene_file, alias, 0)

    def test_source_mutation_after_read_refused(self):
        import carbon_pc_first_model_scene_rebind as module
        previous = module.rebind_one_pc_scene_model
        def tamper(*args):
            patched, report = previous(*args)
            self.scene_file.write_bytes(self.scene_file.read_bytes()+b'X')
            return patched, report
        with patch.object(module, 'rebind_one_pc_scene_model', tamper):
            with self.assertRaises(ValueError):
                inspect_private_scene_and_candidate(
                    self.scene_file, self.candidate_file, 0)


if __name__ == '__main__':
    unittest.main()
