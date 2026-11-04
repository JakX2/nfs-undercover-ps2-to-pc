"""Source-free PC-shaped pack framing and negative tests, no game assets."""
import unittest
import struct
from synthetic_pc_dxt1_pack_envelope import build_synthetic_pc_dxt1_pack
from texture_metadata_pixel_bridge import parse_pack, mip_size, children
from texture_pixel_base_alignment import aligned_pixel_array
from pc_dxt_reference_decode import decode_dxt_base


def fixture(h, name, color=(255,0,0), width=8, height=8, levels=1):
    return {'hash':h,'name':name,'width':width,'height':height,
            'rgba':bytes((*color,255))*(width*height),'mip_levels':levels}


class EnvelopeTests(unittest.TestCase):
    def test_single_synthetic_dxt1_pack(self):
        src=fixture(0x11223344,b'SYNTH_A')
        packet=build_synthetic_pc_dxt1_pack([src])
        r=parse_pack(packet,'pc')
        self.assertEqual(r['summary']['indexed_texture_records'],1)
        self.assertEqual(r['summary']['valid_palette_ranges'],0)
        px,pad=aligned_pixel_array(packet,r['records'])
        self.assertEqual(pad,120)
        m=r['records'][src['hash']]
        self.assertEqual(m['image_bytes'],mip_size(8,8,34,1))
        rgba=decode_dxt_base(px[m['image_offset']:m['image_offset']+m['image_bytes']],8,8,b'DXT1')
        self.assertEqual(rgba,src['rgba'])

    def test_sorted_hashes_multiple_mip_levels_and_offsets(self):
        a=fixture(0x22222222,b'SYNTH_B',(0,255,0),16,8,4)
        b=fixture(0x11111111,b'SYNTH_C',(0,0,255),8,8,2)
        raw=build_synthetic_pc_dxt1_pack([a,b])
        parsed=parse_pack(raw,'pc')
        self.assertEqual(tuple(parsed['records']), (b['hash'],a['hash']))
        self.assertEqual(parsed['summary']['valid_image_ranges'],2)
        pixel,pad=aligned_pixel_array(raw,parsed['records'])
        for item in (a,b):
            m=parsed['records'][item['hash']]
            self.assertEqual(m['mip_levels'],item['mip_levels'])
            self.assertEqual(m['image_bytes'],mip_size(item['width'],item['height'],34,item['mip_levels']))
            s=m['image_offset']
            self.assertEqual(decode_dxt_base(pixel[s:s+m['base_image_bytes']],item['width'],item['height'],b'DXT1'),item['rgba'])

    def test_deterministic_pack_bytes(self):
        items=[fixture(5,b'SYNTH_C'),fixture(3,b'SYNTH_D')]
        self.assertEqual(build_synthetic_pc_dxt1_pack(items),build_synthetic_pc_dxt1_pack(list(reversed(items))))

    def test_rigid_alignment(self):
        raw=build_synthetic_pc_dxt1_pack([fixture(7,b'SYNTH_PADNAME')])
        pixels,pad=aligned_pixel_array(raw)
        self.assertEqual(pad,120)
        self.assertEqual(len(raw)%4,0)
        self.assertEqual(len(pixels)>0,True)

    def test_padding_corruption_rejected(self):
        raw=bytearray(build_synthetic_pc_dxt1_pack([fixture(7,b'SYNTH_G')]))
        where=raw.find(bytes([0x11])*120)
        self.assertNotEqual(where,-1)
        raw[where+10]=0
        with self.assertRaisesRegex(ValueError,'padding'):
            aligned_pixel_array(raw)

    def test_pc_platform_fourcc_only(self):
        raw=build_synthetic_pc_dxt1_pack([fixture(9,b'SYNTH_HEADER')])
        total=struct.unpack_from('<I',raw,4)[0]
        root=children(raw,8,8+total)
        desc=children(root[1][1])
        self.assertEqual(len(desc[0][1]),124)
        self.assertEqual(len(desc[3][1]),24)
        self.assertEqual(desc[3][1][12:16],b'DXT1')
        self.assertEqual(desc[3][1][:12]+desc[3][1][16:],bytes(20))

    def test_native_chunk_lengths_and_order(self):
        raw=build_synthetic_pc_dxt1_pack([fixture(9,b'SYNTH_HEADER')])
        total=struct.unpack_from('<I',raw,4)[0]
        root=children(raw,8,8+total)
        self.assertEqual([cid for cid,_ in root],[0,0xB3310000,0,0xB3320000])
        pixel_children=children(root[3][1])
        self.assertEqual([cid for cid,_ in pixel_children],[0x33320001,0,0x33320002])
        self.assertEqual(len(pixel_children[0][1]),24)
        self.assertEqual(len(pixel_children[1][1]),80)

    def test_no_entries(self):
        with self.assertRaisesRegex(ValueError,'count'):
            build_synthetic_pc_dxt1_pack([])

    def test_too_many_entries(self):
        with self.assertRaisesRegex(ValueError,'count'):
            build_synthetic_pc_dxt1_pack([fixture(i+1,b'SYNTH_A') for i in range(17)])

    def test_duplicate_identity(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_A'),fixture(1,b'SYNTH_B')])

    def test_wrong_name_prefix(self):
        with self.assertRaisesRegex(ValueError,'SYNTH'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'ORIGINAL')])

    def test_bad_name_non_ascii(self):
        with self.assertRaisesRegex(ValueError,'SYNTH'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_\xff')])

    def test_unsafe_name_length(self):
        with self.assertRaisesRegex(ValueError,'SYNTH'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_' + b'X'*145)])

    def test_reject_non_power_of_two(self):
        with self.assertRaisesRegex(ValueError,'power-of-two'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_H',width=6)])

    def test_reject_bad_mip_count(self):
        with self.assertRaisesRegex(ValueError,'mip'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_H',levels=9)])

    def test_reject_translucent(self):
        r=fixture(1,b'SYNTH_H')
        r['rgba']=r['rgba'][:-1]+bytes([8])
        with self.assertRaisesRegex(ValueError,'alpha'):
            build_synthetic_pc_dxt1_pack([r])

    def test_reject_identity_zero(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            build_synthetic_pc_dxt1_pack([fixture(0,b'SYNTH_H')])

    def test_reject_unknown_fields(self):
        r=fixture(1,b'SYNTH_H');r['other']=123
        with self.assertRaisesRegex(ValueError,'fields'):
            build_synthetic_pc_dxt1_pack([r])

    def test_reject_invalid_dimensions(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            build_synthetic_pc_dxt1_pack([fixture(1,b'SYNTH_H',width=4096)])

    def test_reject_damaged_rgba_length(self):
        r=fixture(1,b'SYNTH_H');r['rgba']=b'broken'
        with self.assertRaisesRegex(ValueError,'byte count'):
            build_synthetic_pc_dxt1_pack([r])

if __name__=='__main__':unittest.main()
