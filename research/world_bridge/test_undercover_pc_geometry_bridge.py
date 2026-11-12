"""Synthetic-only tests for complete Undercover->Carbon candidate mesh roots.

These tests ship no original game data. On GitHub CI they exercise the actual
existing Carbon PC native geometry readers/writers; local original assets are
needed separately for any private original-source audit.
"""
import math
import os
import tempfile
import zipfile
from pathlib import Path
import struct
import unittest
from collections import Counter
from unittest.mock import patch

from undercover_pc_geometry_bridge import (
    _chunk,_hash,_vec,_cross,_norm,_new_header,_sig,
    mesh_specs_from_ps2,pack_pc_geometry_root,
    verify_ps2_to_pc_faces,convert_decoded_ps2_model,
    audit_original_undercover,_source_geometry_occurrences)


def basic():
    xyz=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
    uv=((0.,0.),(1.,0.),(0.,1.))
    return xyz,uv,((0,1,2),),(0,),(0x01020304,)


def tiled():
    xyz=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.),(0.,0.,1.),(1.,0.,1.))
    uv=((0.,0.),(1.,0.),(0.,1.),(1.,1.),(0.,0.),(1.,0.))
    faces=((0,1,2),(2,1,3),(0,4,5),(0,5,1))
    labels=(1,1,0,0)
    return xyz,uv,faces,labels,(0xABCD0123,0xABCD0123,0x12345678)


class EnvelopePrimitiveTests(unittest.TestCase):
    def test_chunk(self):
        self.assertEqual(_chunk(0x11223344,b'A'),struct.pack('<II',0x11223344,1)+b'A')
    def test_bad_chunk(self):
        for k,v in ((-1,b'x'),(0x100000000,b'x'),(1,bytearray(b'x')),(True,b'x')):
            with self.subTest(k=k),self.assertRaises(ValueError):_chunk(k,v)
    def test_hash_bounds(self):
        for bad in (0,-1,0x100000000,True,False,1.):
            with self.subTest(v=bad),self.assertRaises(ValueError):_hash(bad)
    def test_finite_coordinate(self):
        self.assertEqual(_vec((2,3.,4),3,'position'),(2.,3.,4.))
    def test_invalid_coordinate(self):
        for bad in ((1.,2.),(1.,float('nan'),2.),(1.,float('inf'),2.),(1.,1e10,2.),(False,1.,2.),'123'):
            with self.subTest(v=bad),self.assertRaises(ValueError):_vec(bad,3,'position')
    def test_cross_normal(self):
        x=basic()[0]
        self.assertEqual(_norm(_cross(*x)),(0.,0.,1.))
    def test_zero_cross(self):
        self.assertIsNone(_norm((0.,0.,0.)))
    def test_source_header_fields(self):
        h=_new_header(0x1234,3)
        self.assertEqual(len(h),184)
        self.assertEqual(struct.unpack_from('<I',h,12)[0],0x16)
        self.assertEqual(struct.unpack_from('<I',h,16)[0],0x1234)
        self.assertEqual(h[25],3)


