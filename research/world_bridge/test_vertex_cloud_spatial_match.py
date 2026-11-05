"""Synthetic-only tolerance and failure controls for position-cloud comparisons."""
import unittest
from vertex_cloud_spatial_match import directional_nearest, bidirectional_cloud_match


class VertexCloudSpatialTests(unittest.TestCase):
    def test_nearby_vertices_bidirectional(self):
        r=bidirectional_cloud_match([(0,0,0),(1,2,3)],[(0.006,0,0),(1.005,2,3)])
        self.assertTrue(r['both_directions_match'])
        self.assertEqual(r['ps2_to_pc']['points_checked'],2)

    def test_strict_tolerance_negative(self):
        r=bidirectional_cloud_match([(0,0,0)],[(0.02,0,0)])
        self.assertFalse(r['both_directions_match'])

    def test_second_cloud_missing_vertex(self):
        r=bidirectional_cloud_match([(0,0,0),(1,0,0)],[(0,0,0)])
        self.assertFalse(r['both_directions_match'])
        self.assertEqual(r['pc_to_ps2']['unmatched_within_tolerance'],1)
        self.assertEqual(r['ps2_to_pc']['unmatched_within_tolerance'],0)

    def test_duplicate_positions_are_accepted(self):
        r=bidirectional_cloud_match([(0,0,0),(0,0,0)],[(0,0,0)])
        self.assertTrue(r['both_directions_match'])
        self.assertEqual(r['pc_vertices'],2)

    def test_cross_adjacent_grid_boundary(self):
        r=directional_nearest([(0.0099,0.0099,0.0099)],[(0.0101,0.0101,0.0101)])
        self.assertTrue(r['all_points_have_nearby_targets'])

    def test_diagonal_distance_is_euclidean(self):
        r=directional_nearest([(0,0,0)],[(0.009,0.009,0.009)])
        self.assertEqual(r['unmatched_within_tolerance'],1)

    def test_negative_coordinate_cells(self):
        r=directional_nearest([(-1.001,-0.001,-2.0001)],[(-1.,0.,-2.)])
        self.assertEqual(r['unmatched_within_tolerance'],0)

    def test_exact_distance_zero(self):
        r=directional_nearest([(1.,2.,3.)],[(1.,2.,3.)])
        self.assertEqual(r['max_matching_witness_distance'],0.)

    def test_too_small_tolerance(self):
        with self.assertRaisesRegex(ValueError,'Tolerance'):
            directional_nearest([(0,0,0)],[(0,0,0)],0.)

    def test_nan_coordinates(self):
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            directional_nearest([(float('nan'),0,0)],[(0,0,0)])

    def test_empty_cloud_rejected(self):
        with self.assertRaisesRegex(ValueError,'nonempty'):
            bidirectional_cloud_match([],[(0,0,0)])

    def test_not_xyz(self):
        with self.assertRaisesRegex(ValueError,'non-XYZ'):
            directional_nearest([(0,0)],[(0,0,0)])


if __name__=='__main__':
    unittest.main()
