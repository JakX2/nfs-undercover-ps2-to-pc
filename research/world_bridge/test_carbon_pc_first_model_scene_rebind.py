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
    inspect_owner_original_carbon_rb_section, export_private_rebound_pc_scene,
)
from carbon_pc_native_postscene_layout_gate import _children, SCENE_CHILDREN, scene_profile
from scenery_model_hash_bridge import FIRST_HASH_OFFSET, INFO_ID, INSTANCE_ID
from test_carbon_pc_first_model_stream_assembly import (
    MODEL, IMG1, geometry, dxt5,
)
from carbon_pc_first_model_stream_assembly import build_private_pc_first_model_stream
from test_carbon_pc_native_postscene_layout_gate import (
    scene, pc_section, fixture_stream_and_bundle,
)

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
        with self.assertRaisesRegex(ValueError, 'nonexistent source info'):
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

    def test_guarded_private_scene_export_from_extracted_source(self):
        output = self.root / 'one-undercover-info.pcscene'
        report = inspect_private_scene_and_candidate(
            self.scene_file, self.candidate_file, 0,
            private_scene_output=output, write_private=True)
        original = self.scene_file.read_bytes()
        modified = output.read_bytes()
        a, _ = scene_positions(original)[INFO_ID]
        self.assertEqual(struct.unpack_from('<II',
            modified, a+FIRST_HASH_OFFSET), (MODEL, MODEL))
        self.assertEqual(modified[:a+FIRST_HASH_OFFSET],
                         original[:a+FIRST_HASH_OFFSET])
        self.assertEqual(modified[a+FIRST_HASH_OFFSET+8:],
                         original[a+FIRST_HASH_OFFSET+8:])
        self.assertTrue(report['private_scene_export']['private_scene_created'])
        self.assertFalse(report['private_scene_export']['carbon_stream_sector_complete'])
        self.assertFalse(report['private_scene_export']['in_game_model_rendered'])
        self.assertNotIn(str(output), json.dumps(report))

    def test_no_export_without_both_flags(self):
        output = self.root / 'rebound.pcscene'
        for kwargs in ({'private_scene_output': output},
                       {'write_private': True},
                       {'write_private': 'True', 'private_scene_output': output}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(
                    ValueError, 'requires BOTH'):
                inspect_private_scene_and_candidate(
                    self.scene_file, self.candidate_file, 0, **kwargs)
        self.assertFalse(output.exists())

    def test_existing_export_is_preserved(self):
        output = self.root / 'existing.pcscene'
        output.write_bytes(b'DO NOT OVERWRITE')
        with self.assertRaises(FileExistsError):
            inspect_private_scene_and_candidate(
                self.scene_file, self.candidate_file, 0,
                private_scene_output=output, write_private=True)
        self.assertEqual(output.read_bytes(), b'DO NOT OVERWRITE')

    def test_private_scene_writer_refuses_stock_game_tracks(self):
        tracks = self.root / 'Carbon' / 'TRACKS'
        tracks.mkdir(parents=True)
        output = tracks / 'would-be-patch.pcscene'
        with self.assertRaisesRegex(ValueError, 'OUTSIDE game TRACKS'):
            export_private_rebound_pc_scene(
                ORIGINAL_SCENE, CANDIDATE, 0, output, apply=True)
        self.assertFalse(output.exists())

    def test_private_writer_does_not_rename_to_bun(self):
        output = self.root / 'rebound.BUN'
        with self.assertRaises(ValueError):
            export_private_rebound_pc_scene(
                ORIGINAL_SCENE, CANDIDATE, 0, output, apply=True)
        self.assertFalse(output.exists())

    def test_private_writer_revalidates_and_needs_opt_in(self):
        output = self.root / 'rebound.pcscene'
        with self.assertRaisesRegex(ValueError, 'explicit'):
            export_private_rebound_pc_scene(
                ORIGINAL_SCENE, CANDIDATE, 0, output)
        self.assertFalse(output.exists())
        result = export_private_rebound_pc_scene(
            ORIGINAL_SCENE, CANDIDATE, 1, output, apply=True)
        self.assertEqual(result['private_scene_rebound_info_rows'], 1)
        self.assertTrue(result['private_scene_revalidated_on_disk'])
        self.assertFalse(result['source_carbon_game_files_modified'])

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


class OwnerCarbonPairSectionTests(unittest.TestCase):
    """Original-free native Carbon L5RB section/source filename controls."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tracks = self.root / 'CarbonTest' / 'TRACKS'
        self.tracks.mkdir(parents=True)
        self.bun = self.tracks / 'L5RB.BUN'
        self.stream = self.tracks / 'STREAML5RB.BUN'
        self.candidate = self.root / 'first-model.pcchunk'
        self.candidate.write_bytes(CANDIDATE)
        b, st = fixture_stream_and_bundle([
            (141, pc_section(1)), (142, pc_section(6, zero_gap=True))
        ])
        self.bun.write_bytes(b)
        self.stream.write_bytes(st)

    def audit(self, section=141, index=0, **kw):
        params = {
            'carbon_l5rb_bun': self.bun,
            'carbon_stream_l5rb_bun': self.stream,
            'candidate_path': self.candidate,
            'section_id': section, 'info_index': index,
        }
        params.update(kw)
        return inspect_owner_original_carbon_rb_section(**params)

    def test_native_section_141_extracted_and_rebound_in_ram(self):
        before = [(p.read_bytes(), p.stat().st_mtime_ns)
                  for p in (self.bun, self.stream, self.candidate)]
        report = self.audit(section=141, index=0)
        after = [(p.read_bytes(), p.stat().st_mtime_ns)
                 for p in (self.bun, self.stream, self.candidate)]
        self.assertEqual(before, after)
        self.assertTrue(report['native_carbon_full_original_rb_section_profile_verified'])
        self.assertTrue(report['original_carbon_scene_extracted_without_writing'])
        self.assertTrue(report['original_carbon_source_file_preserved'])
        self.assertEqual(report['native_carbon_pc_source_section_id'], 141)
        self.assertEqual(report['native_carbon_original_postscene_control_groups'], 1)
        self.assertFalse(report['native_carbon_stream_sector_complete'])
        self.assertFalse(report['pc_external_loader_registration_verified'])
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_native_142_zero_chunk_and_six_control_groups(self):
        report = self.audit(section=142, index=1)
        self.assertEqual(report['native_carbon_pc_source_section_id'], 142)
        self.assertEqual(report['native_carbon_original_postscene_control_groups'], 6)
        self.assertEqual(report['selected_info_instances_preserved'], 1)

    def test_export_source_pinned_rebound_scene_without_modifying_carbon(self):
        output = self.root / 'new-original-derived-scene.pcscene'
        before = (self.bun.read_bytes(), self.stream.read_bytes(),
                  self.candidate.read_bytes())
        report = self.audit(
            private_scene_output=output, write_private=True)
        self.assertTrue(output.is_file())
        self.assertEqual(before, (
            self.bun.read_bytes(), self.stream.read_bytes(),
            self.candidate.read_bytes()))
        self.assertTrue(report['private_scene_export']['private_scene_created'])
        self.assertFalse(report['native_carbon_stream_sector_complete'])
        self.assertNotIn(str(output), json.dumps(report))
        # Only the selected scene info primary hash pair can differ.
        from carbon_pc_native_postscene_layout_gate import (
            _scan_roots, stream_rows,
        )
        rows = stream_rows(self.bun.read_bytes(), self.stream.stat().st_size)
        at, n = rows[141]
        original = _scan_roots(self.stream.read_bytes()[at:at+n], 1)['scene']
        a, _ = scene_positions(original)[INFO_ID]
        self.assertEqual(output.read_bytes()[:a+FIRST_HASH_OFFSET],
                         original[:a+FIRST_HASH_OFFSET])
        self.assertEqual(output.read_bytes()[a+FIRST_HASH_OFFSET+8:],
                         original[a+FIRST_HASH_OFFSET+8:])

    def test_owner_original_mode_export_requires_explicit_flag(self):
        output = self.root / 'only-if-explicit.pcscene'
        for kwargs in (
            {'private_scene_output': output},
            {'write_private': True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(
                    ValueError, 'requires BOTH'):
                self.audit(**kwargs)
        self.assertFalse(output.exists())

    def test_private_export_refuses_to_overwrite_previous_result(self):
        output = self.root / 'already-exists.pcscene'
        output.write_bytes(b'PREVIOUS PRIVATE TEST')
        with self.assertRaises(FileExistsError):
            self.audit(private_scene_output=output, write_private=True)
        self.assertEqual(output.read_bytes(), b'PREVIOUS PRIVATE TEST')

    def test_native_cli_private_export_is_explicit_and_redacted(self):
        from carbon_pc_first_model_scene_rebind import main
        output = self.root / 'cli-owner-private.pcscene'
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141',
            '--private-candidate', str(self.candidate),
            '--info-index', '0',
            '--private-scene-output', str(output),
            '--write-private',
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        self.assertTrue(output.is_file())
        decoded = json.loads(printed.call_args.args[0])
        self.assertTrue(decoded['private_scene_export']['private_scene_created'])
        self.assertNotIn(str(output), json.dumps(decoded))

    def test_missing_section_refused(self):
        with self.assertRaises(ValueError):
            self.audit(section=143)

    def test_out_of_range_info_index_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.audit(index=2)

    def test_bad_bundle_pair_name_or_directory_refused(self):
        wrong = self.root / 'L5RB.BUN'
        wrong.write_bytes(self.bun.read_bytes())
        with self.assertRaisesRegex(ValueError, 'TRACKS'):
            self.audit(carbon_l5rb_bun=wrong)
        wrong2 = self.tracks / 'WRONG.BUN'
        wrong2.write_bytes(self.stream.read_bytes())
        with self.assertRaisesRegex(ValueError, 'TRACKS'):
            self.audit(carbon_stream_l5rb_bun=wrong2)

    def test_corrupt_source_stream_postscene_controls_refused(self):
        # The outer 92-byte index is intact, but the native Carbon PC
        # post-scene controls have invalid framing. Never rebind it.
        source = self.stream.read_bytes()
        pos = source.find(struct.pack('<I', 0x37220))
        self.assertGreater(pos, 0)
        broken = bytearray(source)
        broken[pos:pos+4] = b'\xff\xff\xff\xff'
        self.stream.write_bytes(broken)
        with self.assertRaises(ValueError):
            self.audit()

    def test_bad_source_table_rejected(self):
        bad = bytearray(self.bun.read_bytes())
        bad[0:4] = b'xxxx'
        self.bun.write_bytes(bad)
        with self.assertRaises(ValueError):
            self.audit()

    def test_unsupported_section_id_or_boolean_rejected(self):
        for bad in (0, 240, True, '141', None):
            with self.subTest(section=repr(bad)), self.assertRaises(ValueError):
                self.audit(section=bad)

    def test_original_files_not_replaced_with_candidate(self):
        # The entire operation remains read-only even with a successful
        # source pair and correct model/instance patch.
        files_before = {p: p.read_bytes()
                        for p in (self.bun, self.stream, self.candidate)}
        self.audit()
        files_after = {p: p.read_bytes()
                       for p in (self.bun, self.stream, self.candidate)}
        self.assertEqual(files_before, files_after)
        self.assertEqual(len(list(self.root.glob('**/*pcscene'))), 0)

    def test_cli_uses_owner_native_rb_section_without_export(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141',
            '--private-candidate', str(self.candidate),
            '--info-index', '0',
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        public_report = json.loads(printed.call_args.args[0])
        self.assertTrue(public_report['original_carbon_scene_extracted_without_writing'])
        self.assertNotIn(str(self.bun), json.dumps(public_report))
        self.assertNotIn(str(self.candidate), json.dumps(public_report))

    def test_cli_requires_paired_source_flags(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--private-candidate', str(self.candidate),
            '--info-index', '0',
        ]
        with patch('sys.argv', args), patch('sys.stderr'):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)



class V22NativeSourceClosureIntegrationTests(unittest.TestCase):
    """Source-pinned V21+V22 check using a fully indexed original-free pack."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.tracks = self.root / 'Carbon' / 'TRACKS'
        self.tracks.mkdir(parents=True)
        self.bun = self.tracks / 'L5RB.BUN'
        self.stream = self.tracks / 'STREAML5RB.BUN'
        self.candidate = self.root / 'undercover.pcchunk'
        self.nativefile = self.root / 'carbon-native.bin'
        self.candidate.write_bytes(CANDIDATE)
        self.make_native(101)

    @staticmethod
    def original_free_native_geometry(identity):
        from undercover_pc_geometry_bridge import convert_decoded_ps2_model
        xyz = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
        uv = ((0., 0.), (1., 0.), (0., 1.))
        return convert_decoded_ps2_model(
            identity, (IMG1,), xyz, uv, ((0, 1, 2),), (0,), None)[0]

    def make_native(self, model_id):
        from test_carbon_pc_native_postscene_layout_gate import (
            chunk, native_tail,
        )
        from carbon_pc_native_postscene_layout_gate import TEXTURE
        root = self.original_free_native_geometry(model_id)
        self.nativefile.write_bytes(root)
        prefix = chunk(TEXTURE, bytes(8)) + root
        # The measured PC source permits a bounded zero frame between
        # native geometry and the scene. Align scene root exactly to 16.
        padding = (-(len(prefix) + 8)) % 16
        native_section = (prefix + chunk(0, bytes(padding)) +
                          scene(pc=True, infos=2, inst=2) + native_tail(1))
        from carbon_pc_native_postscene_layout_gate import profile_carbon_section
        self.assertEqual(profile_carbon_section(native_section)['native_postscene_control_groups'], 1)
        b, st = fixture_stream_and_bundle([(141, native_section)])
        self.bun.write_bytes(b)
        self.stream.write_bytes(st)

    def run_original(self, **changes):
        kwargs = {
            'carbon_l5rb_bun': self.bun,
            'carbon_stream_l5rb_bun': self.stream,
            'candidate_path': self.candidate,
            'section_id': 141, 'info_index': 0,
            'audit_model_closure': True,
        }
        kwargs.update(changes)
        return inspect_owner_original_carbon_rb_section(**kwargs)

    def test_original_source_geometry_closes_all_active_scene_models(self):
        original = (self.bun.read_bytes(), self.stream.read_bytes(),
                    self.candidate.read_bytes())
        report = self.run_original()
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')
        self.assertEqual(report['model_reference_closure']['source_native_geometry_roots_supplied'], 1)
        self.assertTrue(report['model_reference_closure'][
            'all_referenced_instance_model_slots_backed_in_supplied_roots'])
        self.assertFalse(report['model_reference_closure']['undercover_object_rendered_in_game'])
        self.assertEqual(original, (self.bun.read_bytes(), self.stream.read_bytes(),
                                    self.candidate.read_bytes()))
        self.assertNotIn(str(self.tracks), json.dumps(report))

    def test_original_source_geometry_missing_model_reports_incomplete(self):
        self.make_native(777)
        report = self.run_original()
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'INCOMPLETE_REFERENCES_IN_SUPPLIED_NATIVE_GEOMETRY')
        self.assertEqual(report['model_reference_closure'][
            'referenced_model_identities_unresolved_in_supplied_roots'], 1)

    def test_incomplete_closure_blocks_opt_in_private_scene_export(self):
        self.make_native(777)
        destination = self.root / 'should-not-export.pcscene'
        with self.assertRaisesRegex(ValueError, 'incomplete model closure'):
            self.run_original(private_scene_output=destination, write_private=True)
        self.assertFalse(destination.exists())

    def test_complete_closure_permits_private_scene_export_with_caveats(self):
        target = self.root / 'rebound.pcscene'
        report = self.run_original(
            private_scene_output=target, write_private=True)
        self.assertTrue(target.exists())
        self.assertTrue(report['private_scene_export']['private_scene_created'])
        self.assertFalse(report['private_scene_export']['carbon_stream_sector_complete'])
        self.assertFalse(report['model_reference_closure']['external_loader_model_registration_verified'])
        self.assertNotIn(str(target), json.dumps(report))

    def test_additional_original_root_can_supply_missing_native_model(self):
        self.make_native(777)
        extra = self.original_free_native_geometry(101)
        report = self.run_original(additional_native_geometry_roots=(extra,))
        self.assertEqual(report['model_reference_closure']['source_native_geometry_roots_supplied'], 2)
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')

    def test_duplicate_original_geometry_identity_is_blocked(self):
        root = self.nativefile.read_bytes()
        report = self.run_original(additional_native_geometry_roots=(root,))
        self.assertEqual(report['model_reference_closure']['source_native_repeated_model_identities'], 1)
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID')

    def test_legacy_no_closure_flag_keeps_existing_v21_behavior(self):
        self.make_native(777)
        report = self.run_original(audit_model_closure=False)
        self.assertNotIn('model_reference_closure', report)
        self.assertFalse(report['native_carbon_stream_sector_complete'])

    def test_raw_scene_uses_owner_supplied_geometry_root(self):
        source = self.root / 'original.pcscene'
        source.write_bytes(scene(pc=True, infos=2, inst=2))
        report = inspect_private_scene_and_candidate(
            source, self.candidate, 0, audit_model_closure=True,
            native_carbon_geometry_roots=(self.nativefile.read_bytes(),))
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')

    def test_raw_scene_requires_supplied_geometry_for_closure(self):
        source = self.root / 'original.pcscene'
        source.write_bytes(scene(pc=True, infos=2, inst=2))
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(
                source, self.candidate, 0, audit_model_closure=True)

    def test_extra_roots_without_audit_flag_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'require --audit-model-closure'):
            self.run_original(audit_model_closure=False,
                              additional_native_geometry_roots=(self.nativefile.read_bytes(),))

    def test_cli_audits_original_section_local_geometry(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141', '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--audit-model-closure',
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        report = json.loads(printed.call_args.args[0])
        self.assertEqual(report['model_reference_closure']['source_native_geometry_roots_supplied'], 1)
        self.assertFalse(report['model_reference_closure']['native_carbon_stream_sector_complete'])

    def test_cli_extra_native_root_requires_closure_option(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141', '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--native-carbon-geometry-root', str(self.nativefile),
        ]
        with patch('sys.argv', args), patch('sys.stderr'):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)

    def test_cli_raw_scene_plus_external_owner_native_root(self):
        from carbon_pc_first_model_scene_rebind import main
        source = self.root / 'extracted.pcscene'
        source.write_bytes(scene(pc=True, infos=2, inst=2))
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-pc-scene-root', str(source),
            '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--native-carbon-geometry-root', str(self.nativefile),
            '--audit-model-closure',
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        report = json.loads(printed.call_args.args[0])
        self.assertEqual(report['model_reference_closure']['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')



if __name__ == '__main__':
    unittest.main()
