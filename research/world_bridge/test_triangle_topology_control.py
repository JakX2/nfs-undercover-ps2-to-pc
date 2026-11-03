"""Synthetic-only end-to-end same-hash triangle count/identity gates."""
import unittest
from unittest.mock import patch
from triangle_topology_control import compare_solid_controls

PC=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.))
PS=((0.004,0.,0.),(1.004,0.,0.),(0.004,1.,0.),(1.004,1.,0.))

class TriangleModelTests(unittest.TestCase):
    @patch('triangle_topology_control.pc_faces',return_value=(PC,((0,1,2),)))
    @patch('triangle_topology_control.ps2_faces',return_value=(PS,((0,1,2),)))
    def test_same_model_has_unique_face_match(self,*_):
        got=compare_solid_controls({9:object()},{9:object()})
        self.assertEqual(got['ps2_triangles_uniquely_assigned'],1)
        self.assertEqual(got['models_with_identical_triangle_counts'],1)

    def test_model_identity_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity sets disagree'):
            compare_solid_controls({9:object()},{10:object()})

    def test_empty_model_group_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity sets disagree'):
            compare_solid_controls({}, {})

    @patch('triangle_topology_control.pc_faces',return_value=(PC,((0,1,2),)))
    @patch('triangle_topology_control.ps2_faces',return_value=(PS,((1,3,2),)))
    def test_wrong_face_connectivity_rejected(self,*_):
        with self.assertRaisesRegex(ValueError,'unmatched triangle geometry'):
            compare_solid_controls({9:object()},{9:object()})

    @patch('triangle_topology_control.pc_faces',return_value=(PC,((0,1,2),(1,3,2))))
    @patch('triangle_topology_control.ps2_faces',return_value=(PS,((0,1,2),)))
    def test_extra_pc_face_is_reported(self,*_):
        got=compare_solid_controls({9:object()},{9:object()})
        self.assertEqual(got['unused_pc_triangles_after_matching'],1)
        self.assertEqual(got['models_with_identical_triangle_counts'],0)

    @patch('triangle_topology_control.pc_faces',return_value=(PC,((0,1,2),)))
    @patch('triangle_topology_control.ps2_faces',return_value=(PS,((0,1,2),(0,1,2))))
    def test_insufficient_pc_faces_rejected(self,*_):
        with self.assertRaisesRegex(ValueError,'unmatched triangle geometry'):
            compare_solid_controls({9:object()},{9:object()})

if __name__=='__main__':unittest.main()
