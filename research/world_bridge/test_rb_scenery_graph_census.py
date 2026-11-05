"""Synthetic-only tests for bounded RB scenery-graph census."""
import struct
import unittest
from rb_scenery_graph_census import scan_stream, compare, summarize, STREAM_LIMIT
from section_identity_anchor import parse_rows
from test_section_identity_anchor import row
from test_z0_tree_graph_probe import root, children


def scene_at(offset=128, length=4096, number=141, name=b'A41', one_root=True):
    r=root()
    data=bytearray(length)
    if one_root:
        data[offset:offset+len(r)] = r
    index=parse_rows(row(name=name,section=number,offset=0,size=length),len(data))
    return bytes(data), index


class RBCensusTests(unittest.TestCase):
    def test_embedded_scene(self):
        data,index=scene_at()
        out,ignored=scan_stream(data,index)
        self.assertEqual(len(out),1)
        self.assertFalse(out[141]['at_section_start'])
        self.assertEqual(ignored,0)
        self.assertEqual(summarize(out,index,ignored)['tree_nodes'],1)

    def test_scene_at_section_start(self):
        data,index=scene_at(offset=0)
        out,_=scan_stream(data,index)
        self.assertTrue(out[141]['at_section_start'])

    def test_no_scenes(self):
        data,index=scene_at(one_root=False)
        out,ignored=scan_stream(data,index)
        self.assertEqual((len(out),ignored),(0,0))

    def test_rejected_fake_signature(self):
        data,index=scene_at(one_root=False)
        buf=bytearray(data);struct.pack_into('<II',buf,16,0x80034100,0xffffffff)
        out,ignored=scan_stream(bytes(buf),index)
        self.assertEqual((len(out),ignored),(0,1))

    def test_reject_scene_outside_row(self):
        data,index=scene_at(offset=128)
        ix=parse_rows(row(section=141,offset=2048,size=2048),len(data))
        with self.assertRaisesRegex(ValueError,'outside any stream section'):
            scan_stream(data,ix)

    def test_reject_crossing_section_boundary(self):
        data,index=scene_at(offset=3900)
        with self.assertRaisesRegex(ValueError,'crosses its stream section'):
            scan_stream(data,index)

    def test_reject_duplicate_scene_in_one_section(self):
        data,index=scene_at(offset=128)
        buf=bytearray(data)
        scene=root();buf[2048:2048+len(scene)]=scene
        with self.assertRaisesRegex(ValueError,'Multiple scenery roots'):
            scan_stream(bytes(buf),index)

    def test_two_sections(self):
        r=root();buf=bytearray(8192)
        buf[128:128+len(r)]=r
        buf[4096:4096+len(r)]=r
        ix=parse_rows(row(name=b'A',section=141,offset=0,size=4096)+row(name=b'B',section=142,offset=4096,size=4096),len(buf))
        out,ignored=scan_stream(bytes(buf),ix)
        self.assertEqual((len(out),ignored),(2,0))
        self.assertEqual(summarize(out,ix,ignored)['scenery_instances'],4)

    def test_compare_same(self):
        data,ix=scene_at()
        roots,_=scan_stream(data,ix)
        got=compare(roots,roots)
        self.assertEqual(got['shared_root_section_ids'],1)
        self.assertEqual(got['matching_tree_bytes'],1)
        self.assertEqual(got['matching_instance_bytes'],1)

    def test_compare_one_missing(self):
        data,ix=scene_at()
        roots,_=scan_stream(data,ix)
        got=compare(roots,{})
        self.assertEqual((got['only_left'],got['only_right'],got['shared_root_section_ids']),(1,0,0))

    def test_compare_mutated_tree(self):
        data,ix=scene_at()
        a,_=scan_stream(data,ix)
        b={141:dict(a[141])}
        b[141]['children']=dict(a[141]['children'])
        b[141]['children'][0x34105]=b'X' + b[141]['children'][0x34105][1:]
        got=compare(a,b)
        self.assertEqual(got['matching_tree_bytes'],0)
        self.assertEqual(got['matching_instance_bytes'],1)

    def test_bounded_large_input(self):
        with self.assertRaisesRegex(ValueError,'exceeds inspection bound'):
            scan_stream(bytes(STREAM_LIMIT+1),{})

    def test_broken_parseable_tree_is_failure(self):
        r=bytearray(root())
        # Change the last tree child's instance index (tree slot 2) from 1 to 999.
        identifier=struct.pack('<I',0x34105)
        ix=r.find(identifier)
        self.assertGreater(ix,0)
        struct.pack_into('<h',r,ix+8+28+2,999)
        data=bytes(r)+bytes(4096-len(r))
        ix=parse_rows(row(section=141,size=4096),len(data))
        with self.assertRaisesRegex(ValueError,'instance child index'):
            scan_stream(data,ix)

    def test_nonzero_unknown_byte_not_assumed_empty(self):
        r=root(children(unknown=b'X'*128))
        stream=r+bytes(4096-len(r))
        ix=parse_rows(row(section=141,size=4096),len(stream))
        a,_=scan_stream(stream,ix)
        self.assertFalse(summarize(a,ix,0)['all_unknown_0x34107_zero'])


if __name__=='__main__':unittest.main()
