"""Synthetic-only donor-section layout and archive safety controls."""
import struct
import tempfile
from pathlib import Path
import unittest
import zipfile
from test_texture_visual_pair_gate import make_pack
from undercover_ps2_texture_layout_coverage import analyze_sections, analyze_original_archive


def fixture():
    a=make_pack('ps2',bits=4)
    b=make_pack('ps2',bits=8)
    start_a=2048
    start_b=((start_a+len(a)+2047)//2048)*2048
    rows=bytearray(92*2)
    for i,(section,off,data) in enumerate(((241,start_a,a),(3401,start_b,b))):
        struct.pack_into('<h',rows,i*92+8,section)
        struct.pack_into('<II',rows,i*92+0x14,off,len(data))
    bun=struct.pack('<II',0x34110,len(rows))+rows
    stream=bytearray(start_b+len(b))
    stream[start_a:start_a+len(a)]=a
    stream[start_b:start_b+len(b)]=b
    return bun,bytes(stream),a,b


class CoverageTests(unittest.TestCase):
    def test_both_sections_base_buffers_decode(self):
        _,_,a,b=fixture()
        report=analyze_sections({241:a,3401:b})
        self.assertEqual(report['total_source_records'],4)
        self.assertEqual(report['total_decoded_base_images'],4)
        self.assertEqual(report['shared_source_texture_identities'],2)
        self.assertEqual(report['sections']['241']['four_bit_linear'],2)
        self.assertEqual(report['sections']['3401']['eight_bit_linear'],2)
        self.assertGreater(report['sections']['241']['pixel_alignment_pad_bytes'],0)
        self.assertNotIn('286331153',repr(report))

    def test_archive_reader_full_crc_and_sections(self):
        bun,stream,_,_=fixture()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'TRACKS.zip'
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('TRACKS/L2RB.BUN',bun)
                z.writestr('TRACKS/STREAML2RB.BUN',stream)
            self.assertEqual(analyze_original_archive(path)['total_decoded_base_images'],4)

    def test_bad_section_ids_rejected(self):
        _,_,a,b=fixture()
        with self.assertRaisesRegex(ValueError,'both original'):
            analyze_sections({241:a,3402:b})

    def test_missing_archive_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing original'):
            analyze_original_archive('/this/path/does/not/exist.zip')

    def test_invalid_palette_fails_without_partial_success(self):
        _,_,a,b=fixture()
        with self.assertRaises(ValueError):
            analyze_sections({241:a[:-12],3401:b})


if __name__=='__main__':unittest.main()
