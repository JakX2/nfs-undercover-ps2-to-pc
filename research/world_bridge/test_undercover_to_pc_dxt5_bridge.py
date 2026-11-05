"""Source-free, in-memory synthetic Undercover indexed -> Carbon existing DXT5 tests."""
import struct
import unittest
from test_texture_visual_pair_gate import make_pack
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import _chunks,aligned_pixel_array
from undercover_to_pc_dxt5_bridge import (
    decode_undercover_source,encode_roundtrip,audit_undercover_section,
    overlay_undercover_on_existing_pc_dxt5)
from pc_dxt_reference_decode import decode_dxt_base


def dxt5_pc_fixture(extra_dxt1=False, w=8,h=8,mips=1):
    # Synthetic source fixture with 4096-byte pixel field, so extending its
    # DXT1 image to DXT5 does not alter the parent chunk structure.
    hashes=(0x11111111,0x22222222) if extra_dxt1 else (0x11111111,)
    pc=bytearray(make_pack('pc',hashes=hashes))
    root=_chunks(pc,8,8+struct.unpack_from('<I',pc,4)[0])
    desc=_chunks(pc,root[1][1],root[1][2])
    meta=desc[2][1]
    pm=desc[3][1]
    pc[meta+46]=38
    pc[meta+50]=mips
    n=sum(max(1,((w>>i)+3)//4)*max(1,((h>>i)+3)//4)*16 for i in range(mips))
    struct.pack_into('<I',pc,meta+28,n)
    struct.pack_into('<I',pc,meta+36,((w+3)//4)*((h+3)//4)*16)
    pc[pm+12:pm+16]=b'DXT5'
    if (w,h)!=(8,8):
        # Vary dimensions only to exercise mismatch detection; the native
        # source pack must remain parseable after byte-size correction.
        struct.pack_into('<HH',pc,meta+40,w,h)
        pc[meta+44]=w.bit_length()-1
        pc[meta+45]=h.bit_length()-1
    assert parse_pack(pc,'pc')['records']
    return bytes(pc)

class DonorTests(unittest.TestCase):
    def test_linear_8bit_synthetic_decoder(self):
        ps=make_pack('ps2',bits=8)
        data,w,h,bits,flag=decode_undercover_source(ps,0)
        self.assertEqual((w,h,bits,flag),(8,8,8,0))
        self.assertEqual(len(data),256)
        self.assertEqual(set(data[3::4]),{255})
    def test_linear_4bit_synthetic_decoder(self):
        data,w,h,bits,flag=decode_undercover_source(make_pack('ps2',bits=4),0)
        self.assertEqual((w,h,bits,flag),(8,8,4,0))
        self.assertEqual(set(data[3::4]),{255})
    def test_roundtrip_preserves_binary_alpha(self):
        rgba=b''.join(bytes((255,0,0,255 if i%2 else 0)) for i in range(64))
        packed,score=encode_roundtrip(rgba,8,8)
        self.assertEqual(len(packed),64)
        self.assertEqual(score['mean_absolute_alpha_error'],0)
    def test_donor_ordinal_bounds(self):
        for bad in (-1,999,1.0,True):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                decode_undercover_source(make_pack('ps2'),bad)
    def test_invalid_ps2_section_rejected(self):
        with self.assertRaises(ValueError):
            decode_undercover_source(b'broken',0)
    def test_bad_swizzle_flag_rejected(self):
        p=bytearray(make_pack('ps2'))
        # Only one PS2 platform flag changes, preserving metadata structure.
        root=_chunks(p,8,8+struct.unpack_from('<I',p,4)[0])
        desc=_chunks(p,root[1][1],root[1][2])
        p[desc[3][1]+0x17]=9
        with self.assertRaisesRegex(ValueError,'transfer layout'):
            decode_undercover_source(p,0)
    def test_aggregate_audit_privacy_and_counts(self):
        r=audit_undercover_section(make_pack('ps2',bits=4),2)
        self.assertEqual(r['sampled_textures'],2)
        self.assertEqual(r['source_textures_with_nonopaque_alpha'],0)
        self.assertEqual(r['mean_alpha_mae'],0)
        self.assertNotIn('286331153',repr(r))
        self.assertNotIn('SYNTHETIC_',repr(r))
    def test_audit_sample_limit(self):
        with self.assertRaisesRegex(ValueError,'limit'):
            audit_undercover_section(make_pack('ps2'),0)
    def test_audit_invalid_image_range(self):
        with self.assertRaises(ValueError):
            audit_undercover_section(make_pack('ps2')[:-200])
    def test_alpha_is_not_forced_opaque(self):
        p=bytearray(make_pack('ps2',bits=8))
        # Palette red at +4 carries alpha in byte +7, set to 64.
        px,_=aligned_pixel_array(p)
        root=_chunks(p,8,8+struct.unpack_from('<I',p,4)[0]);chunks=_chunks(p,root[3][1],root[3][2])
        origin=chunks[2][1]+(-chunks[2][1]%128)
        p[origin+7]=64
        rgba,*_=decode_undercover_source(p,0)
        self.assertIn(128,rgba[3::4])
        self.assertIn(255,rgba[3::4])

class OverlayTests(unittest.TestCase):
    def test_overlays_existing_pc_dxt5_without_losing_transparency(self):
        source=make_pack('ps2',bits=4)
        pc=dxt5_pc_fixture(extra_dxt1=True)
        new,report=overlay_undercover_on_existing_pc_dxt5(pc,source)
        self.assertEqual(len(new),len(pc))
        self.assertTrue(report['only_one_existing_image_span_changed'])
        self.assertEqual(report['source_indexed_bits'],4)
        self.assertEqual(report['mip_levels'],1)
        self.assertEqual(report['alpha_mae_against_decoded_ps2'],0)
        a=parse_pack(pc,'pc')['records'];b=parse_pack(new,'pc')['records']
        self.assertEqual(a,b)
        before, _=aligned_pixel_array(pc,a);after,_=aligned_pixel_array(new,b)
        other=a[0x22222222]
        start=other['image_offset'];end=start+other['image_bytes']
        self.assertEqual(before[start:end],after[start:end])
        self.assertGreater(report['changed_image_bytes'],0)
        self.assertNotIn('286331153',repr(report))
    def test_reproducible_conversion(self):
        pc=dxt5_pc_fixture()
        ps=make_pack('ps2',bits=8)
        self.assertEqual(overlay_undercover_on_existing_pc_dxt5(pc,ps),
                         overlay_undercover_on_existing_pc_dxt5(pc,ps))
    def test_multi_mip_overlay(self):
        pc=dxt5_pc_fixture(mips=3)
        _,r=overlay_undercover_on_existing_pc_dxt5(pc,make_pack('ps2'))
        self.assertEqual(r['mip_levels'],3)
        self.assertEqual(r['replaced_image_bytes'],96)
    def test_wrong_target_dimensions_rejected(self):
        pc=dxt5_pc_fixture(w=16,h=8)
        with self.assertRaisesRegex(ValueError,'dimensions differ'):
            overlay_undercover_on_existing_pc_dxt5(pc,make_pack('ps2'))
    def test_outside_dxt5_slot_rejected(self):
        with self.assertRaisesRegex(ValueError,'ordinal outside'):
            overlay_undercover_on_existing_pc_dxt5(dxt5_pc_fixture(),make_pack('ps2'),pc_dxt5_ordinal=2)
    def test_missing_pc_dxt5_slot_rejected(self):
        with self.assertRaisesRegex(ValueError,'ordinal outside'):
            overlay_undercover_on_existing_pc_dxt5(make_pack('pc'),make_pack('ps2'))
    def test_invalid_pc_ordinal_rejected(self):
        for v in (-1,True,0.5):
            with self.subTest(v=v),self.assertRaises(ValueError):
                overlay_undercover_on_existing_pc_dxt5(dxt5_pc_fixture(),make_pack('ps2'),pc_dxt5_ordinal=v)
    def test_broken_pc_source_rejected(self):
        with self.assertRaises(ValueError):
            overlay_undercover_on_existing_pc_dxt5(b'broken',make_pack('ps2'))
    def test_broken_ps2_source_rejected(self):
        with self.assertRaises(ValueError):
            overlay_undercover_on_existing_pc_dxt5(dxt5_pc_fixture(),b'broken')

if __name__=='__main__':unittest.main()
