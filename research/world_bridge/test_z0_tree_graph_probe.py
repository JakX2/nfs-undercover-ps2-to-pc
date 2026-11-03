"""Synthetic-only checks for Z0 tree graph structural interpretation."""
import struct
import unittest
from z0_tree_graph_probe import (parse_tree_nodes, parse_fixed_chunks,
                                scene_children, inspect_scene, SCENE_CHILDREN,
                                SCENE_ROOT, FILLER_WORD, INSTANCE_CHUNK,
                                INFO_CHUNK, EXTRA_CHUNK, TREE_CHUNK,
                                UNKNOWN_CHUNK)


def node(codes=(), bb_min=(-2.,-3.,-4.), bb_max=(5.,6.,7.)):
    assert len(codes) <= 10
    return (struct.pack('<3fI3f', *bb_min, len(codes), *bb_max)
            + struct.pack('<10h', *(tuple(codes)+(0,)*(10-len(codes)))))


def children(instances=2, infos=2, nodes=None, filler=False, aux_count=None, unknown=None):
    if nodes is None: nodes = [node((0,1))]
    return {
        0x34101: bytes(68),
        INSTANCE_CHUNK: FILLER_WORD+bytes(96*instances),
        INFO_CHUNK: bytes(72*infos),
        EXTRA_CHUNK: bytes(32*(instances if aux_count is None else aux_count)),
        TREE_CHUNK: (FILLER_WORD*2 if filler else b'') + b''.join(nodes),
        UNKNOWN_CHUNK: bytes(128) if unknown is None else unknown,
    }


def root(contents=None):
    if contents is None: contents=children()
    raw=b''.join(struct.pack('<II', i, len(contents[i]))+contents[i] for i in SCENE_CHILDREN)
    return struct.pack('<II', SCENE_ROOT,len(raw))+raw


