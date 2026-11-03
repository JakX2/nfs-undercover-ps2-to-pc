"""Synthetic-only Carbon PC/PS2 same-hash pixel comparison audit tests."""
import struct
import unittest
from texture_visual_pair_gate import compare_sections, _options


def chunk(tag, data):
    return struct.pack('<II', tag, len(data)) + data


def make_pack(platform='pc', bits=8, hashes=(0x11111111,0x22222222),
              identical=False, corrupt_palette=False, constant=False, name_prefix=b'SYNTHETIC_'):
    width=height=8
    metadata=bytearray()
    platform_meta=bytearray()
    pixel=bytearray(8192 if platform == 'ps2' else 4096)
    for j, h in enumerate(hashes):
        color_blocks = ((0,1,1,0) if j==0 else (1,0,0,1))
        if constant: color_blocks=(0,0,0,0)
        if platform=='pc':
            codec=34; image_size=32; base_size=32; palette_size=0; palette_offset=0
            image_offset=64+j*256
            # One DXT1 color block per 4x4 tile, red or blue.
            image=b''.join(struct.pack('<HHI',0xf800 if v==0 else 0x001f,0,0) for v in color_blocks)
            pixel[image_offset:image_offset+len(image)]=image
            pm=bytearray(24);pm[12:16]=b'DXT1';platform_meta+=pm
        else:
            codec=bits;image_size=width*height*bits//8; base_size=image_size
            palette_size=64 if bits==4 else 1024
            palette_offset=j*1024
            image_offset=3000+j*256
            pixel[palette_offset+4:palette_offset+8]=bytes((255,0,0,255))
            pixel[palette_offset+8:palette_offset+12]=bytes((0,0,255,255))
            # Each 4x4 quadrant corresponds to one DXT block
            values=bytearray(1 if color_blocks[(y//4)*2+x//4]==0 else 2
                             for y in range(height) for x in range(width))
            if bits==8:
                image=values
            else:
                image=bytearray(values[i] | (values[i+1]<<4) for i in range(0,len(values),2))
            pixel[image_offset:image_offset+len(image)]=image
            platform_meta+=bytes(84)
            if corrupt_palette:
                palette_size=16
        record=bytearray(88)
        struct.pack_into('<I',record,12,h)
        struct.pack_into('<5I',record,20,image_offset,palette_offset,image_size,palette_size,base_size)
        struct.pack_into('<HH',record,40,width,height)
        record[44]=3; record[45]=3;record[46]=codec
        struct.pack_into('<H',record,48,(0 if platform=='pc' else (16 if bits==4 else 256)))
        record[50]=1;record[51]=1
        name=name_prefix+str(j).encode()
        padded=((len(name)+2+3)//4)*4-1
        record+=bytes((padded,))+name+bytes(padded-len(name))
        metadata+=record
    desc=chunk(0xB3310000,
               chunk(0x33310001,b'HEADER')+
               chunk(0x33310002,b''.join(struct.pack('<II',h,0) for h in hashes))+
               chunk(0x33310004,metadata)+
               chunk(0x33310005,platform_meta))
    pix=chunk(0xB3320000,chunk(0x33320001,bytes(24))+chunk(0,bytes(80))+chunk(0x33320002,pixel))
    return chunk(0xB3300000,chunk(0,bytes(48))+desc+chunk(0,bytes(80))+pix)


class VisualPairGateTests(unittest.TestCase):
    def test_same_hash_linear_rgb_matches_synthetic_dxt1(self):
        report=compare_sections(make_pack(),make_pack('ps2'),2)
        self.assertEqual(report['shared_identity_count'],2)
        self.assertEqual(report['sampled_pairs'],2)
        self.assertEqual(report['spatially_informative_pairs'],2)
        self.assertEqual(report['sampled_provisional_ps2_plus_0x17_flag_counts'],{'0':2})
        row=next(r for r in report['candidates'] if r['hypothesis']=='linear/linear/raw/rgba')
        self.assertEqual(row['mean_rgb_mae'],0)
        self.assertEqual(row['mean_alpha_mae'],0)
        self.assertEqual(row['supported_pairs'],2)
        self.assertTrue(row['complete_coverage'])

    def test_wrong_channels_are_worse(self):
        r=compare_sections(make_pack(),make_pack('ps2'),2)
        by={c['hypothesis']:c for c in r['candidates']}
        self.assertGreater(by['linear/linear/raw/bgra']['mean_rgb_mae'],by['linear/linear/raw/rgba']['mean_rgb_mae'])

    def test_same_hash_4bit_candidate(self):
        r=compare_sections(make_pack(),make_pack('ps2',bits=4),2)
        self.assertEqual(next(x for x in r['candidates'] if x['hypothesis']=='linear/linear/raw/rgba')['mean_rgb_mae'],0)
        self.assertFalse(any('/csm1/' in c['hypothesis'] for c in r['candidates']))

    def test_candidate_failures_not_silently_ignored(self):
        r=compare_sections(make_pack(),make_pack('ps2'),2)
        row=next(x for x in r['candidates'] if x['hypothesis']=='gs_vram/linear/raw/rgba')
        self.assertEqual(row['supported_pairs'],0)
        self.assertEqual(row['failed_pairs'],2)
        self.assertIsNone(row['mean_rgb_mae'])

    def test_nonmatching_hash_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'two safe matching'):
            compare_sections(make_pack(),make_pack('ps2',hashes=(0x33333333,0x44444444)))

    def test_one_shared_hash_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'two safe matching'):
            compare_sections(make_pack(hashes=(0x11111111,0x22222222)),make_pack('ps2',hashes=(0x11111111,0x33333333)))

    def test_invalid_palette_rejected(self):
        with self.assertRaisesRegex(ValueError,'palette size'):
            compare_sections(make_pack(),make_pack('ps2',corrupt_palette=True))

    def test_sample_limit_rejected(self):
        for n in (0,1,13,2.0,True):
            with self.subTest(n=n),self.assertRaisesRegex(ValueError,'max_pairs'):
                compare_sections(make_pack(),make_pack('ps2'),n)

    def test_privacy_aggregate_excludes_names_and_hashes(self):
        report=compare_sections(make_pack(),make_pack('ps2'),2)
        text=repr(report)
        self.assertNotIn('SYNTHETIC_',text)
        self.assertNotIn('286331153',text)
        self.assertNotIn('0x11111111',text)
        self.assertIn('UNVERIFIED',text)

    def test_matching_hash_with_different_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity metadata mismatch'):
            compare_sections(make_pack(),make_pack('ps2',name_prefix=b'DIFFERENT_'),2)

    def test_wrong_record_bounds_rejected(self):
        with self.assertRaises(ValueError):
            compare_sections(make_pack()[:150],make_pack('ps2'),2)

    def test_uniform_images_report_lack_of_spatial_evidence(self):
        r=compare_sections(make_pack(constant=True),make_pack('ps2',constant=True),2)
        self.assertEqual(r['sampled_uniform_pc_images'],2)
        self.assertEqual(r['spatially_informative_pairs'],0)

    def test_options_count_and_4bpp_degenerate_removal(self):
        self.assertEqual(len(list(_options(8))),24)
        self.assertEqual(len(list(_options(4))),12)


if __name__=='__main__':unittest.main()