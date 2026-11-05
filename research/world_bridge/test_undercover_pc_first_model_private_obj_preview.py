"""Source-free synthetic V11 PC-mesh OBJ and fail-closed owner-output controls."""
from pathlib import Path
import tempfile
import unittest
from undercover_pc_first_model_private_obj_preview import (
    private_obj_text, write_private_obj, audit_original_private_obj)

XYZ=((0.0,0.0,0.0),(1.0,0.0,0.0),(1.0,1.0,0.0),(0.0,1.0,0.0))
UV=((0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0))
FACES=((0,1,2),(0,2,3))
LABELS=(0,1)

class OBJTest(unittest.TestCase):
    def build(self, xyz=XYZ, uv=UV, faces=FACES, labels=LABELS):
        return private_obj_text(xyz,uv,faces,labels)

    def test_valid_materials_and_two_faces(self):
        a=self.build()
        self.assertEqual(sum(x.startswith('v ') for x in a.splitlines()),4)
        self.assertEqual(sum(x.startswith('vt ') for x in a.splitlines()),4)
        self.assertEqual(sum(x.startswith('f ') for x in a.splitlines()),2)
        self.assertIn('f 1/1 2/2 3/3',a)
        self.assertIn('usemtl UC_MATERIAL_001',a)

    def test_material_switches_preserve_sequence(self):
        a=self.build(labels=(1,0))
        self.assertLess(a.index('UC_MATERIAL_001'),a.index('UC_MATERIAL_000'))

    def test_same_material_not_repeated(self):
        self.assertEqual(self.build(labels=(0,0)).count('usemtl'),1)

    def test_deterministic(self):
        self.assertEqual(self.build(),self.build())

    def test_no_source_hashes_in_header(self):
        a=self.build()
        self.assertNotIn('0x',a)
        self.assertNotIn('SOURCE_MODEL_HASH',a)

    def test_invalid_vertex_count(self):
        with self.assertRaises(ValueError):self.build(xyz=XYZ[:2],uv=UV[:2])

    def test_uv_count_mismatch(self):
        with self.assertRaises(ValueError):self.build(uv=UV[:-1])

    def test_no_faces(self):
        with self.assertRaises(ValueError):self.build(faces=(),labels=())

    def test_label_count_mismatch(self):
        with self.assertRaises(ValueError):self.build(labels=(0,))

    def test_out_of_bounds_face(self):
        with self.assertRaises(ValueError):self.build(faces=((0,1,4),),labels=(0,))

    def test_negative_face(self):
        with self.assertRaises(ValueError):self.build(faces=((0,1,-1),),labels=(0,))

    def test_bool_face_index(self):
        with self.assertRaises(ValueError):self.build(faces=((False,1,2),),labels=(0,))

    def test_degenerate_face(self):
        with self.assertRaises(ValueError):self.build(faces=((0,0,2),),labels=(0,))

    def test_negative_material(self):
        with self.assertRaises(ValueError):self.build(labels=(0,-1))

    def test_oversized_material(self):
        with self.assertRaises(ValueError):self.build(labels=(0,127))

    def test_boolean_material(self):
        with self.assertRaises(ValueError):self.build(labels=(0,True))

    def test_nan_position(self):
        with self.assertRaises(ValueError):self.build(xyz=((float('nan'),0,0),)+XYZ[1:])

    def test_inf_uv(self):
        with self.assertRaises(ValueError):self.build(uv=((float('inf'),0),)+UV[1:])

    def test_invalid_row_shape(self):
        with self.assertRaises(ValueError):self.build(xyz=((0,0),)+XYZ[1:])

    def test_large_coordinate(self):
        with self.assertRaises(ValueError):self.build(xyz=((1e9,0,0),)+XYZ[1:])


class PrivateExportTest(unittest.TestCase):
    def text(self):
        return private_obj_text(XYZ,UV,FACES,LABELS)

    def test_exclusive_file_creation(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'one.obj'
            self.assertTrue(write_private_obj(target,self.text()))
            self.assertEqual(target.read_text(encoding='utf-8'),self.text())
            with self.assertRaises(ValueError):write_private_obj(target,self.text())

    def test_reject_output_in_game_root(self):
        with tempfile.TemporaryDirectory() as td:
            game=Path(td)/'CarbonPC';game.mkdir()
            with self.assertRaises(ValueError):write_private_obj(game/'test.obj',self.text())

    def test_reject_no_parent_dir(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):write_private_obj(Path(td)/'missing'/'one.obj',self.text())

    def test_reject_wrong_extension(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):write_private_obj(Path(td)/'test.exe',self.text())

    def test_reject_nonobj_text(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):write_private_obj(Path(td)/'test.obj','malicious text')

    def test_reject_symlink_output(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.obj';p.symlink_to(Path(td)/'absent.obj')
            with self.assertRaises(ValueError):write_private_obj(p,self.text())

    def test_default_audit_requires_existing_original(self):
        with self.assertRaises(ValueError):audit_original_private_obj('/not/real/undercover.zip')

    def test_export_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,'requires'):
            audit_original_private_obj('/not/real/undercover.zip',private_obj='/tmp/test.obj')

    def test_export_without_path_refused(self):
        with self.assertRaisesRegex(ValueError,'requires'):
            audit_original_private_obj('/not/real/undercover.zip',write_private=True)

    def test_boolean_export_flag_refused(self):
        with self.assertRaises(ValueError):
            audit_original_private_obj('/not/real/undercover.zip',write_private=1)


if __name__=='__main__':
    unittest.main()
