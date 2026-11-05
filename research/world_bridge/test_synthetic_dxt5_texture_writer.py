"""Synthetic-only BC3/DXT5 base, alpha, palette and mip regressions."""
import unittest
from synthetic_dxt5_texture_writer import (
    _alpha_palette,encode_dxt5_alpha_block,encode_dxt5_block,encode_dxt5_base,
    encode_dxt5_mips,downsample_rgba_2x2)
from pc_dxt_reference_decode import decode_dxt_base

class DXT5BlockTests(unittest.TestCase):
    def test_constant_alpha_exact(self):
        for a in (0,1,33,128,254,255):
            with self.subTest(a=a):
                rgba=bytes((255,0,0,a))*16
                got=decode_dxt_base(encode_dxt5_block(rgba),4,4,b'DXT5')
                self.assertEqual(got,rgba)
    def test_binary_alpha_exact(self):
        rgba=b''.join(bytes((0,255,0,255 if i&1 else 0)) for i in range(16))
        self.assertEqual(decode_dxt_base(encode_dxt5_block(rgba),4,4,b'DXT5'),rgba)
    def test_alpha_gradient_bounded(self):
        rgba=b''.join(bytes((0,0,255,i*17)) for i in range(16))
        got=decode_dxt_base(encode_dxt5_block(rgba),4,4,b'DXT5')
        self.assertLess(sum(abs(got[k]-rgba[k]) for k in range(3,64,4))/16,14)
    def test_alpha_block_deterministic(self):
        src=bytes((10,22,37,64,80,90,94,102,111,118,120,170,204,208,248,255))
        self.assertEqual(encode_dxt5_alpha_block(src),encode_dxt5_alpha_block(src))
        self.assertEqual(len(encode_dxt5_alpha_block(src)),8)
    def test_palette_matches_decoder_modes(self):
        self.assertEqual(_alpha_palette(255,0),(255,0,218,182,145,109,72,36))
        self.assertEqual(_alpha_palette(0,255),(0,255,51,102,153,204,0,255))
    def test_wrong_block_type_or_length_rejected(self):
        for bad in (b'broken',bytes(63),None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                encode_dxt5_block(bad)
        for bad in (bytes(15),bytes(17),None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                encode_dxt5_alpha_block(bad)
    def test_transparency_retained_not_coerced(self):
        rgba=bytes((100,150,200,0))*16
        got=decode_dxt_base(encode_dxt5_block(rgba),4,4,b'DXT5')
        self.assertEqual(got[3::4],bytes(16))

class DXT5ImageTests(unittest.TestCase):
    def test_nonsquare_odd_dimensions(self):
        rgba=bytes((255,0,0,40))*15
        packed=encode_dxt5_base(rgba,5,3)
        self.assertEqual(len(packed),32)
        self.assertEqual(decode_dxt_base(packed,5,3,b'DXT5'),rgba)
    def test_image_truncated_rejected(self):
        with self.assertRaisesRegex(ValueError,'byte count'):
            encode_dxt5_base(bytes(20),4,4)
    def test_unreasonable_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            encode_dxt5_base(b'',8192,8192)
    def test_reproducibility(self):
        source=b''.join(bytes((i*5%256,i*11%256,i*13%256,i*17%256)) for i in range(64))
        self.assertEqual(encode_dxt5_base(source,8,8),encode_dxt5_base(source,8,8))
    def test_mips_exact_size_and_monotonic(self):
        source=bytes((20,60,100,170))*128
        packed,spans=encode_dxt5_mips(source,16,8,5)
        self.assertEqual([s[:2] for s in spans],[(16,8),(8,4),(4,2),(2,1),(1,1)])
        self.assertEqual([s[3] for s in spans],[128,32,16,16,16])
        self.assertEqual(len(packed),208)
        for w,h,offset,n in spans:
            self.assertEqual(len(decode_dxt_base(packed[offset:offset+n],w,h,b'DXT5')),w*h*4)
    def test_max_mips_exceeded(self):
        with self.assertRaisesRegex(ValueError,'mip'):
            encode_dxt5_mips(bytes((0,0,0,0))*16,4,4,4)
    def test_downsample_prevents_transparent_color_bleeding(self):
        rgba=bytes((255,0,0,255)) + bytes((0,0,255,0))*3
        got,w,h=downsample_rgba_2x2(rgba,2,2)
        self.assertEqual((w,h),(1,1))
        self.assertEqual(got,bytes((255,0,0,64)))
    def test_downsample_all_invisible_defined(self):
        rgba=bytes((30,60,90,0))*4
        self.assertEqual(downsample_rgba_2x2(rgba,2,2)[0],bytes((30,60,90,0)))
    def test_alpha_candidate_6_step_can_win(self):
        vals=bytes((120,124,128,130,133,135,140,142,143,145,145,148,150,150,0,255))
        encoded=encode_dxt5_alpha_block(vals)
        self.assertEqual(len(encoded),8)
        pic=decode_dxt_base(encoded+bytes((0,0,0,0,0,0,0,0)),4,4,b'DXT5')
        self.assertLess(sum(abs(pic[i*4+3]-vals[i]) for i in range(16)),100)
if __name__=='__main__':unittest.main()
