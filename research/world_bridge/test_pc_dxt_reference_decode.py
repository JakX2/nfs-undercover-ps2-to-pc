"""Synthetic base-block DXT and resolution-comparison regression controls."""
import unittest
from pc_dxt_reference_decode import decode_dxt_base, compare_rgba_nearest


class DXTTests(unittest.TestCase):
    def test_dxt1_opaque_red(self):
        block=(0xf800).to_bytes(2,'little')+bytes(2)+bytes(4)
        self.assertEqual(decode_dxt_base(block,4,4,b'DXT1'),bytes((255,0,0,255))*16)

    def test_dxt1_selector3_transparent(self):
        block=(0).to_bytes(2,'little')+(0xf800).to_bytes(2,'little')+(0xffffffff).to_bytes(4,'little')
        self.assertEqual(decode_dxt_base(block,4,4,b'DXT1'),bytes(64))

    def test_dxt1_opaque_blue(self):
        block=(0x1f).to_bytes(2,'little')+bytes(2)+bytes(4)
        self.assertEqual(decode_dxt_base(block,4,4,b'DXT1'),bytes((0,0,255,255))*16)

    def test_dxt3_four_bit_alpha_expands(self):
        block=bytes((0x0f,))*8+(0xf800).to_bytes(2,'little')+bytes(2)+bytes(4)
        pic=decode_dxt_base(block,4,4,b'DXT3')
        self.assertEqual(pic[:4],bytes((255,0,0,255)))
        self.assertEqual(pic[4:8],bytes((255,0,0,0)))

    def test_dxt5_alpha_8step(self):
        alpha=bytes((255,0))+bytes((0,0,0,0,0,0))
        block=alpha+(0xf800).to_bytes(2,'little')+bytes(2)+bytes(4)
        self.assertEqual(decode_dxt_base(block,4,4,b'DXT5'),bytes((255,0,0,255))*16)

    def test_dxt5_alpha_6step_explicit_zero(self):
        alpha=bytes((10,20))+(6).to_bytes(6,'little')
        block=alpha+(0xf800).to_bytes(2,'little')+bytes(2)+bytes(4)
        pic=decode_dxt_base(block,4,4,b'DXT5')
        self.assertEqual(pic[:4],bytes((255,0,0,0)))

    def test_multiple_blocks_and_cropping(self):
        red=(0xf800).to_bytes(2,'little')+bytes(2)+bytes(4)
        blue=(0x1f).to_bytes(2,'little')+bytes(2)+bytes(4)
        pic=decode_dxt_base(red+blue,5,4,b'DXT1')
        self.assertEqual(len(pic),5*4*4)
        self.assertEqual(pic[:4],bytes((255,0,0,255)))
        self.assertEqual(pic[4*4:5*4],bytes((0,0,255,255)))

    def test_unknown_fourcc_rejected(self):
        with self.assertRaisesRegex(ValueError,'FOURCC'):
            decode_dxt_base(bytes(8),4,4,b'DXT7')

    def test_wrong_byte_count_rejected(self):
        with self.assertRaisesRegex(ValueError,'byte count'):
            decode_dxt_base(bytes(3),4,4,b'DXT1')

    def test_unreasonable_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'dimensions'):
            decode_dxt_base(b'',8192,8192,b'DXT1')


class MetricTests(unittest.TestCase):
    def test_identical_images_match(self):
        pic=bytes((50,60,70,255))*4
        self.assertEqual(compare_rgba_nearest(pic,2,2,pic,2,2),{
            'compared_pixels':4,'mean_absolute_rgb_error':0.0,'mean_absolute_alpha_error':0.0})

    def test_nearest_scaling(self):
        pc=b''.join(bytes((20,20,20,255)) if x<2 else bytes((100,100,100,255)) for y in range(4) for x in range(4))
        ps=bytes((20,20,20,255))+bytes((100,100,100,255))
        got=compare_rgba_nearest(pc,4,4,ps,2,1)
        self.assertEqual(got['compared_pixels'],2)
        self.assertEqual(got['mean_absolute_alpha_error'],0.0)
        self.assertEqual(got['mean_absolute_rgb_error'],0.0)

    def test_comparison_dimension_rejected(self):
        with self.assertRaisesRegex(ValueError,'buffer length'):
            compare_rgba_nearest(bytes(3),1,1,bytes(4),1,1)


if __name__=='__main__':unittest.main()
