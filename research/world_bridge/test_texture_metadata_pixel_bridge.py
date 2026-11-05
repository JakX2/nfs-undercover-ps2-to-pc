"""Synthetic-only texture-metadata, mip-byte and pixel-span regression tests."""
import struct
import unittest
from texture_metadata_pixel_bridge import parse_pack,mip_size,compare_carbon

def chunk(cid,data):return struct.pack('<II',cid,len(data))+data

def build(platform='pc',kind=34,levels=2,wrong_fourcc=False,clash=False,
          wrong_name=False,broken_base=False,wrong_hash=False,wrong_pointer=False,
          bad_platform_stride=False,damage_name_header=False,missing_pixels=False):
    w,h=8,8
    if platform=='ps2' and kind not in (4,8):kind=4
    ntex=2
    index=[0x11111111,0x22222222]
    idx=b''.join(struct.pack('<II',v,1 if wrong_pointer and i==0 else 0) for i,v in enumerate(index))
    meta=b'';pl=b''
    pdata_len=4096 if platform=='ps2' and kind==8 else 2048
    for i,hsh in enumerate(index):
        comp=kind
        base=mip_size(w,h,comp,1)
        image=mip_size(w,h,comp,levels)
        palette=0 if platform=='pc' else (64 if comp==4 else 1024)
        offset=0 if i==0 else (8 if clash else 1600)
        paloff=0 if platform=='pc' else (1024 if i==0 else (64 if clash else 512))
        if platform=='ps2':
            offset=(2200 if i==0 else 2304) if kind==8 else (256 if i==0 else (280 if clash else 1664))
            paloff=(0 if i==0 else 1024) if kind==8 else (0 if i==0 else (8 if clash else 1024))
        rec=bytearray(88)
        if damage_name_header and i==0:rec[0]=7
        struct.pack_into('<I',rec,12,hsh if not wrong_hash or i!=0 else 0xbadc0de)
        struct.pack_into('<5I',rec,20,offset,paloff,image,palette,base+(16 if broken_base and i==0 else 0))
        struct.pack_into('<HH',rec,40,w,h)
        rec[44]=3;rec[45]=3;rec[46]=comp
        struct.pack_into('<H',rec,48,0 if platform=='pc' else (16 if comp==4 else 256))
        rec[50]=levels
        rec[51]=3
        names=(b'TEST_A',b'TEST_B')
        text=names[i]
        # Pad length such that length % 4 == 3 and name is NUL-terminated.
        n=((len(text)+1+3)//4)*4-1
        if wrong_name and i==0:n+=1
        rec+=bytes([n])+text+b'\0'*(n-len(text))
        meta+=rec
        if platform=='pc':
            plat=bytearray(24)
            plat[12:16]=b'FAIL' if wrong_fourcc and i==0 else {34:b'DXT1',36:b'DXT3',38:b'DXT5'}.get(comp,b'BAD!')
            pl+=plat
        else:pl+=bytes(84)
    if bad_platform_stride:pl=pl[:-1]
    pack_header=chunk(0x33310001,b'HEADER')
    descr=chunk(0xb3310000,pack_header+chunk(0x33310002,idx)+chunk(0x33310004,meta)+chunk(0x33310005,pl))
    px=chunk(0xb3320000,chunk(0x33320001,bytes(24))+chunk(0,bytes(80))+chunk(0x33320002,b'' if missing_pixels else bytes(pdata_len)))
    return chunk(0xb3300000,chunk(0,bytes(48))+descr+chunk(0,bytes(80))+px)

class MetadataPixelTests(unittest.TestCase):
    def test_valid_pc_dxt1(self):
        r=parse_pack(build(),'pc')
        self.assertEqual(r['summary']['indexed_texture_records'],2)
        self.assertEqual(r['summary']['valid_palette_ranges'],0)
        self.assertEqual(r['summary']['platform_info_bytes_per_record'],24)

    def test_valid_pc_dxt5(self):
        self.assertEqual(parse_pack(build(kind=38),'pc')['summary']['image_compression_types'],{38:2})

    def test_valid_pc_dxt3(self):
        self.assertEqual(parse_pack(build(kind=36),'pc')['summary']['image_compression_types'],{36:2})

    def test_valid_ps2_4bit(self):
        r=parse_pack(build('ps2',kind=4,levels=1),'ps2')
        self.assertEqual(r['summary']['valid_palette_ranges'],2)
        self.assertEqual(r['summary']['platform_info_bytes_per_record'],84)

    def test_valid_ps2_8bit(self):
        r=parse_pack(build('ps2',kind=8,levels=1),'ps2')
        self.assertEqual(r['summary']['valid_palette_ranges'],2)
        self.assertEqual(r['summary']['image_compression_types'],{8:2})

    def test_correct_dxt_mipmap_formula(self):
        self.assertEqual(mip_size(256,256,34,6),43680)
        self.assertEqual(mip_size(256,256,38,6),87360)

    def test_reject_hash_pointer(self):
        with self.assertRaisesRegex(ValueError,'pointer'):
            parse_pack(build(wrong_pointer=True),'pc')

    def test_reject_metadata_hash(self):
        with self.assertRaisesRegex(ValueError,'metadata hash'):
            parse_pack(build(wrong_hash=True),'pc')

    def test_reject_name_header(self):
        with self.assertRaisesRegex(ValueError,'lead-in'):
            parse_pack(build(damage_name_header=True),'pc')

    def test_reject_name_length(self):
        with self.assertRaisesRegex(ValueError,'name'):
            parse_pack(build(wrong_name=True),'pc')

    def test_reject_wrong_dxt_fourcc(self):
        with self.assertRaisesRegex(ValueError,'FOURCC'):
            parse_pack(build(wrong_fourcc=True),'pc')

    def test_reject_mismatched_base_size(self):
        with self.assertRaisesRegex(ValueError,'Image bytes disagree'):
            parse_pack(build(broken_base=True),'pc')

    def test_reject_wrong_platform_info_stride(self):
        with self.assertRaisesRegex(ValueError,'metadata stride'):
            parse_pack(build(bad_platform_stride=True),'pc')

    def test_reject_overlapping_images(self):
        with self.assertRaisesRegex(ValueError,'overlap'):
            parse_pack(build(clash=True),'pc')

    def test_reject_empty_pixel_array(self):
        with self.assertRaisesRegex(ValueError,'header/payload'):
            parse_pack(build(missing_pixels=True),'pc')

    def test_reject_wrong_platform(self):
        with self.assertRaisesRegex(ValueError,'Bad platform'):
            parse_pack(build(),'wii')

    def test_donor_resolution_variants_are_distinguished(self):
        a=parse_pack(build(),'pc')
        b=parse_pack(build(),'pc')
        r=compare_carbon(a,b)
        self.assertEqual(r['common_texture_hashes'],2)
        self.assertEqual(r['same_dimensions'],2)

    def test_unknown_codec_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported PC DXT'):
            parse_pack(build('pc',kind=4),'pc')

    def test_palette_ranged_and_disjoint(self):
        got=parse_pack(build('ps2',kind=4,levels=1),'ps2')
        self.assertTrue(got['summary']['all_pixel_spans_disjoint'])

if __name__=='__main__':unittest.main()
