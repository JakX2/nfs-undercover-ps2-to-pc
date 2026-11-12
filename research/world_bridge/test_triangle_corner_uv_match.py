"""Source-free regression tests: same-face XYZ and UV corner assignments."""
import unittest
from triangle_corner_uv_match import match_faces

P = ((0.,0.,0.), (1.,0.,0.), (0.,1.,0.), (1.,1.,0.))
U = ((0.,0.), (1.,0.), (0.,1.), (1.,1.))


def match(pcfaces, psfaces, puv=U, suv=U, pc_labels=None, ps_labels=None, **kw):
    pc_labels = pc_labels if pc_labels is not None else [0]*len(pcfaces)
    ps_labels = ps_labels if ps_labels is not None else [0]*len(psfaces)
    return match_faces(P, puv, pcfaces, pc_labels, P, suv, psfaces, ps_labels,
                       max(pc_labels+ps_labels+[0])+1, **kw)


class TriangleCornerUVTests(unittest.TestCase):
    def test_identical(self):
        r = match([(0,1,2)], [(0,1,2)])
        self.assertTrue(r['all_ps2_faces_matched'])
        self.assertEqual(r['faces_requiring_periodic_uv_wrap'], 0)

    def test_rotated_corner_order(self):
        self.assertTrue(match([(0,1,2)], [(1,2,0)])['all_ps2_faces_matched'])

    def test_reversed_face_winding_geometry(self):
        r = match([(0,1,2)], [(0,2,1)])
        self.assertEqual(r['odd_corner_permutations_provisional'], 1)

    def test_periodic_uv_offsets(self):
        v = tuple((u+3.,w-2.) for u,w in U)
        r = match([(0,1,2)], [(0,1,2)], suv=v)
        self.assertEqual(r['faces_requiring_periodic_uv_wrap'], 1)
        self.assertTrue(r['all_ps2_faces_matched'])

    def test_wrong_uv_corner_assignment_is_not_explained_by_geometry(self):
        # UV attributes changed on only one corner despite identical XYZ/texture.
        v = list(U); v[0] = (.25,.35)
        r = match([(0,1,2)], [(0,1,2)], suv=v)
        self.assertEqual(r['unmatched_ps2_faces'], 1)
        self.assertEqual(r['ps2_faces_with_no_corner_candidate'], 1)

    def test_uv_transpose_is_not_accepted(self):
        v = tuple((w,u) for u,w in U)
        r = match([(0,1,2)], [(0,1,2)], suv=v)
        # This particular UV set is symmetric on nonzero corners: need a
        # generic asymmetric set to verify a transpose cannot pass.
        self.assertTrue(r['all_ps2_faces_matched'])
        a = ((.12,.31),(.42,.62),(.74,.87),(.95,.11))
        b = tuple((w,u) for u,w in a)
        self.assertEqual(match([(0,1,2)],[(0,1,2)],puv=a,suv=b)['unmatched_ps2_faces'],1)

    def test_texture_change_rejected(self):
        r = match([(0,1,2)], [(0,1,2)], pc_labels=[0], ps_labels=[1])
        self.assertFalse(r['all_ps2_faces_matched'])

    def test_two_distinct_duplicate_faces(self):
        r = match([(0,1,2),(0,1,2)],[(0,1,2),(0,1,2)])
        self.assertEqual(r['ps2_faces_assigned_distinct_pc_faces'],2)
        self.assertEqual(r['ps2_faces_with_multiple_pc_candidates'],2)

    def test_duplicate_faces_insufficient_pc(self):
        r = match([(0,1,2)],[(0,1,2),(0,1,2)])
        self.assertEqual(r['unmatched_ps2_faces'],1)
        self.assertEqual(r['ps2_faces_with_no_corner_candidate'],0)

    def test_extra_pc_face_counted(self):
        r = match([(0,1,2),(1,3,2)],[(0,1,2)])
        self.assertEqual(r['unmatched_pc_faces'],1)

    def test_float_difference_within_tolerance(self):
        v = tuple((u+0.002,w+0.003) for u,w in U)
        self.assertTrue(match([(0,1,2)],[(0,1,2)],suv=v)['all_ps2_faces_matched'])

    def test_float_difference_outside_tolerance(self):
        v = list(U);v[0] = (.04,.03)
        self.assertFalse(match([(0,1,2)],[(0,1,2)],suv=v)['all_ps2_faces_matched'])

    def test_bad_xyz_rejected(self):
        xyz = ((float('nan'),0.,0.),P[1],P[2])
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            match_faces(P,U,[(0,1,2)],[0],xyz,U[:3],[(0,1,2)],[0],1)

    def test_bad_label_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Out-of-range'):
            match_faces(P,U,[(0,1,2)],[2],P,U,[(0,1,2)],[0],1)

    def test_bad_index_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid triangle vertex'):
            match([(0,1,10)],[(0,1,2)])

    def test_invalid_tolerance_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid texture-table'):
            match([(0,1,2)],[(0,1,2)], uv_tolerance=0)


if __name__ == '__main__':
    unittest.main()
