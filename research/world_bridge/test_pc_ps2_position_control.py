"""Synthetic-only control tests for PC/PS2 model identity and XYZ witness joins."""
import unittest
from unittest.mock import patch
from pc_ps2_position_control import compare_source_models


class PCPS2PositionControlTests(unittest.TestCase):
    @patch('pc_ps2_position_control.pc_positions', return_value=[(0.,0.,0.),(1.,0.,0.)])
    @patch('pc_ps2_position_control.ps2_positions', return_value=[(0.005,0.,0.),(1.004,0.,0.)])
    def test_same_hash_geometry_clouds_match(self, *_):
        r=compare_source_models({101:object()},{101:object()})
        self.assertEqual(r['paired_models_passed'],1)
        self.assertEqual((r['pc_vertex_positions'],r['ps2_vertex_occurrences']),(2,2))

    def test_different_model_sets_rejected(self):
        with self.assertRaisesRegex(ValueError,'identical indexed hash sets'):
            compare_source_models({101:object()},{102:object()})

    def test_empty_models_rejected(self):
        with self.assertRaisesRegex(ValueError,'identical indexed hash sets'):
            compare_source_models({}, {})

    @patch('pc_ps2_position_control.pc_positions', return_value=[(0.,0.,0.)])
    @patch('pc_ps2_position_control.ps2_positions', return_value=[(1.,0.,0.)])
    def test_unmatched_xyz_rejected(self, *_):
        with self.assertRaisesRegex(ValueError,'fails XYZ cloud matching'):
            compare_source_models({101:object()},{101:object()})


if __name__=='__main__':
    unittest.main()
