"""Source-free regression tests for competing indexed PS2 layout hypotheses."""
import unittest
import hashlib
from ps2_texture_layout_candidates import (
    _gs_address, decode_indices, decode_rgba, palette_rgba, indices_to_rgba,
)


def encode_gs(indices, width, height, bits):
    # Synthetic GS memory fixture writer, only for exact full-page tests.
    raw = bytearray(width * height * bits // 8)
    for y in range(height):
        for x in range(width):
            off, shift = _gs_address(x, y, width, bits)
            if off >= len(raw):
                raise ValueError('Fixture cannot fit full-page GS memory')
            mask = ((1 << bits) - 1) << shift
            raw[off] = (raw[off] & ~mask) | ((indices[y * width + x] << shift) & mask)
    return bytes(raw)


class GSAddresses(unittest.TestCase):
    def test_psmct32_known_column_and_block_positions(self):
        self.assertEqual([_gs_address(x,y,64,32)[0] for x,y in
                          ((0,0),(1,0),(2,0),(0,1),(8,0),(0,8))],
                         [0,4,16,8,256,512])

    def test_psmt8_known_column_and_block_positions(self):
        self.assertEqual([_gs_address(x,y,128,8)[0] for x,y in
                          ((0,0),(8,0),(0,1),(0,2),(0,4),(0,16))],
                         [0,2,8,33,96,512])

    def test_psmt4_known_nibble_positions(self):
        self.assertEqual([_gs_address(x,y,128,4) for x,y in
                          ((0,0),(8,0),(0,2),(0,4),(32,0))],
                         [(0,0),(1,0),(32,4),(96,0),(512,0)])

    def test_psmt8_pages_across(self):
        self.assertEqual(_gs_address(128,0,256,8)[0],8192)
        self.assertEqual(_gs_address(0,64,256,8)[0],16384)

    def test_psmt4_pages_across(self):
        self.assertEqual(_gs_address(128,0,256,4)[0],8192)
        self.assertEqual(_gs_address(0,128,256,4)[0],16384)


class CandidateIndexes(unittest.TestCase):
    def test_linear8(self):
        self.assertEqual(decode_indices(b'\x03\x02\x01\x00',2,2,8),b'\x03\x02\x01\x00')

    def test_linear4_low_nibble_first(self):
        self.assertEqual(decode_indices(b'\xA1\xC3',4,1,4),bytes([1,10,3,12]))

    def test_vram8_full_page_round_trip(self):
        w,h=128,64
        source=bytes(((x//7) + y*3) & 255 for y in range(h) for x in range(w))
        self.assertEqual(decode_indices(encode_gs(source,w,h,8),w,h,8,'gs_vram'),source)

    def test_vram4_full_page_round_trip(self):
        w,h=128,128
        source=bytes(((x//3) + y*5) & 15 for y in range(h) for x in range(w))
        self.assertEqual(decode_indices(encode_gs(source,w,h,4),w,h,4,'gs_vram'),source)

    def test_transfer8_has_distinct_layout(self):
        w,h=128,64
        raw=bytes((x*7+y*11)&255 for y in range(h//2) for x in range(w*2))
        got=decode_indices(raw,w,h,8,'ct32_transfer')
        self.assertEqual(len(got),w*h)
        self.assertNotEqual(got,decode_indices(raw,w,h,8,'linear'))

    def test_transfer4_has_distinct_layout(self):
        w,h=128,128
        raw=bytes((x*7+y*11)&255 for y in range(h//4) for x in range(w*2))
        got=decode_indices(raw,w,h,4,'ct32_transfer')
        self.assertEqual(len(got),w*h)
        self.assertNotEqual(got,decode_indices(raw,w,h,4,'linear'))

    def test_independent_8bit_transfer_golden_vector(self):
        # Independent 8-bit Sparky/Victor Suba unswizzle yields this SHA-256.
        src=bytes((i*17+i//9)%256 for i in range(128*64))
        got=decode_indices(src,128,64,8,'ct32_transfer')
        self.assertEqual(hashlib.sha256(got).hexdigest(),
                         '1df1de3d36e03b96269f9480361a42bfcf1210e7bc015239cd432e2d437e34ef')

    def test_independent_4bit_transfer_golden_vector(self):
        # Independent 4-bit Sparky implementation yields this SHA-256.
        src=bytes((i*17+i//9)%256 for i in range(128*128//2))
        got=decode_indices(src,128,128,4,'ct32_transfer')
        self.assertEqual(hashlib.sha256(got).hexdigest(),
                         '1b067d38205d220de9361167193173d1c044ae6782e9e44d65be5602ae6dc740')

    def test_gs_vram_small_layout_rejected(self):
        with self.assertRaisesRegex(ValueError,'GS layout addresses'):
            decode_indices(bytes(16*32),16,32,8,'gs_vram')

    def test_ct32_transfer_odd_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError,'CT32 transfer'):
            decode_indices(bytes(4),1,8,4,'ct32_transfer')

    def test_wrong_packed_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'Wrong source'):
            decode_indices(bytes(32),16,16,8,'linear')

    def test_unknown_layout_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown explicit'):
            decode_indices(bytes(64),16,8,4,'auto')

    def test_dimensions_guard(self):
        with self.assertRaisesRegex(ValueError,'safety bound'):
            decode_indices(b'',8192,8192,8)


class Palettes(unittest.TestCase):
    def test_csm1_8bit_swaps_group_8_with_16(self):
        p=b''.join(bytes((i,0,0,128)) for i in range(256))
        c=palette_rgba(p,8,'csm1','double')
        self.assertEqual(c[8*4:8*4+4],bytes((16,0,0,255)))
        self.assertEqual(c[16*4:16*4+4],bytes((8,0,0,255)))
        self.assertEqual(c[24*4:24*4+4],bytes((24,0,0,255)))
        self.assertEqual(c[40*4:40*4+4],bytes((48,0,0,255)))

    def test_csm1_4bit_identity(self):
        p=b''.join(bytes((i,i,i,100)) for i in range(16))
        self.assertEqual(palette_rgba(p,4,'csm1'),p)

    def test_rgba_and_bgra_candidates(self):
        p=bytes((1,2,3,20))*16
        self.assertEqual(palette_rgba(p,4,'linear','raw','rgba')[:4],bytes((1,2,3,20)))
        self.assertEqual(palette_rgba(p,4,'linear','raw','bgra')[:4],bytes((3,2,1,20)))

    def test_alpha_raw_and_double(self):
        p=bytes((1,2,3,80))*16
        self.assertEqual(palette_rgba(p,4,'linear','raw')[:4],bytes((1,2,3,80)))
        self.assertEqual(palette_rgba(p,4,'linear','double')[:4],bytes((1,2,3,160)))

    def test_palette_wrong_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'palette byte count'):
            palette_rgba(bytes(12),4)

    def test_bad_index_rejected(self):
        with self.assertRaisesRegex(ValueError,'exceeds codec'):
            indices_to_rgba(bytes((16,)),bytes(64),4)

    def test_full_linear_rgba_pipeline(self):
        p=b''.join(bytes((i,i+1,i+2,100)) for i in range(16))
        got=decode_rgba(bytes((0x10,0x32)),p,4,1,4)
        self.assertEqual(got[:8],bytes((0,1,2,100,1,2,3,100)))
        self.assertEqual(got[8:],bytes((2,3,4,100,3,4,5,100)))


if __name__=='__main__':unittest.main()
