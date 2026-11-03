"""Synthetic-only tests of candidate 92-byte 0x34110 section rows."""
import struct
import unittest
from track_stream_section_probe import (find_chunk, parse_sections, compare_section_ids, ROW_SIZE)


def row(name=b"X0", number=2400, offset=0, size=64,
        compressed=None, status=0, filetype=1):
    if compressed is None:
        compressed=size
    block=bytearray(ROW_SIZE)
    block[:len(name)]=name
    struct.pack_into('<h',block,8,number)
    struct.pack_into('<I',block,0x0c,status)
    struct.pack_into('<I',block,0x10,filetype)
    struct.pack_into('<III',block,0x14,offset,size,compressed)
    return bytes(block)


def chunk(cid,data=b""):
    return struct.pack('<II',cid,len(data))+data


class TrackSectionTests(unittest.TestCase):
    def test_valid_two_rows(self):
        identities, stats=parse_sections(row()+row(b'Z0',2600,4096,500),10000)
        self.assertEqual(stats['rows'],2)
        self.assertEqual(stats['all_offsets_2048_aligned'],2)
        self.assertEqual(stats['sizes_equal_compressed'],2)
        self.assertEqual(identities,{2400:'X0',2600:'Z0'})

    def test_invalid_stride(self):
        with self.assertRaisesRegex(ValueError,'92-byte'):
            parse_sections(row()+b'x',10000)

    def test_empty_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'nonempty'):
            parse_sections(b'',10000)

    def test_invalid_stream_size(self):
        with self.assertRaisesRegex(ValueError,'stream size'):
            parse_sections(row(),0)

    def test_duplicate_section(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            parse_sections(row()+row(b'Z0',2400,4096),10000)

    def test_nonascii_name(self):
        with self.assertRaisesRegex(ValueError,'Unprintable'):
            parse_sections(row(b'\xff'),10000)

    def test_outside_stream(self):
        with self.assertRaisesRegex(ValueError,'outside stream'):
            parse_sections(row(offset=8192,size=4096),10000)

    def test_overlap(self):
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            parse_sections(row(size=5000)+row(b'Z0',2600,4096,500),10000)

    def test_non_matching_candidate_fields_are_reported(self):
        _,s=parse_sections(row(compressed=32,status=2,filetype=8),10000)
        self.assertEqual((s['sizes_equal_compressed'],s['status_zero'],s['filetype_one']), (0,0,0))

    def test_compare_section_names(self):
        self.assertEqual(compare_section_ids({1:'A',2:'B'},{1:'A',2:'C',3:'D'}),
                         {'shared_section_numbers':2,'matching_names_at_shared_numbers':1,
                          'conflicting_names_at_shared_numbers':1})

    def test_find_single_chunk(self):
        data=chunk(0x34112,b'')+chunk(0x34110,row())+chunk(0x34111,b'abcdefgh')
        self.assertEqual(find_chunk(data),row())

    def test_find_missing_or_duplicate(self):
        with self.assertRaisesRegex(ValueError,'exactly one'):
            find_chunk(chunk(0x34112))
        with self.assertRaisesRegex(ValueError,'exactly one'):
            find_chunk(chunk(0x34110,row())*2)

    def test_find_truncated_chunk(self):
        with self.assertRaisesRegex(ValueError,'exceeds file'):
            find_chunk(struct.pack('<II',0x34110,300)+b'abc')


if __name__=='__main__':
    unittest.main()
