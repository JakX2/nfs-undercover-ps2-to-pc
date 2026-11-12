"""Source-free regression tests for strictly in-memory existing DXT1 overlay."""
import struct
import unittest

from synthetic_pc_dxt1_pack_envelope import build_synthetic_pc_dxt1_pack
from pc_texture_header_overlay_gate import profile_pc_texture_headers, overlay_existing_dxt1
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array, _chunks
from pc_dxt_reference_decode import decode_dxt_base


def src(identity, name=b'SYNTH_A', width=8, height=8, levels=1, color=(255,0,0)):
    return {'hash':identity,'name':name,'width':width,'height':height,
            'mip_levels':levels,'rgba':bytes((*color,255))*(width*height)}


class ProfileTests(unittest.TestCase):
    def test_synthetic_header_shape(self):
        a=build_synthetic_pc_dxt1_pack([src(7)])
        result=profile_pc_texture_headers([a])
        self.assertEqual(result['source_sections'],1)
        self.assertEqual(result['total_pc_texture_records'],1)
        self.assertEqual(result['descriptor_header_size'],124)
        self.assertTrue(result['descriptor_headers_all_zero'])
        self.assertEqual(result['platform_records_fourcc_only'],1)
        self.assertEqual(result['pixel_alignment_padding_sizes'],[120])

    def test_multiple_synthetic_headers_identical(self):
        a=build_synthetic_pc_dxt1_pack([src(7)])
        b=build_synthetic_pc_dxt1_pack([src(9),src(10,b'SYNTH_B')])
        p=profile_pc_texture_headers([a,b])
        self.assertTrue(p['descriptor_headers_identical'])
        self.assertEqual(p['total_pc_texture_records'],3)

    def test_differing_header_exposed_not_silently_accepted(self):
        a=build_synthetic_pc_dxt1_pack([src(7)])
        b=bytearray(a)
        needle=struct.pack('<II',0x33310001,124)
        location=b.index(needle)+8
        b[location+96]=1
        p=profile_pc_texture_headers([a,b])
        self.assertFalse(p['descriptor_headers_identical'])
        self.assertFalse(p['descriptor_headers_all_zero'])
        self.assertEqual(p['descriptor_header_nonzero_u32_offsets'],[96])

    def test_malformed_section_rejected(self):
        with self.assertRaises(ValueError):
            profile_pc_texture_headers([b'broken'])

    def test_empty_sections_rejected(self):
        with self.assertRaisesRegex(ValueError,'count'):
            profile_pc_texture_headers([])

    def test_too_many_sections_rejected(self):
        a=build_synthetic_pc_dxt1_pack([src(7)])
        with self.assertRaisesRegex(ValueError,'count'):
            profile_pc_texture_headers([a]*17)

    def test_unsupported_section_collection_rejected(self):
        with self.assertRaisesRegex(ValueError,'count'):
            profile_pc_texture_headers((x for x in []))