class Z0TreeGraphTests(unittest.TestCase):
    def test_simple_z0(self):
        r=inspect_scene(root())
        self.assertEqual((r['scenery_instances'],r['scenery_infos'],r['nodes'],r['instance_references']),(2,2,1,2))
        self.assertTrue(r['unknown_0x34107_all_zero'])

    def test_eight_byte_filler(self):
        r=inspect_scene(root(children(filler=True)))
        self.assertEqual(r['prefix_filler_bytes'],8)

    def test_three_node_tree_and_negative_references(self):
        n=[node((0,-1)),node((1,-2)),node((2,))]
        r=inspect_scene(root(children(instances=3,nodes=n)))
        self.assertEqual((r['nodes'],r['nested_node_references'],r['instance_references']),(3,2,3))

    def test_nonempty_unknown_is_not_dropped(self):
        r=inspect_scene(root(children(unknown=b'X'*128)))
        self.assertFalse(r['unknown_0x34107_all_zero'])

    def test_invalid_tree_stride(self):
        with self.assertRaisesRegex(ValueError,'48-byte'):
            parse_tree_nodes(node((0,1))+b'x',2)

    def test_invalid_tree_prefix(self):
        with self.assertRaisesRegex(ValueError,'tree prefix'):
            parse_tree_nodes(b'notfill!'+node((0,1)),2)

    def test_bad_instance_prefix(self):
        c=children();c[INSTANCE_CHUNK]=b'xxxx'+c[INSTANCE_CHUNK][4:]
        with self.assertRaisesRegex(ValueError,'instance stride/prefix'):
            parse_fixed_chunks(c)

    def test_bad_instance_stride(self):
        c=children();c[INSTANCE_CHUNK]+=b'x'
        with self.assertRaisesRegex(ValueError,'instance stride/prefix'):
            parse_fixed_chunks(c)

    def test_bad_info_stride(self):
        c=children();c[INFO_CHUNK]+=b'x'
        with self.assertRaisesRegex(ValueError,'information stride'):
            parse_fixed_chunks(c)

    def test_auxiliary_count_mismatch(self):
        c=children(aux_count=1)
        with self.assertRaisesRegex(ValueError,'instance record count'):
            parse_fixed_chunks(c)

    def test_instance_child_outside_count(self):
        with self.assertRaisesRegex(ValueError,'instance child index'):
            parse_tree_nodes(node((0,2)),2)

    def test_negative_node_link_outside_count(self):
        with self.assertRaisesRegex(ValueError,'nested tree child index'):
            parse_tree_nodes(node((-1,)),2)

    def test_self_referential_tree_node(self):
        with self.assertRaisesRegex(ValueError,'nested tree child index'):
            parse_tree_nodes(node((-1,))+node((-1,)),0)

    def test_cycle_in_graph(self):
        n=[node((-1,)),node((-2,)),node((-1,))]
        with self.assertRaisesRegex(ValueError,'Cycle'):
            parse_tree_nodes(b''.join(n),0)

    def test_unreachable_node(self):
        with self.assertRaisesRegex(ValueError,'unreachable'):
            parse_tree_nodes(node((0,))+node((1,)),2)

    def test_duplicate_leaf_instance_reference(self):
        with self.assertRaisesRegex(ValueError,'exactly once'):
            parse_tree_nodes(node((0,0)),2)

    def test_missing_leaf_instance_reference(self):
        with self.assertRaisesRegex(ValueError,'exactly once'):
            parse_tree_nodes(node((0,)),2)

    def test_dag_double_reference_to_one_node(self):
        nodes=[node((-1,-1)), node((-2,)), node((0,))]
        with self.assertRaisesRegex(ValueError,'strict tree'):
            parse_tree_nodes(b''.join(nodes),1)

    def test_nonzero_unused_child(self):
        b=bytearray(node((0,)))
        struct.pack_into('<h',b,28+2,3)
        with self.assertRaisesRegex(ValueError,'unused'):
            parse_tree_nodes(bytes(b),2)

    def test_nonfinite_bounds(self):
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            parse_tree_nodes(node((0,),bb_min=(float('nan'),0,0)),2)

    def test_inverted_bounds(self):
        with self.assertRaisesRegex(ValueError,'Inverted'):
            parse_tree_nodes(node((0,),bb_min=(10,0,0)),2)

    def test_too_many_children(self):
        b=bytearray(node((0,)))
        struct.pack_into('<I',b,12,11)
        with self.assertRaisesRegex(ValueError,'Too many'):
            parse_tree_nodes(bytes(b),2)

    def test_invalid_root_id(self):
        b=bytearray(root())
        struct.pack_into('<I',b,0,123)
        with self.assertRaisesRegex(ValueError,'Missing scenery root'):
            scene_children(bytes(b))

    def test_invalid_root_length(self):
        b=bytearray(root())
        struct.pack_into('<I',b,4,9999)
        with self.assertRaisesRegex(ValueError,'Truncated or oversized'):
            scene_children(bytes(b))

    def test_bad_scene_child_order(self):
        c=children();l=list(SCENE_CHILDREN)
        l[0],l[1]=l[1],l[0]
        data=b''.join(struct.pack('<II',i,len(c[i]))+c[i] for i in l)
        with self.assertRaisesRegex(ValueError,'child order'):
            scene_children(struct.pack('<II',SCENE_ROOT,len(data))+data)

    def test_duplicate_child(self):
        c=children();pairs=[(i,c[i]) for i in SCENE_CHILDREN]
        pairs[1]=pairs[0]
        data=b''.join(struct.pack('<II',i,len(b))+b for i,b in pairs)
        with self.assertRaisesRegex(ValueError,'duplicated'):
            scene_children(struct.pack('<II',SCENE_ROOT,len(data))+data)

    def test_truncated_child(self):
        c=children();data=b''.join(struct.pack('<II',i,len(c[i]))+c[i] for i in SCENE_CHILDREN)
        d=bytearray(struct.pack('<II',SCENE_ROOT,len(data))+data)
        struct.pack_into('<I',d,8+4,0xffffffff)
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            scene_children(bytes(d))


if __name__=='__main__':unittest.main()
