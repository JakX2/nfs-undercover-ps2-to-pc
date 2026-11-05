"""Synthetic-only checks for source-authenticated face/UV/texture joining."""
import unittest
from unittest.mock import patch
from triangle_corner_uv_control import compare_controls

P = ((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
U = ((.21,.31),(.46,.68),(.73,.89))
F = ((0,1,2),)
A = (P,U,F,(0,))


class FaceCornerOriginalControlTests(unittest.TestCase):
    @patch('triangle_corner_uv_control.pc_geometry_attributes', return_value=A)
    @patch('triangle_corner_uv_control.ps2_geometry_attributes', return_value=A)
    def test_matched_model(self, *_):
        m=[(123, {'texture_table': (77,)})]
        r=compare_controls({123:object()}, {123:object()}, m, m)
        self.assertEqual(r['ps2_faces_assigned_distinct_pc_faces'],1)

    def test_hash_mismatch_rejected(self):
        m=[(123, {'texture_table': (77,)})]
        with self.assertRaisesRegex(ValueError,'model hash sets disagree'):
            compare_controls({123:object()},{321:object()},m,m)

    def test_mismatched_local_texture_table_rejected(self):
        m=[(123, {'texture_table': (77,)})]
        n=[(123, {'texture_table': (88,)})]
        with self.assertRaisesRegex(ValueError,'texture hash tables differ'):
            compare_controls({123:object()},{123:object()},m,n)

    def test_duplicate_model_hash_material_rejected(self):
        m=[(123, {'texture_table': (77,)}),(123, {'texture_table': (77,)})]
        with self.assertRaisesRegex(ValueError,'material model identities'):
            compare_controls({123:object()},{123:object()},m,m)

    @patch('triangle_corner_uv_control.pc_geometry_attributes', return_value=A)
    @patch('triangle_corner_uv_control.ps2_geometry_attributes', return_value=(P,((.1,.4),U[1],U[2]),F,(0,)))
    def test_disagreeing_face_uv_rejected(self, *_):
        m=[(123, {'texture_table': (77,)})]
        with self.assertRaisesRegex(ValueError,'fails face-corner'):
            compare_controls({123:object()},{123:object()},m,m)

    @patch('triangle_corner_uv_control.pc_geometry_attributes', return_value=(P,U,((0,1,2),(0,1,2)),(0,0)))
    @patch('triangle_corner_uv_control.ps2_geometry_attributes', return_value=A)
    def test_extra_pc_triangle_counted(self, *_):
        m=[(123, {'texture_table': (77,)})]
        r=compare_controls({123:object()},{123:object()},m,m)
        self.assertEqual(r['unmatched_pc_faces'],1)
        self.assertEqual(r['models_with_equal_face_counts'],0)


if __name__=='__main__': unittest.main()
