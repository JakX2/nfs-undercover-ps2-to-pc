"""Synthetic-only geometric face/winding comparator regression tests."""
import unittest
from triangle_face_spatial_match import directional_face_match, bidirectional_face_match

A=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
B=((0.,0.,0.),(1.,0.,0.),(1.,1.,0.))

class TriangleFaceSpatialTests(unittest.TestCase):
    def test_identical(self):
        r=bidirectional_face_match([A],[A]);self.assertTrue(r['all_pc_faces_have_ps2_counterparts'])
        self.assertTrue(r['all_ps2_faces_have_pc_counterparts'])
        self.assertFalse(r['exact_multiplicity_or_material_equality_proven'])

    def test_cyclic_winding_same(self):
        r=directional_face_match([A],[(A[1],A[2],A[0])])
        self.assertEqual((r['same_winding_only'],r['reversed_winding_only']),(1,0))

    def test_reversed_winding_detected(self):
        r=directional_face_match([A],[(A[0],A[2],A[1])])
        self.assertEqual((r['same_winding_only'],r['reversed_winding_only']),(0,1))

    def test_vertex_packing_jitter(self):
        jitter=((.005,0.,0.),(1.,.005,0.),(0.,1.,-.005))
        r=bidirectional_face_match([A],[jitter]);self.assertTrue(r['all_ps2_faces_have_pc_counterparts'])

    def test_missing_triangle_in_pc(self):
        r=bidirectional_face_match([A],[A,B])
        self.assertEqual((r['pc_to_ps2']['unmatched_faces'],r['ps2_to_pc']['unmatched_faces']),(0,1))

    def test_pc_extra_triangle(self):
        r=bidirectional_face_match([A,B],[A])
        self.assertEqual((r['pc_to_ps2']['unmatched_faces'],r['ps2_to_pc']['unmatched_faces']),(1,0))

    def test_centroid_same_but_shape_different(self):
        shifted=((0.,0.,0.),(2.,0.,0.),(-1.,1.,0.))
        r=directional_face_match([A],[shifted]);self.assertEqual(r['unmatched_faces'],1)

    def test_centroid_crosses_grid_boundary(self):
        tiny=((.0098,.0098,0.),(1.0098,.0098,0.),(.0098,1.0098,0.))
        small=((.0102,.0102,0.),(1.0102,.0102,0.),(.0102,1.0102,0.))
        self.assertEqual(directional_face_match([tiny],[small])['unmatched_faces'],0)

    def test_euclidean_tolerance_not_box(self):
        b=tuple((x+.009,y+.009,z+.009) for x,y,z in A)
        self.assertEqual(directional_face_match([A],[b])['unmatched_faces'],1)

    def test_negative_coordinates(self):
        s=tuple((-x-1,-y-1,-z-1) for x,y,z in A)
        r=directional_face_match([s],[s]);self.assertEqual(r['matched_faces'],1)

    def test_multiple_target_candidates_reported(self):
        r=directional_face_match([A],[A,A]);self.assertEqual(r['faces_with_multiple_matching_targets'],1)

    def test_multiplicity_not_claimed_even_if_both_directions_match(self):
        r=bidirectional_face_match([A,A],[A]);self.assertTrue(r['all_pc_faces_have_ps2_counterparts'])
        self.assertTrue(r['all_ps2_faces_have_pc_counterparts'])
        self.assertNotEqual(r['pc_faces'],r['ps2_faces'])

    def test_zero_area_winding_ambiguous(self):
        flat=((0.,0.,0.),(0.,0.,0.),(0.,0.,0.))
        r=directional_face_match([flat],[flat]);self.assertEqual(r['winding_ambiguous'],1)

    def test_invalid_nonfinite(self):
        with self.assertRaisesRegex(ValueError,'finite'):
            directional_face_match([((float('nan'),0,0),(1,0,0),(0,1,0))],[A])

    def test_invalid_non_xyz(self):
        with self.assertRaisesRegex(ValueError,'finite'):
            directional_face_match([((0,0),(1,0,0),(0,1,0))],[A])

    def test_invalid_empty(self):
        with self.assertRaisesRegex(ValueError,'nonempty'):
            directional_face_match([],[A])

    def test_invalid_tolerance(self):
        with self.assertRaisesRegex(ValueError,'tolerance'):
            directional_face_match([A],[A],0)

    def test_reject_nontriangle(self):
        with self.assertRaisesRegex(ValueError,'three vertices'):
            directional_face_match([A[:2]],[A])

    def test_one_winding_each_is_ambiguous(self):
        r=directional_face_match([A],[A,(A[0],A[2],A[1])]);self.assertEqual(r['winding_ambiguous'],1)

if __name__=='__main__':unittest.main()
