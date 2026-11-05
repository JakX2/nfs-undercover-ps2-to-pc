"""Synthetic-only tests of variable-length visibility records and graph guards."""
import struct
import unittest
from visibility_edge_bridge import (parse_boundaries, parse_drivable_sections,
                                    visibility_children, summarize)
from scenery_visibility_anchor import VISIBILITY_ROOT, VISIBILITY_CHILDREN


def boundary(section=101, count=4):
    b=bytearray(48+8*count)
    struct.pack_into('<hB',b,8,section,count)
    for k in range(6+2*count):
        struct.pack_into('<f',b,12+4*k,42.0)
    return bytes(b)


def drivable(section=101, refs=(101,201), capacity=4, most=2):
    b=bytearray(20+2*capacity)
    struct.pack_into('<hBBh',b,12,section,most,capacity,len(refs))
    for i,r in enumerate(refs):struct.pack_into('<h',b,18+2*i,r)
    return bytes(b)


def root(children=None):
    if children is None:
        children={cid:bytes(8) for cid in VISIBILITY_CHILDREN}
        children[0x34152]=boundary()
        children[0x34153]=drivable()
    body=b''.join(struct.pack('<II',cid,len(children[cid]))+children[cid]
                  for cid in VISIBILITY_CHILDREN)
    return struct.pack('<II',VISIBILITY_ROOT,len(body))+body


def bundle(chunk):return chunk


class VisibilityRecordsTests(unittest.TestCase):
    def test_boundary_rows(self):
        r=parse_boundaries(boundary(101,4)+boundary(102,7))
        self.assertEqual(r,{101:4,102:7})

    def test_drivable_rows(self):
        r=parse_drivable_sections(drivable(101,(101,2501))+drivable(102,(102,),5))
        self.assertEqual(r[101]['refs'],(101,2501))
        self.assertEqual(r[102]['capacity'],5)

    def test_undercover_capacity_above_mw_72(self):
        a=parse_drivable_sections(drivable(101,tuple(range(101,179)),84,72))
        self.assertEqual(len(a[101]['refs']),78)

    def test_truncated_boundary(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):
            parse_boundaries(bytes(20))

    def test_oversized_boundary_point_count(self):
        with self.assertRaisesRegex(ValueError,'boundary section or point'):
            parse_boundaries(boundary(101,17))

    def test_boundary_duplicate(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            parse_boundaries(boundary()+boundary())

    def test_boundary_nan(self):
        b=bytearray(boundary());struct.pack_into('<f',b,12,float('nan'))
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            parse_boundaries(bytes(b))

    def test_boundary_out_of_bounds(self):
        with self.assertRaisesRegex(ValueError,'exceeds chunk'):
            parse_boundaries(boundary()[:-1])

    def test_drivable_invalid_capacity(self):
        b=bytearray(drivable());b[15]=129
        with self.assertRaisesRegex(ValueError,'counts'):
            parse_drivable_sections(bytes(b))

    def test_drivable_too_many_refs(self):
        b=bytearray(drivable());struct.pack_into('<h',b,16,5)
        with self.assertRaisesRegex(ValueError,'counts'):
            parse_drivable_sections(bytes(b))

    def test_drivable_negative_reference(self):
        b=drivable(101,(-1,))
        with self.assertRaisesRegex(ValueError,'Invalid or repeated'):
            parse_drivable_sections(b)

    def test_drivable_duplicate_reference(self):
        with self.assertRaisesRegex(ValueError,'Invalid or repeated'):
            parse_drivable_sections(drivable(101,(101,101)))

    def test_duplicate_drivable_section(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            parse_drivable_sections(drivable()+drivable())

    def test_incomplete_drivable(self):
        with self.assertRaisesRegex(ValueError,'exceeds chunk'):
            parse_drivable_sections(drivable()[:-1])

    def test_child_order(self):
        c=visibility_children(bundle(root()))
        self.assertEqual(tuple(c),VISIBILITY_CHILDREN)
        s=summarize(c)
        self.assertEqual((s['boundary_sections'],s['drivable_sections'],s['visibility_references']), (1,1,2))

    def test_duplicate_visibility_child(self):
        c={cid:bytes(8) for cid in VISIBILITY_CHILDREN}
        arr=list(VISIBILITY_CHILDREN);arr[1]=arr[0]
        body=b''.join(struct.pack('<II',cid,len(c[cid]))+c[cid] for cid in arr)
        with self.assertRaisesRegex(ValueError,'duplicate visibility child'):
            visibility_children(bundle(struct.pack('<II',VISIBILITY_ROOT,len(body))+body))

    def test_truncated_visibility_root(self):
        with self.assertRaisesRegex(ValueError,'out of bounds'):
            visibility_children(bundle(root()[:-1]))


if __name__=='__main__':unittest.main()
