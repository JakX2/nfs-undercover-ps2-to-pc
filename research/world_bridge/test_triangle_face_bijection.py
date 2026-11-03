"""Synthetic-only robust triangle-to-triangle geometry and matching tests."""
import unittest
from triangle_face_bijection import match_triangle_faces as match

P=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))

class TriangleFaceTests(unittest.TestCase):
    def test_identical_single_triangle(self):
        r=match(P,[(0,1,2)],P,[(0,1,2)])
        self.assertTrue(r['every_ps2_triangle_has_distinct_pc_match'])
        self.assertEqual((r['relative_permutation_even'],r['relative_permutation_odd']),(1,0))

    def test_cyclic_vertex_rotation_same_winding(self):
        r=match(P,[(0,1,2)],P,[(1,2,0)])
        self.assertEqual((r['relative_permutation_even'],r['relative_permutation_odd']),(1,0))

    def test_reverse_winding_detected(self):
        r=match(P,[(0,1,2)],P,[(0,2,1)])
        self.assertEqual((r['relative_permutation_even'],r['relative_permutation_odd']),(0,1))

    def test_small_perturbation_matches(self):
        q=tuple((x+0.005,y,z) for x,y,z in P)
        r=match(P,[(0,1,2)],q,[(0,1,2)])
        self.assertTrue(r['every_ps2_triangle_has_distinct_pc_match'])
        self.assertLessEqual(r['max_corner_witness_distance'],0.01)

    def test_different_diagonal_rejected(self):
        q=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.))
        r=match(q,[(0,1,2)],q,[(0,1,3)])
        self.assertEqual(r['ps2_triangles_not_assigned'],1)
        self.assertEqual(r['ps2_triangles_with_no_geometric_candidate'],1)

    def test_different_triangle_with_same_centroid_is_rejected(self):
        q=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
        other=((-0.5,-0.5,0.),(1.5,0.,0.),(0.,1.5,0.))
        r=match(q,[(0,1,2)],other,[(0,1,2)])
        self.assertEqual(r['ps2_triangles_not_assigned'],1)

    def test_duplicated_console_triangles_need_distinct_pc_faces(self):
        r=match(P,[(0,1,2)],P,[(0,1,2),(0,1,2)])
        self.assertEqual(r['ps2_triangles_with_no_geometric_candidate'],0)
        self.assertEqual(r['ps2_triangles_not_assigned'],1)

    def test_duplicate_pc_and_ps2_triangles_can_pair(self):
        r=match(P,[(0,1,2),(0,1,2)],P,[(0,1,2),(0,1,2)])
        self.assertEqual(r['ps2_triangles_uniquely_assigned'],2)
        self.assertEqual(r['ps2_triangles_with_multiple_pc_candidates'],2)

    def test_extra_pc_triangles_counted(self):
        r=match(P,[(0,1,2),(0,1,2)],P,[(0,1,2)])
        self.assertEqual(r['unused_pc_triangles_after_matching'],1)
        self.assertFalse(r['equal_triangle_counts'])

    def test_augmenting_path_not_greedy(self):
        base=P
        pca=tuple((x,y,z) for x,y,z in base)
        pcb=tuple((x+0.014,y,z) for x,y,z in base)
        psa=tuple((x+0.006,y,z) for x,y,z in base)
        psb=tuple((x-0.007,y,z) for x,y,z in base)
        r=match(pca+pcb,[(0,1,2),(3,4,5)],psa+psb,[(0,1,2),(3,4,5)])
        self.assertEqual(r['ps2_triangles_uniquely_assigned'],2)
        self.assertEqual(r['ps2_triangles_with_multiple_pc_candidates'],1)

    def test_rejects_just_over_threshold(self):
        q=tuple((x+0.01001,y,z) for x,y,z in P)
        r=match(P,[(0,1,2)],q,[(0,1,2)])
        self.assertEqual(r['ps2_triangles_not_assigned'],1)

    def test_negative_coordinate_bins(self):
        p=((-2.,-3.,-4.),(-1.,-3.,-4.),(-2.,-2.,-4.))
        q=tuple((x+0.005,y,z) for x,y,z in p)
        self.assertEqual(match(p,[(0,1,2)],q,[(0,1,2)])['ps2_triangles_uniquely_assigned'],1)

    def test_nonfinite_coordinate_rejected(self):
        p=((float('nan'),0.,0.),(1.,0.,0.),(0.,1.,0.))
        with self.assertRaisesRegex(ValueError,'Invalid 3D'):
            match(p,[(0,1,2)],P,[(0,1,2)])

    def test_out_of_bounds_triangle_index_rejected(self):
        with self.assertRaisesRegex(ValueError,'Out-of-bounds'):
            match(P,[(0,1,3)],P,[(0,1,2)])

    def test_boolean_triangle_index_rejected(self):
        with self.assertRaisesRegex(ValueError,'Out-of-bounds'):
            match(P,[(0,True,2)],P,[(0,1,2)])

    def test_empty_faces_rejected(self):
        with self.assertRaisesRegex(ValueError,'Empty or excessive triangle'):
            match(P,[],P,[(0,1,2)])

    def test_empty_positions_rejected(self):
        with self.assertRaisesRegex(ValueError,'Empty or excessive vertex'):
            match([],[(0,1,2)],P,[(0,1,2)])

    def test_invalid_tolerance_rejected(self):
        with self.assertRaisesRegex(ValueError,'tolerance'):
            match(P,[(0,1,2)],P,[(0,1,2)],tolerance=0)

    def test_large_tolerance_rejected(self):
        with self.assertRaisesRegex(ValueError,'tolerance'):
            match(P,[(0,1,2)],P,[(0,1,2)],tolerance=10)

    def test_degenerate_faces_match_only_as_geometry(self):
        p=((0.,0.,0.),(1.,0.,0.),(1.,0.,0.))
        r=match(p,[(0,1,2)],p,[(0,1,2)])
        self.assertEqual(r['ps2_triangles_uniquely_assigned'],1)

if __name__=='__main__':unittest.main()