class SourceMeshGroupTests(unittest.TestCase):
    def get(self, args=None):
        return mesh_specs_from_ps2(*(basic() if args is None else args))
    def test_single_triangle(self):
        m,s=self.get()
        self.assertEqual((len(m),len(m[0]['positions']),len(m[0]['triangles'])),(1,3,1))
        self.assertEqual(m[0]['normals'],((0.,0.,1.),)*3)
        self.assertEqual(s['source_triangles'],1)
    def test_two_materials(self):
        m,s=self.get(tiled())
        self.assertEqual(len(m),2)
        self.assertEqual(s['generated_pc_triangles'],4)
        self.assertEqual([x['texture_index'] for x in m],[0,1])
    def test_repeated_texture_hash_kept_distinct_indices(self):
        m,s=self.get(tiled())
        self.assertEqual([x['texture_index'] for x in m],[0,1])
        self.assertEqual(s['source_material_table_entries'],3)
    def test_deterministic_group_order(self):
        a=self.get(tiled())
        b=self.get(tiled())
        self.assertEqual(a,b)
    def test_no_reorder_inside_material(self):
        m,_=self.get(tiled())
        self.assertEqual([len(z['triangles']) for z in m],[2,2])
    def test_nonunit_input_area_normals_re_normalized(self):
        xyz=((0.,0.,0.),(7.,0.,0.),(0.,11.,0.))
        m,_=self.get((xyz,basic()[1],basic()[2],basic()[3],basic()[4]))
        self.assertAlmostEqual(sum(x*x for x in m[0]['normals'][0]),1.)
    def test_winding_reversal(self):
        x,u,f,l,t=basic()
        m,_=self.get((x,u,((0,2,1),),l,t))
        self.assertEqual(m[0]['normals'],((0.,0.,-1.),)*3)
    def test_uv_seams_preserved(self):
        x,u,f,l,t=basic()
        x=x+((0.,0.,0.),);u=u+((.7,.8),)
        m,_=self.get((x,u,((0,1,2),(3,1,2)),(0,0),t))
        self.assertEqual(len(m[0]['positions']),4)
        self.assertIn((.7,.8),m[0]['uv'])
    def test_reversed_normal_fallback(self):
        x,u,f,l,t=basic();x=x+((0.,0.,2.),);u=u+((.2,.3),)
        m,s=self.get((x,u,((0,1,2),(0,1,3),(0,3,1)),(0,0,0),t))
        self.assertGreaterEqual(s['candidate_normal_fallback_vertices'],1)
    def test_zero_area_triangle_preserved_if_other_face_valid(self):
        x,u,f,l,t=basic();x=x+((2.,0.,0.),);u=u+((2.,0.),)
        m,s=self.get((x,u,((0,1,2),(0,1,3)),(0,0),t))
        self.assertEqual(s['degenerate_geometric_faces_preserved'],1)
        self.assertEqual(s['generated_pc_triangles'],2)
    def test_entire_mesh_degenerate_rejected(self):
        x,u,f,l,t=basic();x=((0.,0.,0.),(1.,0.,0.),(2.,0.,0.))
        with self.assertRaisesRegex(ValueError,'No nondegenerate'):
            self.get((x,u,f,l,t))
    def test_repeated_face_vertex_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaisesRegex(ValueError,'repeated-index'):
            self.get((x,u,((0,0,1),),l,t))
    def test_out_of_range_face_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaisesRegex(ValueError,'triangle index'):
            self.get((x,u,((0,1,3),),l,t))
    def test_missing_uv_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u[:-1],f,l,t))
    def test_missing_faces_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,(),(),t))
    def test_labels_mismatch_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,f,(),t))
    def test_material_out_of_range_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaisesRegex(ValueError,'material table'):
            self.get((x,u,f,(1,),t))
    def test_negative_material_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,f,(-1,),t))
    def test_bool_indices_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,((True,1,2),),l,t))
    def test_boolean_material_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,f,(True,),t))
    def test_bad_table_hash_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((x,u,f,l,(0,)))
    def test_bad_float_rejected(self):
        x,u,f,l,t=basic()
        with self.assertRaises(ValueError):self.get((((0.,0.,float('nan')),*x[1:]),u,f,l,t))


