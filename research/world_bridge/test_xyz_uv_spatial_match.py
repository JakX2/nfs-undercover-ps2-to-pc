"""Synthetic-only XYZ/UV periodic seam and geometry mismatch controls."""
import unittest
from xyz_uv_spatial_match import directional_xyz_uv as check,bidirectional_xyz_uv as both
XYZ=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
UV=((0.25,0.75),(0.75,0.25),(0.5,0.5))

class XYZUVControlTests(unittest.TestCase):
    def test_identical_vertex_attributes(self):
        r=both(XYZ,UV,XYZ,UV)
        self.assertTrue(r['matches_both_directions'])
        self.assertEqual(r['pc_to_ps2']['integer_uv_tile_offset_rescues'],0)

    def test_fractional_quantization_within_tolerance(self):
        uv=tuple((a+0.001,b-0.001) for a,b in UV)
        self.assertTrue(both(XYZ,UV,XYZ,uv)['matches_both_directions'])

    def test_periodic_u_and_v_offsets(self):
        uv=tuple((a+1,b-2) for a,b in UV)
        r=both(XYZ,UV,XYZ,uv)
        self.assertTrue(r['matches_both_directions'])
        self.assertEqual(r['pc_to_ps2']['integer_uv_tile_offset_rescues'],3)

    def test_flipped_v_unmatched(self):
        target_uv=((.25,.15),(.75,.85),(.5,.7))
        r=check(XYZ,UV,XYZ,target_uv)
        self.assertEqual(r['missing_periodic_uv_witnesses'],3)

    def test_spatial_neighbor_required(self):
        shifted=tuple((x+10,y,z) for x,y,z in XYZ)
        r=check(XYZ,UV,shifted,UV)
        self.assertEqual(r['missing_xyz_witnesses'],3)

    def test_integer_wrapping_does_not_hide_noninteger_error(self):
        uv=tuple((a+1.1,b-2) for a,b in UV)
        r=check(XYZ,UV,XYZ,uv)
        self.assertEqual(r['missing_periodic_uv_witnesses'],3)

    def test_ambiguous_xyz_with_valid_uv_witness(self):
        xyz=((0.,0.,0.),(0.001,0.,0.))
        uv=((0.1,0.1),(0.9,0.9))
        r=check(((0.0005,0.,0.),),((0.9,0.9),),xyz,uv)
        self.assertTrue(r['all_vertices_have_xyz_and_periodic_uv_match'])

    def test_negative_xyz_boundary(self):
        r=check(((-0.001,0.,0.),),((0.,0.),),((0.001,0.,0.),),((1.,0.),))
        self.assertTrue(r['all_vertices_have_xyz_and_periodic_uv_match'])

    def test_reject_nan_uv(self):
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            check(XYZ,UV,XYZ,((0.,float('nan')),*UV[1:]))

    def test_reject_mismatched_uv_count(self):
        with self.assertRaisesRegex(ValueError,'counts disagree'):
            check(XYZ,UV,XYZ,UV[:2])

    def test_reject_bad_tolerance(self):
        with self.assertRaisesRegex(ValueError,'tolerance'):
            check(XYZ,UV,XYZ,UV,uv_tol=0)

    def test_bidirectional_mismatched_cloud(self):
        r=both(XYZ,UV,XYZ[:2],UV[:2])
        self.assertFalse(r['matches_both_directions'])

if __name__=='__main__':unittest.main()
