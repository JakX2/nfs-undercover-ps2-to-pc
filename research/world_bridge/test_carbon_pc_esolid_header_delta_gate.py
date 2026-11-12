"""Synthetic-only Carbon PC/PS2 eSolid header normalization and native mesh tests."""
import struct
import unittest
from carbon_pc_esolid_header_delta_gate import (
    inspect_header,normalize_ps2_header,compare_same_model_headers)
from undercover_pc_geometry_bridge import _new_header,convert_decoded_ps2_model
from geometry_hash_control import SOLID_ROOT,read_chunks

MODEL=0xA0B0C0D0
TEXTURE=0xAABBCCDD
XYZ=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
UV=((0.,0.),(1.,0.),(0.,1.))
FACES=((0,1,2),)


def source_header(pad=0,version=0x16,triangles=1,upper=9,materials=1):
    body=bytearray(_new_header(MODEL,materials))
    struct.pack_into('<I',body,12,version)
    struct.pack_into('<I',body,20,(upper<<16)|triangles)
    return b'\x11'*pad+bytes(body)


class PairedHeaderRules(unittest.TestCase):
    def test_original_fields(self):
        got=inspect_header(source_header())
        self.assertEqual((got['identity'],got['texture_count'],
                          got['triangles_candidate'],got['ps2_upper_count']),
                         (MODEL,1,1,9))

    def test_all_padding_profiles(self):
        for p in (0,4,8,12):
            with self.subTest(p=p):
                src=source_header(pad=p)
                dst=normalize_ps2_header(src,MODEL,1,1)
                self.assertEqual(inspect_header(dst)['pad'],p)
                self.assertEqual(len(dst),len(src))
                self.assertFalse(inspect_header(dst)['ps2_upper_count'])

    def test_only_upper16_bytes_change(self):
        src=source_header(upper=0x1234)
        dst=normalize_ps2_header(src)
        self.assertEqual([i for i,(a,b) in enumerate(zip(src,dst)) if a!=b],[22,23])
        self.assertEqual(dst[16:20],src[16:20])

    def test_material_count_preserved(self):
        src=source_header(materials=3)
        self.assertEqual(inspect_header(normalize_ps2_header(src,
                expected_material_count=3))['texture_count'],3)

    def test_wrong_original_identity_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(),expected_identity=MODEL+1)

    def test_wrong_source_material_count_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(),expected_material_count=2)

    def test_wrong_source_faces_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(),expected_faces=3)

    def test_pc_already_normalized_refused(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(upper=0))

    def test_invalid_original_special_versions_refused(self):
        for ver in (0x800016,0x400016):
            with self.subTest(ver=ver),self.assertRaises(ValueError):
                normalize_ps2_header(source_header(version=ver))

    def test_invalid_format_rejected(self):
        for bad in (b'junk',bytearray(source_header()),b'\x00'*176):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):
                inspect_header(bad)

    def test_zero_triangle_field_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(triangles=0))

    def test_bool_count_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ps2_header(source_header(),expected_faces=True)

    def test_exact_native_pair(self):
        ps=source_header()
        pc=normalize_ps2_header(ps)
        self.assertEqual(compare_same_model_headers(pc,ps),'exact')

    def test_special_native_pc_version_is_exception(self):
        ps=source_header()
        pc=bytearray(normalize_ps2_header(ps))
        struct.pack_into('<I',pc,12,0x400016)
        self.assertEqual(compare_same_model_headers(bytes(pc),ps),
                         'native_special_version_unresolved')

    def test_unexplained_native_difference_rejected(self):
        ps=source_header()
        pc=bytearray(normalize_ps2_header(ps))
        pc[72]=4
        with self.assertRaises(ValueError):
            compare_same_model_headers(bytes(pc),ps)


class NativeGeometryIntegration(unittest.TestCase):
    def convert(self,header,profile='preserve_source'):
        return convert_decoded_ps2_model(MODEL,(TEXTURE,),XYZ,UV,FACES,(0,),
            source_header=header,pc_header_profile=profile)

    def solid_header(self,root):
        solid=next(body for cid,body in read_chunks(root,16,len(root)) if cid==SOLID_ROOT)
        return next(body for cid,body in read_chunks(solid,0,len(solid))
                    if cid==0x00134011)

    def test_old_converter_default_is_preserved(self):
        src=source_header()
        root,stats=self.convert(src)
        self.assertEqual(self.solid_header(root),src)
        self.assertEqual(stats['pc_header_profile'],'preserve_source')

    def test_optin_converts_only_ps2_header_field_and_roundtrips(self):
        src=source_header()
        root,stats=self.convert(src,'carbon_native_control')
        self.assertEqual(self.solid_header(root),normalize_ps2_header(src))
        self.assertTrue(stats['native_pc_parser_roundtrip'])
        self.assertEqual(stats['pc_faces'],1)
        self.assertEqual(stats['pc_header_profile'],'carbon_native_control')
        self.assertEqual(stats['retail_pc_loader_compatibility'],'UNVERIFIED')

    def test_optin_deterministic_source_unchanged(self):
        src=source_header()
        first=self.convert(src,'carbon_native_control')[0]
        second=self.convert(src,'carbon_native_control')[0]
        self.assertEqual(first,second)
        self.assertEqual(src,source_header())

    def test_optin_requires_original_source_header(self):
        with self.assertRaises(ValueError):
            self.convert(None,'carbon_native_control')

    def test_unknown_profile_rejected(self):
        with self.assertRaises(ValueError):
            self.convert(source_header(),'unsupported')

    def test_optin_rejects_wrong_source_face_count(self):
        with self.assertRaises(ValueError):
            self.convert(source_header(triangles=2),'carbon_native_control')

    def test_optin_special_source_version_refused(self):
        with self.assertRaises(ValueError):
            self.convert(source_header(version=0x800016),'carbon_native_control')

if __name__=='__main__':
    unittest.main()