class FullRootTests(unittest.TestCase):
    def get(self,inp=None,header=None):
        args=basic() if inp is None else inp
        return convert_decoded_ps2_model(0xA0B0C0D0,args[-1],*args[:4],source_header=header)
    def test_full_roundtrip_triangle(self):
        blob,stats=self.get()
        self.assertEqual(stats['pc_faces'],1)
        self.assertTrue(stats['native_pc_parser_roundtrip'])
        self.assertTrue(stats['all_f32_xyz_uv_texture_corner_faces_preserved'])
        self.assertEqual(struct.unpack_from('<I',blob)[0],0x80134000)
    def test_multi_material_roundtrip(self):
        blob,stats=self.get(tiled())
        self.assertEqual(stats['generated_pc_meshes'],2)
        self.assertEqual(stats['pc_faces'],4)
    def test_deterministic_byte_output(self):
        self.assertEqual(self.get()[0],self.get()[0])
    def test_f32_subpixel_roundtrip(self):
        x,u,f,l,t=basic()
        x=((.123456789,0.,0.),(1.123456789,0.,0.),(0.,1.123456789,0.))
        blob,s=self.get((x,u,f,l,t))
        self.assertTrue(s['all_f32_xyz_uv_texture_corner_faces_preserved'])
    def test_source_header_preserved(self):
        h=bytearray(_new_header(0xA0B0C0D0,1));h[90:94]=b'TEST'
        blob,_=self.get(header=bytes(h))
        self.assertIn(bytes(h),blob)
    def test_reject_wrong_source_header_hash(self):
        h=_new_header(0xABCD1234,1)
        with self.assertRaisesRegex(ValueError,'source header'):
            self.get(header=h)
    def test_reject_wrong_source_header_count(self):
        h=_new_header(0xA0B0C0D0,2)
        with self.assertRaisesRegex(ValueError,'source header'):
            self.get(header=h)
    def test_reject_malformed_source_header(self):
        with self.assertRaises(ValueError):self.get(header=bytes(10))
    def test_reject_missing_pc_chunks(self):
        with self.assertRaises(ValueError):pack_pc_geometry_root(1,(2,),[])
    def test_reject_bad_pc_chunk_order(self):
        with self.assertRaises(ValueError):pack_pc_geometry_root(1,(2,),[(0x134b02,b'')]*5)
    def test_reject_bad_texture_hash(self):
        with self.assertRaises(ValueError):pack_pc_geometry_root(1,(0,),[(0x134900,b'')]*5)
    def test_uv_changed_rejected_by_face_witness(self):
        x,u,f,l,t=basic()
        changed=((0.,0.),(1.,0.),(0.,.5))
        with self.assertRaisesRegex(ValueError,'corner multiset'):
            verify_ps2_to_pc_faces(x,u,f,l,x,changed,f,l)
    def test_reversed_winding_rejected_by_face_witness(self):
        x,u,f,l,t=basic()
        with self.assertRaisesRegex(ValueError,'corner multiset'):
            verify_ps2_to_pc_faces(x,u,f,l,x,u,((0,2,1),),l)
    def test_cyclic_winding_preserved(self):
        x,u,f,l,t=basic()
        self.assertTrue(verify_ps2_to_pc_faces(x,u,f,l,x,u,((1,2,0),),l)['orientation_preserved_up_to_cyclic_rotation'])
    def test_duplicate_face_multiplicity_preserved(self):
        x,u,f,l,t=basic()
        a=f+f;b=f
        with self.assertRaisesRegex(ValueError,'counts'):
            verify_ps2_to_pc_faces(x,u,a,(0,0),x,u,b,(0,))
    def test_material_changed_rejected_by_face_witness(self):
        x,u,f,l,t=basic()
        with self.assertRaisesRegex(ValueError,'corner multiset'):
            verify_ps2_to_pc_faces(x,u,f,(0,),x,u,f,(1,))


class PrivateCliControls(unittest.TestCase):
    def test_reject_missing_original_zip(self):
        with self.assertRaisesRegex(ValueError,'archive'):
            audit_original_undercover('/not/a/real/private/original.zip')
    def test_section_allowlist(self):
        with self.assertRaises(ValueError):audit_original_undercover('x',section=999)
    def test_reject_negative_ordinal(self):
        with self.assertRaises(ValueError):audit_original_undercover('x',model_ordinal=-1)
    def test_reject_boolean_ordinal(self):
        with self.assertRaises(ValueError):audit_original_undercover('x',model_ordinal=True)
    def test_reject_private_output_without_optin(self):
        with self.assertRaisesRegex(ValueError,'opt-in'):
            audit_original_undercover('x',private_output='PRIVATE_private.bin')
    def test_reject_optin_without_output(self):
        with self.assertRaisesRegex(ValueError,'opt-in'):
            audit_original_undercover('x',write_private=True)
    def test_no_original_assets_in_source_code_summaries(self):
        _,report=convert_decoded_ps2_model(0x12345678,basic()[-1],*basic()[:4])
        for banned in ('texture_hashes','model_hash','positions','uv','faces','original_path'):
            self.assertNotIn(banned,report)
    def test_fit_dummy_fixture(self):
        blob, result = convert_decoded_ps2_model(0x12345678,basic()[-1],*basic()[:4])
        self.assertTrue(result['native_pc_parser_roundtrip'])
        return None


