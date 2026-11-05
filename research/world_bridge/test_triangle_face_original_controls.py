"""Synthetic source-model control tests, no original game data or fixtures."""
from unittest.mock import patch
import unittest
from triangle_face_original_controls import compare_models, pc_triangle_faces
from test_pc_native_vertex_control import parts

A=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
B=((0.,0.,0.),(1.,0.,0.),(1.,1.,0.))

class OriginalControlSyntheticTests(unittest.TestCase):
    def test_native_index_to_triangle(self):
        faces=pc_triangle_faces(parts())
        self.assertEqual(len(faces),1)
        self.assertEqual(faces[0],((0.,0.,0.),(1.,0.,0.),(2.,0.,0.)))

    def test_two_native_buffers_do_not_share_offsets(self):
        faces=pc_triangle_faces(parts(((36,3),(52,3))))
        self.assertEqual(len(faces),2)
        self.assertEqual(faces[0],faces[1])

    @patch('triangle_face_original_controls.pc_triangle_faces',return_value=[A])
    @patch('triangle_face_original_controls.ps2_triangle_faces',return_value=[A])
    def test_model_passes(self,*_):
        res=compare_models({101:object()},{101:object()})
        self.assertEqual(res['models_with_all_faces_present_bidirectionally'],1)

    @patch('triangle_face_original_controls.pc_triangle_faces',return_value=[A,B])
    @patch('triangle_face_original_controls.ps2_triangle_faces',return_value=[A])
    def test_extra_pc_face_is_reported(self,*_):
        res=compare_models({101:object()},{101:object()})
        self.assertEqual(res['pc_to_ps2_unmatched_faces'],1)
        self.assertEqual(res['ps2_to_pc_unmatched_faces'],0)

    @patch('triangle_face_original_controls.pc_triangle_faces',return_value=[A])
    @patch('triangle_face_original_controls.ps2_triangle_faces',return_value=[A,B])
    def test_extra_ps2_face_is_reported(self,*_):
        res=compare_models({101:object()},{101:object()})
        self.assertEqual(res['ps2_to_pc_unmatched_faces'],1)

    def test_model_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'same indexed model'):
            compare_models({101:object()},{102:object()})

    def test_empty_model_sets_rejected(self):
        with self.assertRaisesRegex(ValueError,'same indexed model'):
            compare_models({}, {})

if __name__=='__main__':unittest.main()
