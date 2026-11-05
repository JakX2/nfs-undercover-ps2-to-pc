"""Synthetic-only DXT1 encoding, quantization and mip-chain regression tests."""
import struct
import unittest
from synthetic_dxt1_texture_writer import (
    encode_dxt1_base, encode_dxt1_block, encode_dxt1_mips,
    downsample_opaque_2x2)
from pc_dxt_reference_decode import decode_dxt_base, compare_rgba_nearest


def img(w, h, fn):
    return b''.join(bytes((*fn(x,y),255)) for y in range(h) for x in range(w))


class WriterTests(unittest.TestCase):
    def test_solid_red_exact(self):
        src=bytes((255,0,0,255))*16
        encoded=encode_dxt1_base(src,4,4)
        self.assertEqual(len(encoded),8)
        self.assertEqual(decode_dxt_base(encoded,4,4,b'DXT1'),src)

    def test_solid_black_is_opaque(self):
        src=bytes((0,0,0,255))*16
        dst=decode_dxt_base(encode_dxt1_base(src,4,4),4,4,b'DXT1')
        self.assertEqual(dst,src)

    def test_two_color_checkerboard_exact(self):
        src=img(4,4,lambda x,y:(255,0,0) if (x+y)%2 else (0,0,255))
        dst=decode_dxt_base(encode_dxt1_base(src,4,4),4,4,b'DXT1')
        self.assertEqual(dst,src)

    def test_odd_dimensions_and_clipped_blocks(self):
        src=img(5,7,lambda x,y:(255,0,0) if x<4 else (0,255,0))
        enc=encode_dxt1_base(src,5,7)
        self.assertEqual(len(enc),32)
        got=decode_dxt_base(enc,5,7,b'DXT1')
        self.assertEqual(got,src)

    def test_tiny_mip_levels_replicate(self):
        src=bytes((0,0,255,255))
        enc,spans=encode_dxt1_mips(src,1,1,1)
        self.assertEqual(spans,((1,1,0,8),))
        self.assertEqual(decode_dxt_base(enc,1,1,b'DXT1'),src)

    def test_opaque_gradient_limited_error(self):
        src=img(8,8,lambda x,y:(20*x,24*y, 12*(x+y)))
        enc=encode_dxt1_base(src,8,8)
        dst=decode_dxt_base(enc,8,8,b'DXT1')
        m=compare_rgba_nearest(dst,8,8,src,8,8)
        self.assertLess(m['mean_absolute_rgb_error'],22)
        self.assertEqual(m['mean_absolute_alpha_error'],0)

    def test_encoding_deterministic(self):
        src=img(8,8,lambda x,y:((x*31)%256,(y*71)%256,(x*y*17)%256))
        self.assertEqual(encode_dxt1_base(src,8,8),encode_dxt1_base(src,8,8))

    def test_opaque_mips_strict_layout(self):
        src=img(8,8,lambda x,y:(x*20,y*20,(x+y)*10))
        encoded,spans=encode_dxt1_mips(src,8,8,4)
        self.assertEqual(spans,((8,8,0,32),(4,4,32,8),(2,2,40,8),(1,1,48,8)))
        self.assertEqual(len(encoded),56)
        for w,h,off,size in spans:
            dst=decode_dxt_base(encoded[off:off+size],w,h,b'DXT1')
            self.assertEqual(len(dst),w*h*4)
            self.assertEqual(set(dst[3::4]),{255})

    def test_non_square_mips(self):
        src=bytes((255,255,0,255))*16
        _,spans=encode_dxt1_mips(src,2,8,4)
        self.assertEqual([x[:2] for x in spans],[(2,8),(1,4),(1,2),(1,1)])

    def test_filter_box_rounding(self):
        src=img(2,2,lambda x,y:(0,0,0) if x==0 else (3,3,3))
        dst,w,h=downsample_opaque_2x2(src,2,2)
        self.assertEqual((w,h),(1,1))
        self.assertEqual(dst,bytes((2,2,2,255)))

    def test_translucent_alpha_rejected(self):
        with self.assertRaisesRegex(ValueError,'alpha'):
            encode_dxt1_base(bytes((10,20,30,0))*16,4,4)

    def test_one_translucent_pixel_rejected(self):
        data=bytearray(bytes((10,20,30,255))*16);data[3]=254
        with self.assertRaisesRegex(ValueError,'alpha'):
            encode_dxt1_block(data)

    def test_reject_wrong_input_length(self):
        with self.assertRaisesRegex(ValueError,'byte count'):
            encode_dxt1_base(bytes(63),4,4)

    def test_reject_too_large(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            encode_dxt1_base(b'',4096,4096)

    def test_reject_float_dim(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            encode_dxt1_base(b'',4.0,4)

    def test_reject_mip_count(self):
        with self.assertRaisesRegex(ValueError,'mip count'):
            encode_dxt1_mips(bytes(4),1,1,2)

    def test_reject_boolean_mip(self):
        with self.assertRaisesRegex(ValueError,'mip count'):
            encode_dxt1_mips(bytes(4),1,1,True)

    def test_reject_wrong_type(self):
        with self.assertRaisesRegex(ValueError,'byte count'):
            encode_dxt1_base([1]*64,4,4)


if __name__=='__main__':unittest.main()
