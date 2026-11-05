"""Synthetic-only checks for PC indexed triangles and PS2 strip byte budgets."""
import math
import struct
import unittest
from mesh_topology_control import (parse_pc_mesh,parse_ps2_mesh,filler_size,
    compare_topology,scan_geometry_pack_solids,parse_pc_mesh,PS2_STRIPS,
    PS2_STRIP_DATA,PC_MESH,PC_TRI_INDICES,PC_VERTEX,PC_MATERIAL)
from geometry_hash_control import PLATFORM_PC,PLATFORM_PS2


def chunk(cid, body):
    return struct.pack('<II',cid,len(body))+body


def pc_parts(meshes=1, nindices=3, flags=0x4000, vertex_size=36, nmaterials=None):
    info=bytearray(b'\x11'*4+bytes(48))
    struct.pack_into('<I',info,4+8,0x12)
    struct.pack_into('<I',info,4+12,flags)
    struct.pack_into('<I',info,4+16,meshes)
    struct.pack_into('<I',info,4+44,nindices)
    mesh=b'\x11'*4+bytes(144*meshes)
    indices=b'\x11'*8+bytes((2*nindices+3)//4*4)
    verts=b'\x11'*4+bytes(vertex_size)
    material=b'MAT\0'
    if nmaterials is None:nmaterials=meshes
    return [(PLATFORM_PC,bytes(info)),(PC_MESH,mesh),(PC_TRI_INDICES,indices),
            (PC_VERTEX,verts)]+[(PC_MATERIAL,material)]*nmaterials


def ps2_parts(strips=((3,1,0,2),),strip_bytes=32,flags=0,density=1.):
    info=struct.pack('<III',0x20,len(strips),strip_bytes)
    table=b'\x11'*4
    for nverts,npolys,offset,qsize in strips:
        table+=struct.pack('<HBBfHbbBBbb',flags,nverts,npolys,density,offset,0,0,qsize,0,0,0)
    return [(PLATFORM_PS2, b'\x11'*4+info),(PS2_STRIPS,table),
            (PS2_STRIP_DATA,b'\x11'*8+bytes(strip_bytes))]


def fake_geometry(namehash=123,platform=PLATFORM_PC):
    if platform==PLATFORM_PC: children=pc_parts()
    else: children=ps2_parts()
    s_header=b'\x11'*4+struct.pack('<3I',0,0,0)+struct.pack('<II',0x16,namehash)+bytes(64)
    s_body=chunk(0x134011,s_header)+chunk(0x134012,bytes(8))
    s_body+=chunk(0x80134100,b''.join(chunk(cid,data) for cid,data in children))
    solid=chunk(0x80134010,s_body)
    head=chunk(0x134002,bytes(144))+chunk(0x134003,struct.pack('<II',namehash,0))+chunk(0x80134008,b'')
    frame=bytes(8)+chunk(0x80134001,head)+solid
    return chunk(0x80134000,frame)


class MeshTopologySyntheticTests(unittest.TestCase):
    def test_pc_mesh_triangle_lengths(self):
        r=parse_pc_mesh(pc_parts())
        self.assertEqual((r['pc_mesh_records'],r['pc_triangle_indices'],r['pc_triangle_count']), (1,3,1))
        self.assertEqual(r['candidate_vertex_chunk_classes']['36_only'],1)

    def test_pc_multiple_meshes_and_materials(self):
        r=parse_pc_mesh(pc_parts(meshes=3,nindices=15))
        self.assertEqual((r['pc_mesh_records'],r['pc_material_chunks'],r['pc_triangle_count']),(3,3,5))

    def test_pc_52_only_candidate(self):
        r=parse_pc_mesh(pc_parts(vertex_size=52))
        self.assertEqual(r['candidate_vertex_chunk_classes']['52_only'],1)

    def test_pc_ambiguous_candidate(self):
        r=parse_pc_mesh(pc_parts(vertex_size=468))
        self.assertEqual(r['candidate_vertex_chunk_classes']['ambiguous'],1)

    def test_pc_even_and_odd_index_counts(self):
        self.assertEqual(parse_pc_mesh(pc_parts(nindices=6))['pc_triangle_count'],2)
        self.assertEqual(parse_pc_mesh(pc_parts(nindices=3))['pc_triangle_count'],1)

    def test_pc_reject_wrong_index_count(self):
        c=pc_parts();c[2]=(c[2][0],c[2][1][:-4])
        with self.assertRaisesRegex(ValueError,'index count'):
            parse_pc_mesh(c)

    def test_pc_reject_nontriangle_indices(self):
        with self.assertRaisesRegex(ValueError,'multiple of three'):
            parse_pc_mesh(pc_parts(nindices=4))

    def test_pc_reject_bad_mesh_stride(self):
        c=pc_parts();c[1]=(c[1][0],c[1][1][:-1])
        with self.assertRaisesRegex(ValueError,'144-byte stride'):
            parse_pc_mesh(c)

    def test_pc_reject_mismatched_material_count(self):
        with self.assertRaisesRegex(ValueError,'material-name'):
            parse_pc_mesh(pc_parts(nmaterials=2))

    def test_pc_reject_unsupported_vertex_stride(self):
        with self.assertRaisesRegex(ValueError,'neither 36 nor 52'):
            parse_pc_mesh(pc_parts(vertex_size=17))

    def test_pc_reject_missing_vertex(self):
        with self.assertRaisesRegex(ValueError,'Missing or unrecognized'):
            parse_pc_mesh([x for x in pc_parts() if x[0]!=PC_VERTEX])

    def test_pc_reject_missing_pc_info(self):
        with self.assertRaisesRegex(ValueError,'Missing PC platform'):
            parse_pc_mesh(pc_parts()[1:])

    def test_ps2_valid_strip(self):
        s=parse_ps2_mesh(ps2_parts())
        self.assertEqual((s['strip_entries'],s['strip_polygon_count'],s['strip_vertices_declared']),(1,1,3))

    def test_ps2_multiple_strips(self):
        s=parse_ps2_mesh(ps2_parts(strips=((4,2,0,1),(5,3,1,1))))
        self.assertEqual((s['strip_entries'],s['strip_polygon_count']),(2,5))

    def test_ps2_reject_outside_vif_data(self):
        with self.assertRaisesRegex(ValueError,'data range'):
            parse_ps2_mesh(ps2_parts(strips=((3,1,1,3),)))

    def test_ps2_reject_strip_table_length(self):
        s=ps2_parts();s[1]=(s[1][0],s[1][1]+b'Z')
        with self.assertRaisesRegex(ValueError,'byte count mismatch'):
            parse_ps2_mesh(s)

    def test_ps2_reject_strip_data_length(self):
        s=ps2_parts();s[2]=(s[2][0],s[2][1][:-1])
        with self.assertRaisesRegex(ValueError,'byte count mismatch'):
            parse_ps2_mesh(s)

    def test_ps2_reject_nonzero_flags(self):
        with self.assertRaisesRegex(ValueError,'Invalid PS2 strip'):
            parse_ps2_mesh(ps2_parts(flags=1))

    def test_ps2_reject_nonfinite_density(self):
        with self.assertRaisesRegex(ValueError,'Invalid PS2 strip'):
            parse_ps2_mesh(ps2_parts(density=float('nan')))

    def test_ps2_reject_bad_polygon_count(self):
        with self.assertRaisesRegex(ValueError,'Invalid PS2 strip'):
            parse_ps2_mesh(ps2_parts(strips=((3,4,0,1),)))

    def test_ps2_reject_wrong_version(self):
        s=ps2_parts();b=bytearray(s[0][1]);struct.pack_into('<I',b,4,10);s[0]=(PLATFORM_PS2,bytes(b))
        with self.assertRaisesRegex(ValueError,'version/counts'):
            parse_ps2_mesh(s)

    def test_allows_repeated_model_hash_across_different_packs(self):
        a=fake_geometry(123,PLATFORM_PS2)
        p,solids=scan_geometry_pack_solids(a+bytes(24)+a)
        self.assertEqual((p,len(solids),len(solids[123])),(2,1,2))

    def test_detects_one_solid_in_complete_geometry_pack(self):
        p,solids=scan_geometry_pack_solids(bytes(16)+fake_geometry(456))
        self.assertEqual((p,len(solids)),(1,1))

    def test_detects_no_valid_pack(self):
        with self.assertRaisesRegex(ValueError,'No valid geometry'):
            scan_geometry_pack_solids(bytes(64))

    def test_topology_match_and_differences(self):
        pc={1:[(PLATFORM_PC,{'pc_triangle_count':10})],2:[(PLATFORM_PC,{'pc_triangle_count':20})]}
        ps={1:[(PLATFORM_PS2,{'strip_polygon_count':10})],2:[(PLATFORM_PS2,{'strip_polygon_count':18})]}
        got=compare_topology(pc,ps)
        self.assertEqual((got['same_polygon_count'],got['different_polygon_count']),(1,1))
        self.assertEqual(got['pc_minus_ps2_triangle_delta_distribution'],{'0':1,'2':1})

    def test_topology_rejects_hash_mismatch(self):
        pc={1:[(PLATFORM_PC,{'pc_triangle_count':10})]}
        ps={2:[(PLATFORM_PS2,{'strip_polygon_count':10})]}
        with self.assertRaisesRegex(ValueError,'hashes disagree'):
            compare_topology(pc,ps)

    def test_topology_rejects_ambiguous_same_hash(self):
        pc={1:[(PLATFORM_PC,{'pc_triangle_count':10})]}
        ps={1:[(PLATFORM_PS2,{'strip_polygon_count':10})]*2}
        with self.assertRaisesRegex(ValueError,'exactly one solid'):
            compare_topology(pc,ps)

    def test_alignment_overflow(self):
        with self.assertRaisesRegex(ValueError,'alignment filler'):
            filler_size(b'\x11'*16+bytes(8))

if __name__=='__main__':unittest.main()
