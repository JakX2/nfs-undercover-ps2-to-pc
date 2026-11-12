"""Source-free, synthetic archive-stream/CRC regression tests."""
import io
import struct
import tempfile
from pathlib import Path
import unittest
import zipfile
import zlib

from test_texture_visual_pair_gate import make_pack
from texture_original_archive_pair_audit import (
    _bounds,_capture,_split_chunks,_read_regular,_read_split,analyze_archives)
from track_bundle_probe import SplitZip


def fixture_stream(platform='ps2'):
    a=make_pack(platform)
    b=make_pack(platform,bits=4)
    starts=(2048, ((2048+len(a)+2047)//2048)*2048)
    rows=bytearray(92*2)
    for i,(n,start,data) in enumerate(zip((141,142),starts,(a,b))):
        at=i*92
        struct.pack_into('<h',rows,at+8,n)
        struct.pack_into('<II',rows,at+0x14,start,len(data))
    bun=struct.pack('<II',0x34110,len(rows))+rows
    stream=bytearray(starts[1]+len(b))
    stream[starts[0]:starts[0]+len(a)]=a
    stream[starts[1]:starts[1]+len(b)]=b
    return bun,bytes(stream),a,b


def write_zip(path,bun,stream,method=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path,'w',compression=method) as z:
        z.writestr('TRACKS/L5RB.BUN',bun)
        z.writestr('TRACKS/STREAML5RB.BUN',stream)


def make_split_paths(directory,bun,stream):
    """Create a genuine synthetic two-disk PKZIP layout from standard ZIP."""
    regular=Path(directory)/'original.zip'
    write_zip(regular,bun,stream)
    raw=bytearray(regular.read_bytes())
    eocd=raw.rfind(b'PK\x05\x06')
    cd_start=struct.unpack_from('<I',raw,eocd+16)[0]
    # Entire member data on disk 0, central directory/EOCD on disk 1.
    final=bytearray(raw[cd_start:])
    final_eocd=final.rfind(b'PK\x05\x06')
    struct.pack_into('<HH',final,final_eocd+4,1,1)
    struct.pack_into('<I',final,final_eocd+16,0)
    local=Path(directory)/'TRACKS.z01'
    last=Path(directory)/'TRACKS.zip'
    local.write_bytes(raw[:cd_start])
    last.write_bytes(final)
    return (local,last)


class StreamReaderTests(unittest.TestCase):
    def test_section_rows_bounds_and_alignment(self):
        bun,stream,a,b=fixture_stream()
        mapping=_bounds(bun,len(stream),(141,142))
        self.assertEqual(mapping[141][1],len(a))
        self.assertEqual(mapping[142][1],len(b))
        with self.assertRaisesRegex(ValueError,'Missing requested'):
            _bounds(bun,len(stream),(143,))

    def test_regular_zip_extracts_only_two_sections(self):
        bun,stream,a,b=fixture_stream()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ps2.zip'
            write_zip(path,bun,stream)
            got=_read_regular(path)
            self.assertEqual(got[141],a)
            self.assertEqual(got[142],b)

    def test_regular_zip_stored_member(self):
        bun,stream,a,b=fixture_stream()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ps2.zip'
            write_zip(path,bun,stream,zipfile.ZIP_STORED)
            self.assertEqual(_read_regular(path)[141],a)

    def test_actual_synthetic_split_zip_crc_and_section_extraction(self):
        bun,stream,a,b=fixture_stream()
        with tempfile.TemporaryDirectory() as d:
            parts=make_split_paths(d,bun,stream)
            got=_read_split(parts)
            self.assertEqual(got[141],a)
            self.assertEqual(got[142],b)

    def test_archive_integration_pairs_and_aggregate_only(self):
        bun,stream,_,_=fixture_stream()
        # These are synthetic PS2 archives, not PC, so a PC-vs-PS2 audit must
        # fail the strict PC metadata validation rather than report scores.
        with tempfile.TemporaryDirectory() as d:
            parts=make_split_paths(d,bun,stream)
            ps2=Path(d)/'ps2.zip'
            write_zip(ps2,bun,stream)
            with self.assertRaisesRegex(ValueError,'platform metadata stride'):
                analyze_archives(parts,ps2,max_pairs=2)

    def test_end_to_end_source_free_paired_archive_score(self):
        pc_bun,pc_stream,_,_=fixture_stream('pc')
        ps2_bun,ps2_stream,_,_=fixture_stream('ps2')
        with tempfile.TemporaryDirectory() as d:
            parts=make_split_paths(d,pc_bun,pc_stream)
            ps2=Path(d)/'ps2.zip'
            write_zip(ps2,ps2_bun,ps2_stream)
            report=analyze_archives(parts,ps2,max_pairs=2)
            self.assertEqual(sorted(report['sections']),['141','142'])
            for sec in ('141','142'):
                self.assertEqual(report['sections'][sec]['shared_identity_count'],2)
                row=next(x for x in report['sections'][sec]['candidates']
                         if x['hypothesis']=='linear/linear/raw/rgba')
                self.assertEqual(row['mean_rgb_mae'],0)
            self.assertNotIn('SYNTHETIC_',repr(report))
            self.assertIn('UNVERIFIED',report['verdict'])

    def test_split_zip_crc_corruption_fails(self):
        bun,stream,_,_=fixture_stream()
        with tempfile.TemporaryDirectory() as d:
            parts=make_split_paths(d,bun,stream)
            split=SplitZip(parts)
            name='TRACKS/STREAML5RB.BUN'
            original=split.entries[name]
            # Corrupt expected CRC in a fake copy of the central-index tuple.
            split.entries[name]=(*original[:5],original[5]^0x01000000)
            with self.assertRaisesRegex(ValueError,'CRC'):
                list(_split_chunks(split,name))

    def test_out_of_bounds_capture_rejected(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):
            _capture([b'a'*8],16,{141:(0,12)})

    def test_section_range_collision_rejected(self):
        bun,stream,_,_=fixture_stream()
        raw=bytearray(bun)
        struct.pack_into('<II',raw,8+92+0x14,2048,4096)
        with self.assertRaisesRegex(ValueError,'overlap'):
            _bounds(raw,len(stream),(141,142))

    def test_duplicate_section_rows_rejected(self):
        bun,stream,_,_=fixture_stream()
        raw=bytearray(bun)
        struct.pack_into('<h',raw,8+92+8,141)
        with self.assertRaisesRegex(ValueError,'Duplicate section'):
            _bounds(raw,len(stream),(141,142))

    def test_oversize_or_missing_bounds_rejected(self):
        bun,stream,_,_=fixture_stream()
        with self.assertRaisesRegex(ValueError,'Invalid requested'):
            _bounds(bun,len(stream),(141,141))
        with self.assertRaisesRegex(ValueError,'Malformed'):
            _bounds(bun[:-1],len(stream),(141,142))


if __name__=='__main__':unittest.main()
