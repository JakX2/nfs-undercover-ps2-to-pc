"""V23 original-free native Carbon PC RB geometry+texture material integration.

Synthetic 92-byte RB table, valid complete original PC texture and
geometry roots, source-shaped scenery and postscene control. No retail
assets, original names or private source paths are included.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from carbon_pc_first_model_scene_rebind import (
    inspect_owner_original_carbon_rb_section, inspect_private_scene_and_candidate,
)
from carbon_pc_native_postscene_layout_gate import profile_carbon_section
from test_carbon_pc_native_postscene_layout_gate import (
    chunk, scene, native_tail, fixture_stream_and_bundle,
)
from test_carbon_pc_first_model_stream_assembly import dxt5
from test_carbon_pc_first_model_scene_rebind import CANDIDATE
from test_carbon_pc_scene_material_closure_v23 import (
    NATIVE_MODEL, NATIVE_TEXTURE, OTHER_TEXTURE, native_geometry,
)

class OriginalPcSectionMaterialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.tracks = self.folder / 'Carbon' / 'TRACKS'
        self.tracks.mkdir(parents=True)
        self.bun = self.tracks / 'L5RB.BUN'
        self.stream = self.tracks / 'STREAML5RB.BUN'
        self.candidate = self.folder / 'converted.pcchunk'
        self.candidate.write_bytes(CANDIDATE)
        self.rebuild_source()

    def rebuild_source(self, source_texture_ids=(NATIVE_TEXTURE,),
                       source_model_material=NATIVE_TEXTURE):
        tex = dxt5(*source_texture_ids)
        geom = native_geometry(NATIVE_MODEL, (source_model_material,))
        prefix = tex + geom
        if len(tex) % 16:
            raise AssertionError('Original-free PC texture prefix not 16-byte aligned')
        padding = (-(len(prefix)+8)) % 16
        section = (prefix + chunk(0, bytes(padding)) +
                   scene(pc=True, infos=2, inst=2) + native_tail(1))
        assert profile_carbon_section(section)['native_postscene_control_groups'] == 1
        bundle, stream = fixture_stream_and_bundle([(141, section)])
        self.bun.write_bytes(bundle)
        self.stream.write_bytes(stream)

    def run_audit(self, **kwargs):
        params = dict(
            carbon_l5rb_bun=self.bun,
            carbon_stream_l5rb_bun=self.stream,
            candidate_path=self.candidate, section_id=141, info_index=0,
            audit_model_closure=True,
            audit_material_closure=True,
        )
        params.update(kwargs)
        return inspect_owner_original_carbon_rb_section(**params)

    def test_source_pair_proves_local_scenenative_material_identity_closure(self):
        private = (self.bun, self.stream, self.candidate)
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in private]
        report = self.run_audit()
        after = [(p.read_bytes(), p.stat().st_mtime_ns) for p in private]
        self.assertEqual(before, after)
        closure = report['material_reference_closure']
        self.assertEqual(closure['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')
        self.assertEqual(closure['native_pc_texture_roots_supplied'], 1)
        self.assertEqual(closure['native_pc_geometry_roots_supplied'], 1)
        self.assertEqual(closure['referenced_distinct_material_identities_from_backed_models'], 2)
        self.assertEqual(closure['referenced_material_identities_unresolved_in_supplied_textures'], 0)
        self.assertTrue(closure['all_active_scene_model_materials_have_supplied_images'])
        self.assertFalse(closure['carbon_loader_registered_resources_verified'])
        self.assertFalse(closure['undercover_model_rendered_inside_carbon_verified'])
        self.assertNotIn(str(self.tracks), json.dumps(report))

    def test_native_texture_missing_prevents_private_scene_export(self):
        self.rebuild_source(source_texture_ids=(OTHER_TEXTURE,))
        result = self.run_audit()
        self.assertEqual(result['model_reference_closure']['local_model_reference_gate'],
                         'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF')
        self.assertEqual(result['material_reference_closure']['local_material_closure_gate'],
                         'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES')
        target = self.folder / 'must-not-write.pcscene'
        with self.assertRaisesRegex(ValueError, 'incomplete material closure'):
            self.run_audit(private_scene_output=target, write_private=True)
        self.assertFalse(target.exists())

    def test_private_original_extra_texture_root_resolves_missing_native_material(self):
        self.rebuild_source(source_texture_ids=(OTHER_TEXTURE,))
        ext = dxt5(NATIVE_TEXTURE)
        result = self.run_audit(additional_native_texture_roots=(ext,))
        self.assertEqual(result['material_reference_closure']['native_pc_texture_roots_supplied'], 2)
        self.assertEqual(result['material_reference_closure']['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')

    def test_native_texture_collision_against_converted_dxt_blocks_export(self):
        from test_carbon_pc_first_model_stream_assembly import IMG1
        self.rebuild_source(source_texture_ids=(NATIVE_TEXTURE, IMG1))
        report = self.run_audit()
        self.assertEqual(report['material_reference_closure']['candidate_texture_identities_colliding_with_native'], 1)
        self.assertEqual(report['material_reference_closure']['local_material_closure_gate'],
                         'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY')
        target = self.folder / 'must-not-write.pcscene'
        with self.assertRaisesRegex(ValueError, 'incomplete material closure'):
            self.run_audit(private_scene_output=target, write_private=True)
        self.assertFalse(target.exists())

    def test_material_closure_private_export_only_after_both_gates_succeed(self):
        target = self.folder / 'one-local-scene.pcscene'
        report = self.run_audit(private_scene_output=target, write_private=True)
        self.assertTrue(target.is_file())
        self.assertTrue(report['private_scene_export']['private_scene_revalidated_on_disk'])
        self.assertEqual(report['material_reference_closure']['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')
        self.assertFalse(report['private_scene_export']['carbon_stream_sector_complete'])
        self.assertNotIn(str(target), json.dumps(report))

    def test_requires_model_closure_for_material_and_texture_roots(self):
        with self.assertRaisesRegex(ValueError, 'requires --audit-model-closure'):
            self.run_audit(audit_model_closure=False)
        with self.assertRaisesRegex(ValueError, 'require.*--audit-material-closure'):
            self.run_audit(audit_material_closure=False,
                           additional_native_texture_roots=(dxt5(OTHER_TEXTURE),))

    def test_unrequested_material_audit_preserves_v22_behavior(self):
        self.rebuild_source(source_texture_ids=(OTHER_TEXTURE,))
        report = self.run_audit(audit_material_closure=False)
        self.assertIn('model_reference_closure', report)
        self.assertNotIn('material_reference_closure', report)

    def test_raw_scene_requires_owner_supplied_texture_and_geometry(self):
        raw_scene = self.folder / 'source.pcscene'
        raw_scene.write_bytes(scene(pc=True, infos=2, inst=2))
        raw_geometry = native_geometry()
        with self.assertRaises(ValueError):
            inspect_private_scene_and_candidate(
                raw_scene, self.candidate, 0,
                audit_model_closure=True, audit_material_closure=True,
                native_carbon_geometry_roots=(raw_geometry,))
        report = inspect_private_scene_and_candidate(
            raw_scene, self.candidate, 0,
            audit_model_closure=True, audit_material_closure=True,
            native_carbon_geometry_roots=(raw_geometry,),
            native_carbon_texture_roots=(dxt5(NATIVE_TEXTURE),))
        self.assertEqual(report['material_reference_closure']['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')

    def test_original_source_section_texture_corruption_refused(self):
        damaged = bytearray(self.stream.read_bytes())
        # The synthetic source section begins on a 2048-byte boundary.
        damaged[2048+3] ^= 1  # Corrupt top-level PC texture tag.
        self.stream.write_bytes(damaged)
        with self.assertRaises(ValueError):
            self.run_audit()

    def test_cli_material_audit_uses_native_source_without_extra_root(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141', '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--audit-model-closure', '--audit-material-closure',
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        result = json.loads(printed.call_args.args[0])
        self.assertEqual(result['material_reference_closure']['native_pc_texture_roots_supplied'], 1)
        self.assertFalse(result['material_reference_closure']['native_carbon_sector_complete'])
        self.assertNotIn(str(self.candidate), printed.call_args.args[0])

    def test_cli_supplemental_pc_texture_root_is_strict_and_owner_local(self):
        from carbon_pc_first_model_scene_rebind import main
        self.rebuild_source(source_texture_ids=(OTHER_TEXTURE,))
        other = self.folder / 'native-tex.bin'
        other.write_bytes(dxt5(NATIVE_TEXTURE))
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141', '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--audit-model-closure', '--audit-material-closure',
            '--native-carbon-texture-root', str(other),
        ]
        with patch('sys.argv', args), patch('builtins.print') as printed:
            main()
        report = json.loads(printed.call_args.args[0])
        self.assertEqual(report['material_reference_closure']['native_pc_texture_roots_supplied'], 2)
        self.assertEqual(report['material_reference_closure']['local_material_closure_gate'],
                         'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF')

    def test_cli_texture_flags_without_material_option_rejected(self):
        from carbon_pc_first_model_scene_rebind import main
        args = [
            'carbon_pc_first_model_scene_rebind.py',
            '--carbon-game-bun', str(self.bun),
            '--carbon-game-stream', str(self.stream),
            '--section', '141', '--info-index', '0',
            '--private-candidate', str(self.candidate),
            '--audit-model-closure',
            '--native-carbon-texture-root', str(self.folder / 'bogus.bin'),
        ]
        with patch('sys.argv', args), patch('sys.stderr'):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)

if __name__ == '__main__':
    unittest.main()