class OriginalSourceOccurrenceTests(unittest.TestCase):
    """Self-contained synthetic ZIPs with two independent same-hash source packs."""
    @staticmethod
    def _donor_pack(identity=0x10000001):
        from undercover_pc_geometry_bridge import _chunk,_new_header
        # Valid PS2 metadata/strip framing, without copyrighted VIF data.
        platform_info=bytearray(b'\x11'*4+bytes(48))
        struct.pack_into('<III',platform_info,4,0x20,1,16)
        strip=bytearray(b'\x11'*4+bytes(16))
        struct.pack_into('<HBBfHbbBBbb',strip,4,0,3,1,1.,0,0,0,1,0,0,0)
        raw_stream=b'\x11'*8+bytes(16)
        platform=(_chunk(0x134a00,bytes(platform_info))+
                  _chunk(0x134a01,bytes(strip))+
                  _chunk(0x134a02,raw_stream))
        solid=_chunk(0x80134010,
                _chunk(0x134011,_new_header(identity,1))+
                _chunk(0x134012,struct.pack('<II',0xFAFA1111,0))+
                _chunk(0x80134100,platform))
        idx=_chunk(0x134003,struct.pack('<II',identity,0))
        header=_chunk(0x80134001,_chunk(0x134002,bytes(144))+idx+_chunk(0x80134008,b''))
        return _chunk(0x80134000,bytes(8)+header+solid)

    @staticmethod
    def _source_zip(tmp,content):
        path=Path(tmp)/'synthetic-owner-split.zip'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('TRACKS/STREAML2RB.BUN',content)
        row=bytearray(92)
        struct.pack_into('<h',row,8,241)
        struct.pack_into('<II',row,0x14,0,len(content))
        return path,bytes(row)

    def test_two_packs_duplicate_hash_are_preserved(self):
        first=self._donor_pack()
        second=self._donor_pack()
        with tempfile.TemporaryDirectory() as tmp:
            path,row=self._source_zip(tmp,first+second)
            with patch('visibility_stream_join.read_small',return_value=({241:row},None,None)):
                occurrences,packs=_source_geometry_occurrences(path,241)
        self.assertEqual(packs,2)
        self.assertEqual(len(occurrences),2)
        self.assertEqual(len(set(x[0] for x in occurrences)),1)
        self.assertEqual(len(occurrences[0][2]),1)

    def test_two_packs_distinct_models(self):
        a=self._donor_pack(0x10000001)
        b=self._donor_pack(0x10000002)
        with tempfile.TemporaryDirectory() as tmp:
            path,row=self._source_zip(tmp,a+b)
            with patch('visibility_stream_join.read_small',return_value=({241:row},None,None)):
                occurrences,packs=_source_geometry_occurrences(path,241)
        self.assertEqual((packs,len(set(x[0] for x in occurrences))),(2,2))

    def test_missing_section_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,_=self._source_zip(tmp,self._donor_pack())
            with patch('visibility_stream_join.read_small',return_value=({},None,None)):
                with self.assertRaisesRegex(ValueError,'section absent'):
                    _source_geometry_occurrences(path,241)

    def test_wrong_platform_pack_rejected(self):
        # Parser-valid PC geometry is not a PS2 donor pack.
        xyz,uv,faces,labels,table=basic()
        root,_=convert_decoded_ps2_model(12345,table,xyz,uv,faces,labels)
        with tempfile.TemporaryDirectory() as tmp:
            path,row=self._source_zip(tmp,root)
            with patch('visibility_stream_join.read_small',return_value=({241:row},None,None)):
                with self.assertRaisesRegex(ValueError,'non-PS2'):
                    _source_geometry_occurrences(path,241)

    def test_truncated_stream_member_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,row=self._source_zip(tmp,self._donor_pack())
            row=bytearray(row);struct.pack_into('<II',row,0x14,0,100000)
            with patch('visibility_stream_join.read_small',return_value=({241:bytes(row)},None,None)):
                with self.assertRaisesRegex(ValueError,'safety bounds'):
                    _source_geometry_occurrences(path,241)

    def test_aliased_model_headers_have_separate_records(self):
        a=self._donor_pack();b=self._donor_pack()
        with tempfile.TemporaryDirectory() as tmp:
            path,row=self._source_zip(tmp,a+b)
            with patch('visibility_stream_join.read_small',return_value=({241:row},None,None)):
                occurrences,_=_source_geometry_occurrences(path,241)
        self.assertEqual(occurrences[0][1],occurrences[1][1])
        self.assertIsNot(occurrences[0],occurrences[1])


if __name__=='__main__':unittest.main()
