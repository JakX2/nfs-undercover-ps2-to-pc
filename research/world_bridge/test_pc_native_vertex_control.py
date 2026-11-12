"""Synthetic-only PC geometry record/vertex-index format validation tests."""
import math
import struct
import unittest
from pc_native_vertex_control import inspect_pc_solid


def pack_vertex(x, stride=36, tangent=(0.0, 1.0, 0.0), hand=1.0,
                normal=(0.0, 0.0, 1.0), uv=(0.25, 0.75)):
    base = struct.pack('<3f3fI2f', float(x), 0.0, 0.0, *normal, 0xff112233, *uv)
    if stride == 52:
        base += struct.pack('<3ff', *tangent, hand)
    return base


def parts(layout=((36, 3),), invalid_index=False, bad_bbox=False):
    """A source-free fixture: one mesh and one triangle for each buffer."""
    meshes = bytearray()
    triangle_indices = []
    vertex_chunks = []
    next_index = 0
    for stride, nverts in layout:
        vertices = [pack_vertex(j, stride) for j in range(nverts)]
        vertex_chunks.append((0x134b01, b'\x11'*4+b''.join(vertices)))
        mesh = bytearray(144)
        struct.pack_into('<6f', mesh, 0,
                         -0.005, -0.005, -0.005,
                         float(nverts-1)+0.005+(1 if bad_bbox else 0), 0.005, 0.005)
        struct.pack_into('<I', mesh, 0x40, nverts)
        struct.pack_into('<I', mesh, 0x60, 1)
        struct.pack_into('<I', mesh, 0x64, next_index)
        struct.pack_into('<I', mesh, 0x7c, 3)
        meshes.extend(mesh)
        triangle_indices.extend((0, 1, nverts if invalid_index else 2))
        next_index += 3
    info = bytearray(b'\x11'*4 + bytes(52))
    struct.pack_into('<I',info,4+8,0x12)
    struct.pack_into('<I',info,4+16,len(layout))
    struct.pack_into('<I',info,4+44,len(triangle_indices))
    index = struct.pack('<'+str(len(triangle_indices))+'H',*triangle_indices)
    index += bytes((-len(index))%4)
    return ([(0x134900,bytes(info)),(0x134b02,b'\x11'*4+bytes(meshes)),
             (0x134b03,b'\x11'*8+index)] + vertex_chunks +
             [(0x134c02,b'SYNTHETIC\0')]*len(layout))


class NativePCVertexTests(unittest.TestCase):
    def test_single_36(self):
        got=inspect_pc_solid(parts())
        self.assertEqual((got['vertices_stride_36'],got['mesh_records'],got['triangle_indices']),(3,1,3))
        self.assertEqual(got['vertex_buffers_stride_36'],1)

    def test_single_52(self):
        got=inspect_pc_solid(parts(((52,3),)))
        self.assertEqual(got['vertices_stride_52'],3)
        self.assertEqual(got['tangent_sign_1'],3)

    def test_mixed_buffers_indices_reset(self):
        got=inspect_pc_solid(parts(((36,3),(52,3))))
        self.assertEqual((got['bounded_mesh_records'],got['vertex_buffers_stride_52']),(2,1))
        self.assertTrue(got['every_index_within_its_mesh_vertex_span'])

    def test_all_nan_tangent_sentinel(self):
        p=parts(((52,3),))
        buffer=bytearray(p[3][1])
        struct.pack_into('<3ff',buffer,4+36,float('nan'),float('nan'),float('nan'),0.0)
        p[3]=(0x134b01,bytes(buffer))
        self.assertEqual(inspect_pc_solid(p)['tangent_nan_zero_sign_sentinels'],1)

    def test_reject_partial_nan_tangent(self):
        p=parts(((52,3),));b=bytearray(p[3][1])
        struct.pack_into('<f',b,4+36,float('nan'));p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'Invalid PC tangent'):
            inspect_pc_solid(p)

    def test_reject_wrong_tangent_sign(self):
        p=parts(((52,3),));b=bytearray(p[3][1])
        struct.pack_into('<f',b,4+48,0.25);p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'Invalid PC tangent'):
            inspect_pc_solid(p)

    def test_reject_nonunit_tangent(self):
        p=parts(((52,3),));b=bytearray(p[3][1])
        struct.pack_into('<3f',b,4+36,5.,0.,0.);p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'unit/perpendicular'):
            inspect_pc_solid(p)

    def test_reject_nonorthogonal_tangent(self):
        p=parts(((52,3),));b=bytearray(p[3][1])
        struct.pack_into('<3f',b,4+36,0.,0.,1.);p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'unit/perpendicular'):
            inspect_pc_solid(p)

    def test_reject_outside_mesh_index(self):
        with self.assertRaisesRegex(ValueError,'mapping is not unique'):
            inspect_pc_solid(parts(invalid_index=True))

    def test_reject_wrong_bbox(self):
        with self.assertRaisesRegex(ValueError,'disagree with record bounds'):
            inspect_pc_solid(parts(bad_bbox=True))

    def test_reject_wrong_normal(self):
        p=parts();b=bytearray(p[3][1]);struct.pack_into('<3f',b,4+12,0.,0.,0.)
        p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'normal'):
            inspect_pc_solid(p)

    def test_reject_nan_uv(self):
        p=parts();b=bytearray(p[3][1]);struct.pack_into('<f',b,4+28,float('nan'))
        p[3]=(0x134b01,bytes(b))
        with self.assertRaisesRegex(ValueError,'Nonfinite PC vertex'):
            inspect_pc_solid(p)

    def test_reject_noncontiguous_index_offset(self):
        p=parts(((36,3),(36,3)));b=bytearray(p[1][1]);struct.pack_into('<I',b,4+144+0x64,0)
        p[1]=(0x134b02,bytes(b))
        with self.assertRaisesRegex(ValueError,'Noncontiguous'):
            inspect_pc_solid(p)

    def test_reject_triangle_count_mismatch(self):
        p=parts();b=bytearray(p[1][1]);struct.pack_into('<I',b,4+0x60,2)
        p[1]=(0x134b02,bytes(b))
        with self.assertRaisesRegex(ValueError,'Noncontiguous or inconsistent'):
            inspect_pc_solid(p)


if __name__=='__main__':
    unittest.main()
