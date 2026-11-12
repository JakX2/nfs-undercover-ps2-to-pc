"""Synthetic-only same-model XYZ/periodic UV integration gates."""
import unittest
from unittest.mock import patch
from uv_attribute_control import compare_solid_uv

XYZ=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
UV=((.2,.3),(.5,.6),(.7,.8))

class UVModelControlTests(unittest.TestCase):
    @patch('uv_attribute_control.pc_attributes',return_value=(XYZ,UV))
    @patch('uv_attribute_control.ps2_attributes',return_value=(XYZ,UV))
    def test_same_attributes_pass(self,*_):
        r=compare_solid_uv({1:object()},{1:object()})
        self.assertEqual(r['pc_to_ps2_vertex_records'],3)
        self.assertTrue(r['all_vertex_xyz_and_periodic_uv_pairs_matched'])

    @patch('uv_attribute_control.pc_attributes',return_value=(XYZ,UV))
    @patch('uv_attribute_control.ps2_attributes',return_value=(XYZ,tuple((u+2,v-1) for u,v in UV)))
    def test_whole_uv_tile_offsets_pass(self,*_):
        r=compare_solid_uv({1:object()},{1:object()})
        self.assertEqual(r['pc_to_ps2_integer_uv_tile_offset_rescues'],3)

    def test_unknown_model_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'same-hash solid sets differ'):
            compare_solid_uv({1:object()},{2:object()})

    def test_empty_control_rejected(self):
        with self.assertRaisesRegex(ValueError,'same-hash solid sets differ'):
            compare_solid_uv({}, {})

    @patch('uv_attribute_control.pc_attributes',return_value=(XYZ,UV))
    @patch('uv_attribute_control.ps2_attributes',return_value=(XYZ,tuple((u+.25,v) for u,v in UV)))
    def test_changed_uv_assignment_is_rejected(self,*_):
        with self.assertRaisesRegex(ValueError,'bidirectional XYZ/UV'):
            compare_solid_uv({1:object()},{1:object()})

    @patch('uv_attribute_control.pc_attributes',return_value=(XYZ,UV))
    @patch('uv_attribute_control.ps2_attributes',return_value=(XYZ[:2],UV[:2]))
    def test_missing_ps2_vertex_rejected(self,*_):
        with self.assertRaisesRegex(ValueError,'bidirectional XYZ/UV'):
            compare_solid_uv({1:object()},{1:object()})

if __name__=='__main__':unittest.main()
