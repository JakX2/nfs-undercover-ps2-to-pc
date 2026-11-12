"""Synthetic-only two-resolution PS2 texture/alpha consistency controls."""
import struct
import unittest
from test_texture_visual_pair_gate import chunk
from undercover_texture_variant_visual_control import compare_variant_sections


def source_pack(width=16,bits=4,hashes=(0x11111111,0x22222222),
                name_prefix=b'TEST_',flag=0,damage_color=False,mip_levels=1):
    height=width
    metadata=bytearray();platform=bytearray();pixel=bytearray(2048*len(hashes))
    for j,h in enumerate(hashes):
        size=sum(max(1,width>>k)*max(1,height>>k)*bits//8 for k in range(mip_levels))
        base=width*height*bits//8
        palette_size=64 if bits==4 else 1024
        pal_off=j*2048
        img_off=j*2048+1024
        # Identical palettes/texel logic regardless of resolution; quadrants.
        palette=bytearray(palette_size)
        palette[4:8]=bytes((255,0,0,128))
        palette[8:12]=bytes((0,0,255,64))
        if damage_color and j==0:palette[4:8]=bytes((0,200,0,64))
        pixel[pal_off:pal_off+palette_size]=palette
        out=bytearray()
        for level in range(mip_levels):
            w=max(1,width>>level);lh=max(1,height>>level)
            idx=bytes(1 if ((x<w//2)^(y<lh//2)) else 2
                      for y in range(lh) for x in range(w))
            if bits==4:out.extend(idx[i]|(idx[i+1]<<4) for i in range(0,len(idx),2))
            else:out.extend(idx)
        img=bytes(out)
        pixel[img_off:img_off+size]=img
        rec=bytearray(88)
        struct.pack_into('<I',rec,12,h)
        struct.pack_into('<5I',rec,20,img_off,pal_off,size,palette_size,base)
        struct.pack_into('<HH',rec,40,width,height)
        rec[44]=width.bit_length()-1;rec[45]=height.bit_length()-1;rec[46]=bits
        struct.pack_into('<H',rec,48,1<<bits)
        rec[50]=mip_levels;rec[51]=1
        name=name_prefix+str(j).encode()
        padded=((len(name)+2+3)//4)*4-1
        rec+=bytes((padded,))+name+bytes(padded-len(name))
        metadata+=rec
        pl=bytearray(84);pl[0x17]=flag;pl[4]=0x14 if bits==4 else 0x13
        platform+=pl
    desc=chunk(0xB3310000,chunk(0x33310001,b'HEADER')+
               chunk(0x33310002,b''.join(struct.pack('<II',h,0) for h in hashes))+
               chunk(0x33310004,metadata)+chunk(0x33310005,platform))
    prefix=chunk(0,bytes(48))+desc+chunk(0,bytes(80))
    hdr=chunk(0x33320001,bytes(24))+chunk(0,bytes(80))
    payload_start=8+len(prefix)+8+len(hdr)+8
    pad=(-payload_start)%128
    res=chunk(0xB3320000,hdr+chunk(0x33320002,bytes([0x11])*pad+pixel))
    return chunk(0xB3300000,prefix+res)


class VariantImageTests(unittest.TestCase):
    def test_4bit_identical_images_and_alpha(self):
        r=compare_variant_sections({241:source_pack(),3401:source_pack(8)})
        self.assertEqual(r['cross_section_shared_identities'],2)
        self.assertEqual(r['by_indexed_depth']['4']['mean_rgb_mae'],0)
        self.assertEqual(r['by_indexed_depth']['4']['mean_alpha_mae'],0)
        self.assertEqual(r['swizzle_flag_pair_counts'],{'0/0':2})

    def test_8bit_identical_images_and_alpha(self):
        r=compare_variant_sections({241:source_pack(bits=8),3401:source_pack(8,bits=8)})
        self.assertEqual(r['by_indexed_depth']['8']['mean_rgb_mae'],0)

    def test_changed_palette_increases_error(self):
        r=compare_variant_sections({241:source_pack(),3401:source_pack(8,damage_color=True)})
        self.assertGreater(r['by_indexed_depth']['4']['mean_rgb_mae'],0)
        self.assertLess(r['all']['pairs_below_20_rgb_mae'],2)

    def test_bad_ratio_rejected(self):
        with self.assertRaisesRegex(ValueError,'exactly 2x'):
            compare_variant_sections({241:source_pack(),3401:source_pack()})

    def test_missing_section_rejected(self):
        with self.assertRaisesRegex(ValueError,'both Undercover'):
            compare_variant_sections({241:source_pack()})

    def test_different_hash_sets_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity sets'):
            compare_variant_sections({241:source_pack(),3401:source_pack(8,hashes=(3,4))})

    def test_same_hash_different_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity conflict'):
            compare_variant_sections({241:source_pack(),3401:source_pack(8,name_prefix=b'OTHER_')})

    def test_bad_flag_rejected(self):
        with self.assertRaisesRegex(ValueError,'swizzle flag'):
            compare_variant_sections({241:source_pack(),3401:source_pack(8,flag=3)})

    def test_bad_section_bytes_rejected(self):
        with self.assertRaises(ValueError):
            compare_variant_sections({241:source_pack(),3401:source_pack(8)[:-12]})

    def test_does_not_export_identities_or_colors(self):
        r=compare_variant_sections({241:source_pack(),3401:source_pack(8)})
        self.assertNotIn('TEST_',repr(r))
        self.assertNotIn('286331153',repr(r))
        self.assertIn('CONSISTENCY ONLY',r['verdict'])


if __name__=='__main__':unittest.main()
