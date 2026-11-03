"""Source-free PC-shaped vertex/index fixture tests, using native readback."""
import unittest
import struct
from synthetic_pc_mesh_writer import make_pc_chunks
from pc_native_vertex_control import inspect_pc_solid


def tri(uv=None, texture=0, material='SYNTHETIC'):
    return dict(positions=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)),
                normals=((0.,0.,1.),)*3,
                uv=((0.,0.),(1.,0.),(0.,1.)) if uv is None else uv,
                triangles=((0,1,2),),texture_index=texture,material_name=material)


class SyntheticPCMeshTests(unittest.TestCase):
    def test_single_mesh_roundtrip_native_parser(self):
        chunks=make_pc_chunks([tri()])
        r=inspect_pc_solid(chunks)
        self.assertEqual((r['mesh_records'],r['triangle_count'],r['vertices_stride_36']), (1,1,3))
        self.assertTrue(r['every_index_within_its_mesh_vertex_span'])

    def test_two_materials_two_vertex_buffers(self):
        chunks=make_pc_chunks([tri(texture=0),tri(texture=1,material='DIFFERENT')])
        r=inspect_pc_solid(chunks)
        self.assertEqual((r['mesh_records'],r['vertex_buffers_stride_36'],r['triangle_count']), (2,2,2))

    def test_uv_seam_is_preserved_in_vertex_bytes(self):
        t=tri(uv=((.2,.3),(.4,.5),(.6,.7)))
        chunk=next(b for cid,b in make_pc_chunks([t]) if cid==0x134b01)
        self.assertAlmostEqual(struct.unpack_from('<f',chunk,4+28)[0],.2,places=6)
        self.assertAlmostEqual(struct.unpack_from('<f',chunk,4+36+28+4)[0],.5,places=6)

    def test_deterministic_same_input_bytes(self):
        self.assertEqual(make_pc_chunks([tri()]),make_pc_chunks([tri()]))

    def test_extra_unused_vertex_is_preserved(self):
        t=tri(); t['positions']+=((2.,2.,0.),);t['normals']+=((0.,0.,1.),);t['uv']+=((.2,.2),)
        self.assertEqual(inspect_pc_solid(make_pc_chunks([t]))['vertices_stride_36'],4)

    def test_reject_out_of_range_local_face(self):
        t=tri();t['triangles']=((0,1,3),)
        with self.assertRaisesRegex(ValueError,'Out-of-bounds'):
            make_pc_chunks([t])

    def test_reject_negative_texture_index(self):
        t=tri(texture=-1)
        with self.assertRaisesRegex(ValueError,'texture-table'):
            make_pc_chunks([t])

    def test_reject_bad_material_name(self):
        t=tri(material='bad\0name')
        with self.assertRaisesRegex(ValueError,'material name'):
            make_pc_chunks([t])

    def test_reject_missing_normal(self):
        t=tri();t['normals']=((0.,0.,1.),)*2
        with self.assertRaisesRegex(ValueError,'counts disagree'):
            make_pc_chunks([t])

    def test_reject_zero_normal(self):
        t=tri();t['normals']=((0.,0.,0.),)*3
        with self.assertRaisesRegex(ValueError,'Nonunit'):
            make_pc_chunks([t])

    def test_reject_nonfinite_uv(self):
        t=tri();t['uv']=((float('nan'),0.),)*3
        with self.assertRaisesRegex(ValueError,'Invalid UV'):
            make_pc_chunks([t])

    def test_reject_empty_mesh_list(self):
        with self.assertRaisesRegex(ValueError,'number of synthetic meshes'):
            make_pc_chunks([])

    def test_reject_empty_triangle_list(self):
        t=tri();t['triangles']=()
        with self.assertRaisesRegex(ValueError,'Missing synthetic triangles'):
            make_pc_chunks([t])


if __name__=='__main__':unittest.main()
