"""Synthetic-only texture-pack index and source-reference tests."""
import struct
import unittest
from texture_pack_index_probe import (TEXTURE_ROOT, DESCRIPTOR_ROOT,
    PIXEL_ROOT, HASH_TABLE, children, parse_section_index,
    summarize_index, compare_platform_indexes)


def chunk(tag, payload):
    return struct.pack('<II', tag, len(payload)) + payload


def fixture(hashes=(11,22), pointers=None, pixel=b'SYNTHETIC', swap=False):
    pointers = (0,)*len(hashes) if pointers is None else pointers
    table = b''.join(struct.pack('<II', h, p) for h, p in zip(hashes, pointers))
    desc = [(0x33310001,b'LABEL'),(HASH_TABLE,table),
            (0x33310004,b'METADATA'),(0x33310005,b'FORMAT')]
    if swap:
        desc[1], desc[2] = desc[2], desc[1]
    descriptor = b''.join(chunk(k, v) for k,v in desc)
    root = b''.join(chunk(k,v) for k,v in
                    ((0,bytes(48)),(DESCRIPTOR_ROOT,descriptor),(0,bytes(24)),(PIXEL_ROOT,pixel)))
    return chunk(TEXTURE_ROOT,root) + bytes(32)


class TexturePackTests(unittest.TestCase):
    def test_valid_index(self):
        self.assertEqual(parse_section_index(fixture()), frozenset((11,22)))

    def test_attached_opaque_bytes_not_parsed(self):
        self.assertEqual(parse_section_index(fixture()+b'after'), frozenset((11,22)))

    def test_two_level_children(self):
        f = fixture()
        size = struct.unpack_from('<I',f,4)[0]
        self.assertEqual([x for x,_ in children(f[8:8+size])],
                         [0,DESCRIPTOR_ROOT,0,PIXEL_ROOT])

    def test_reject_invalid_pointer(self):
        with self.assertRaisesRegex(ValueError,'pointer'):
            parse_section_index(fixture(pointers=(0,1234)))

    def test_reject_repeated_hash(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            parse_section_index(fixture(hashes=(11,11)))

    def test_reject_unsorted_hashes(self):
        with self.assertRaisesRegex(ValueError,'unordered'):
            parse_section_index(fixture(hashes=(22,11)))

    def test_reject_zero_hash(self):
        with self.assertRaisesRegex(ValueError,'zero'):
            parse_section_index(fixture(hashes=(0,22)))

    def test_reject_descriptor_wrong_order(self):
        with self.assertRaisesRegex(ValueError,'descriptor child order'):
            parse_section_index(fixture(swap=True))

    def test_reject_empty_pixel_resource(self):
        with self.assertRaisesRegex(ValueError,'Empty serialized'):
            parse_section_index(fixture(pixel=b''))

    def test_reject_unanchored_root(self):
        with self.assertRaisesRegex(ValueError,'section-start'):
            parse_section_index(bytes(4)+fixture())

    def test_reject_truncated_parent(self):
        b = bytearray(fixture())
        struct.pack_into('<I',b,4,len(b)+50)
        with self.assertRaisesRegex(ValueError,'complete'):
            parse_section_index(bytes(b))

    def test_reject_child_exceeding_parent(self):
        with self.assertRaisesRegex(ValueError,'exceeds parent'):
            children(struct.pack('<II', 42,99))

    def test_reject_truncated_child_header(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):
            children(b'xyz')

    def test_index_coverage_reports_missing_vs_unused(self):
        v = summarize_index(frozenset((11,33)),[(11,22),(11,)])
        self.assertEqual(v['referenced_in_local_index'],1)
        self.assertEqual(v['referenced_outside_local_index'],1)
        self.assertEqual(v['indexed_but_not_referenced_by_local_solids'],1)
        self.assertEqual(v['solid_texture_reference_occurrences'],3)

    def test_repeated_solid_table_occurrences_preserved(self):
        v = summarize_index(frozenset((11,22)),[(11,),(11,22)])
        self.assertEqual(v['solid_occurrences'],2)
        self.assertEqual(v['solid_texture_reference_occurrences'],3)

    def test_identical_source_different_index_coverage(self):
        r = compare_platform_indexes(frozenset((11,22)),frozenset((11,)),
                                     [(11,22)],[(11,22)])
        self.assertEqual(r['pc_only_index_hashes'],1)
        self.assertTrue(r['ps2_index_is_subset_of_pc'])

    def test_different_source_tables_rejected(self):
        with self.assertRaisesRegex(ValueError,'not identical'):
            compare_platform_indexes(frozenset((11,)),frozenset((22,)),
                                     [(11,)],[(22,)])

    def test_empty_tables_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing verified'):
            summarize_index(frozenset((11,)),[])


if __name__ == '__main__':
    unittest.main()