class ExistingEntryOverlayTests(unittest.TestCase):
    def test_single_opaque_replacement(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        blue=bytes((0,0,255,255))*64
        after,report=overlay_existing_dxt1(before,7,blue)
        self.assertEqual(report['source_texture_count'],1)
        self.assertTrue(report['unchanged_metadata_and_other_resources'])
        self.assertGreater(report['changed_image_bytes'],0)
        self.assertEqual(len(before),len(after))
        r=parse_pack(after,'pc')['records'][7]
        px,_=aligned_pixel_array(after)
        pic=decode_dxt_base(px[r['image_offset']:r['image_offset']+r['base_image_bytes']],8,8,b'DXT1')
        self.assertEqual(pic,blue)

    def test_only_existing_span_changes_and_other_entries_survive(self):
        first=src(7,levels=3,width=16,height=16)
        second=src(9,name=b'SYNTH_B',color=(0,255,0))
        before=build_synthetic_pc_dxt1_pack([second,first])
        modified,report=overlay_existing_dxt1(before,7,bytes((0,0,255,255))*256)
        self.assertEqual(report['overlaid_mip_levels'],3)
        before_records=parse_pack(before,'pc')['records']
        after_records=parse_pack(modified,'pc')['records']
        self.assertEqual(before_records,after_records)
        start=before_records[9]['image_offset'];size=before_records[9]['image_bytes']
        old_px,_=aligned_pixel_array(before);new_px,_=aligned_pixel_array(modified)
        self.assertEqual(bytes(old_px[start:start+size]),bytes(new_px[start:start+size]))
        diffs=[i for i,(a,b) in enumerate(zip(before,modified)) if a != b]
        self.assertEqual(len(diffs),report['changed_image_bytes'])
        self.assertTrue(diffs)

    def test_repeat_is_deterministic(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        input_rgba=bytes((0,255,0,255))*64
        self.assertEqual(overlay_existing_dxt1(before,7,input_rgba),overlay_existing_dxt1(before,7,input_rgba))

    def test_reject_unknown_identity(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        with self.assertRaises(KeyError):
            overlay_existing_dxt1(before,17,bytes((0,0,255,255))*64)

    def test_reject_invalid_identity(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        with self.assertRaisesRegex(ValueError,'identity'):
            overlay_existing_dxt1(before,True,bytes((0,0,255,255))*64)

    def test_reject_transparency(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        rgba=bytearray(bytes((0,0,255,255))*64);rgba[3]=10
        with self.assertRaisesRegex(ValueError,'alpha'):
            overlay_existing_dxt1(before,7,rgba)

    def test_reject_wrong_rgba_length(self):
        before=build_synthetic_pc_dxt1_pack([src(7)])
        with self.assertRaisesRegex(ValueError,'byte count'):
            overlay_existing_dxt1(before,7,bytes(4))

    def test_reject_wrong_pack_bytes(self):
        with self.assertRaises(ValueError):
            overlay_existing_dxt1(b'junk',7,bytes((0,0,255,255))*64)

    def test_reject_wrong_platform_metadata(self):
        before=bytearray(build_synthetic_pc_dxt1_pack([src(7)]))
        needle=b'DXT1'
        before[before.index(needle):before.index(needle)+4]=b'DXT5'
        with self.assertRaisesRegex(ValueError,'FOURCC'):
            overlay_existing_dxt1(before,7,bytes((0,0,255,255))*64)

    def test_reject_existing_non_dxt1_format(self):
        before=bytearray(build_synthetic_pc_dxt1_pack([src(7)]))
        root=_chunks(before,8,8+struct.unpack_from('<I',before,4)[0])
        desc=_chunks(before,root[1][1],root[1][2])
        pix=_chunks(before,root[3][1],root[3][2])
        # Expand a valid 8x8/one-mip DXT1 (32 bytes) to DXT3 (64 bytes).
        row=desc[2][1]
        before[row+46]=36
        struct.pack_into('<I',before,row+28,64)
        struct.pack_into('<I',before,row+36,64)
        before[desc[3][1]+12:desc[3][1]+16]=b'DXT3'
        for header_pos in (4,root[3][1]-4,pix[2][1]-4):
            struct.pack_into('<I',before,header_pos,struct.unpack_from('<I',before,header_pos)[0]+32)
        before.extend(bytes(32))
        self.assertEqual(parse_pack(before,'pc')['records'][7]['codec'],36)
        with self.assertRaisesRegex(ValueError,'Only existing opaque DXT1'):
            overlay_existing_dxt1(before,7,bytes((0,0,255,255))*64)

    def test_reject_non_bytes_pack_type(self):
        with self.assertRaisesRegex(ValueError,'section bytes'):
            overlay_existing_dxt1('not a pack',7,bytes((0,0,255,255))*64)

    def test_reject_corrupt_pixel_padding(self):
        before=bytearray(build_synthetic_pc_dxt1_pack([src(7)]))
        idx=before.index(bytes([0x11])*120)
        before[idx]=0
        with self.assertRaisesRegex(ValueError,'padding'):
            overlay_existing_dxt1(before,7,bytes((0,0,255,255))*64)

    def test_reject_tampered_dimension(self):
        before=bytearray(build_synthetic_pc_dxt1_pack([src(7)]))
        # The metadata hash occurrence is in index and inside variable metadata.
        # Change only dimensions, leaving mismatched shifts/byte equations.
        hash_bytes=struct.pack('<I',7)
        first=before.index(hash_bytes)
        second=before.index(hash_bytes,first+4)
        before[second+28:second+30]=(4).to_bytes(2,'little')
        with self.assertRaises(ValueError):
            overlay_existing_dxt1(before,7,bytes((0,0,255,255))*64)


if __name__=='__main__':unittest.main()
