#!/usr/bin/env python3
"""Source-free spatial hierarchy and DXT5 smoke-slot regression controls."""
import math
import struct
import unittest

from carbon_pc_dxt5_spatial_smoke_target import (
    _bounds, _inside, _clusters, instance_bounds, validate_tree_bounds,
    spatial_slot_profile,)


def inst(boxes):
    data = bytearray(b'\x11'*4)
    for lo, hi in boxes:
        row=bytearray(96)
        struct.pack_into('<3f',row,0,*lo)
        struct.pack_into('<3f',row,16,*hi)
        data+=row
    return bytes(data)


def tree(nodes, padding=False):
    data=bytearray(b'\x11'*8 if padding else b'')
    for lo,hi,refs in nodes:
        row=bytearray(48)
        struct.pack_into('<3f',row,0,*lo)
        struct.pack_into('<I',row,12,len(refs))
        struct.pack_into('<3f',row,16,*hi)
        struct.pack_into('<10h',row,28,*(list(refs)+[0]*(10-len(refs))))
        data+=row
    return bytes(data)


def fixture():
    boxes = [((1,1,1),(2,2,2)), ((2,2,2),(3,3,3)),
             ((40,1,1),(41,2,2)), ((42,1,1),(43,2,2))]
    # Root encompasses both groups. Child 1 has first two. Child 2 last two.
    nodes=[((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(0,1)),
           ((35,0,0),(50,10,10),(2,3))]
    return boxes,inst(boxes),tree(nodes)


def args():
    boxes, instances, nodes=fixture()
    tex={10:{'codec':34,'width':64,'height':32},
         20:{'codec':38,'width':128,'height':64},
         30:{'codec':38,'width':64,'height':32}}
    profiles=[(101,{'texture_table':(20,30),'per_texture':{0:12,1:3}}),
              (102,{'texture_table':(20,), 'per_texture':{0:7}}),
              (103,{'texture_table':(30,), 'per_texture':{0:10}})]
    prim=[101,102,101,102]
    return tex,profiles,prim,instances,nodes


class BoundsTests(unittest.TestCase):
    def test_instance_count(self):
        self.assertEqual(len(instance_bounds(fixture()[1])),4)

    def test_bound_values(self):
        self.assertEqual(instance_bounds(fixture()[1])[0],((1.,1.,1.),(2.,2.,2.)))

    def test_inverted_axis(self):
        with self.assertRaises(ValueError):_bounds((2,0,0),(1,1,1))

    def test_nonfinite_nan(self):
        with self.assertRaises(ValueError):_bounds((float('nan'),0,0),(1,1,1))

    def test_nonfinite_infinity(self):
        with self.assertRaises(ValueError):_bounds((0,0,0),(float('inf'),1,1))

    def test_extreme_coordinate(self):
        with self.assertRaises(ValueError):_bounds((0,0,0),(10000001,1,1))

    def test_zero_extent_is_supported(self):
        self.assertEqual(_bounds((1,1,1),(1,1,1))[0],(1,1,1))

    def test_inside_epsilon(self):
        self.assertTrue(_inside(((0,0,0),(10,10,10)),((-.0004,1,1),(10.0004,2,2))))

    def test_outside_epsilon(self):
        self.assertFalse(_inside(((0,0,0),(10,10,10)),((-.1,1,1),(2,2,2))))

    def test_instance_wrong_prefix(self):
        b=bytearray(fixture()[1]);b[0]=0
        with self.assertRaises(ValueError):instance_bounds(bytes(b))

    def test_instance_wrong_stride(self):
        with self.assertRaises(ValueError):instance_bounds(fixture()[1]+b'\x00')

    def test_empty_instances(self):
        with self.assertRaises(ValueError):instance_bounds(b'\x11'*4)

    def test_instance_nan(self):
        b=bytearray(fixture()[1]);struct.pack_into('<f',b,4,float('nan'))
        with self.assertRaises(ValueError):instance_bounds(bytes(b))

    def test_instance_inversion(self):
        b=bytearray(fixture()[1]);struct.pack_into('<f',b,4,4.0)
        with self.assertRaises(ValueError):instance_bounds(bytes(b))


class TreeTests(unittest.TestCase):
    def test_valid_nested_tree(self):
        bounds,_,blob=fixture()
        self.assertEqual(validate_tree_bounds(blob,bounds)['validated_instance_leaf_AABBs'],4)

    def test_node_count(self):
        bounds,_,blob=fixture()
        self.assertEqual(validate_tree_bounds(blob,bounds)['tree_nodes'],3)

    def test_valid_eight_byte_prefix(self):
        boxes,_,_=fixture();nodes=[((0,0,0),(50,10,10),(-1,-2)),
                                   ((0,0,0),(10,10,10),(0,1)),
                                   ((35,0,0),(50,10,10),(2,3))]
        self.assertEqual(validate_tree_bounds(tree(nodes,padding=True),boxes)['tree_nodes'],3)

    def test_wrong_tree_padding(self):
        boxes,_,blob=fixture()
        with self.assertRaises(ValueError):validate_tree_bounds(b'\x00'*8+blob,boxes)

    def test_wrong_tree_stride(self):
        boxes,_,blob=fixture()
        with self.assertRaises(ValueError):validate_tree_bounds(blob+b'\x00',boxes)

    def test_truncated_node(self):
        boxes,_,blob=fixture()
        with self.assertRaises(ValueError):validate_tree_bounds(blob[:-5],boxes)

    def test_missing_leaf(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(0,1)),((35,0,0),(50,10,10),(2,))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_duplicate_leaf(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(0,1)),((35,0,0),(50,10,10),(2,2))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_leaf_outside_parent(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(1.5,10,10),(0,1)),((35,0,0),(50,10,10),(2,3))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_child_outside_parent(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(49,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(0,1)),((35,0,0),(50,10,10),(2,3))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_node_invalid_index(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-4)),
           ((0,0,0),(10,10,10),(0,1)),((35,0,0),(50,10,10),(2,3))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_node_self_reference(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(-1,1)),((35,0,0),(50,10,10),(2,3))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)

    def test_too_many_children(self):
        boxes,_,blob=fixture();bad=bytearray(blob);struct.pack_into('<I',bad,12,11)
        with self.assertRaises(ValueError):validate_tree_bounds(bytes(bad),boxes)

    def test_bad_unused_child_slot(self):
        boxes,_,blob=fixture();bad=bytearray(blob);struct.pack_into('<h',bad,28+2*2,1)
        with self.assertRaises(ValueError):validate_tree_bounds(bytes(bad),boxes)

    def test_tree_empty(self):
        with self.assertRaises(ValueError):validate_tree_bounds(b'',fixture()[0])

    def test_tree_zero_leaf(self):
        with self.assertRaises(ValueError):validate_tree_bounds(fixture()[2],[])

    def test_tree_out_of_range_leaf(self):
        boxes,_,_=fixture();bad=tree([((0,0,0),(50,10,10),(-1,-2)),
           ((0,0,0),(10,10,10),(0,1)),((35,0,0),(50,10,10),(2,9))])
        with self.assertRaises(ValueError):validate_tree_bounds(bad,boxes)


class ClustersTests(unittest.TestCase):
    def test_two_groups(self):
        points=[(1,1,1),(2,2,2),(40,1,1),(42,1,1)]
        self.assertEqual([len(x) for x in _clusters(points,12)], [2,2])

    def test_order_stable(self):
        self.assertEqual(_clusters([(20,0,0),(0,0,0),(21,0,0),(1,0,0)],5),[(0,2),(1,3)])

    def test_single_group(self):
        self.assertEqual(_clusters([(0,0,0),(1,0,0),(2,0,0)],1),[(0,1,2)])

    def test_boundary_equal(self):
        self.assertEqual(len(_clusters([(0,0,0),(3,4,0)],5)),1)

    def test_invalid_zero_distance(self):
        with self.assertRaises(ValueError):_clusters([(0,0,0)],0)

    def test_invalid_nan_distance(self):
        with self.assertRaises(ValueError):_clusters([(0,0,0)],float('nan'))

    def test_invalid_bool_distance(self):
        with self.assertRaises(ValueError):_clusters([(0,0,0)],True)

    def test_no_points(self):
        with self.assertRaises(ValueError):_clusters([],12)


class SlotTests(unittest.TestCase):
    def run_profile(self,**kwargs):
        return spatial_slot_profile(*args(), **({'slot': 0} | kwargs))

    def test_valid_slot(self):
        d=self.run_profile()
        self.assertEqual(d['pc_dxt5_slot'],0)
        self.assertEqual(d['source_primary_scenery_instances'],4)
        self.assertEqual(d['source_material_models'],2)
        self.assertEqual(d['source_material_triangles'],19)
        self.assertEqual(d['proximity_cluster_sizes'],[2,2])
        self.assertEqual(d['candidate_world_AABB_extent_xyz'],[42,2,2])
        self.assertTrue(d['all_spatial_tree_bounds_contain_children'])

    def test_other_slot(self):
        self.assertEqual(self.run_profile(slot=1)['source_primary_scenery_instances'],2)

    def test_dxt1_not_a_dxt5_slot(self):
        with self.assertRaises(ValueError):self.run_profile(slot=2)

    def test_invalid_negative_slot(self):
        with self.assertRaises(ValueError):self.run_profile(slot=-1)

    def test_invalid_section(self):
        with self.assertRaises(ValueError):self.run_profile(section=1)

    def test_missing_primary_link(self):
        tex,profiles,prim,insts,nodes=args();prim[0]=0
        with self.assertRaises(ValueError):spatial_slot_profile(tex,profiles,prim,insts,nodes)

    def test_missing_instances(self):
        tex,profiles,prim,insts,nodes=args()
        with self.assertRaises(ValueError):spatial_slot_profile(tex,profiles,[],insts,nodes)

    def test_missing_primary_material(self):
        tex,profiles,prim,insts,nodes=args()
        with self.assertRaises(ValueError):spatial_slot_profile(tex,[],prim,insts,nodes)

    def test_material_invalid_index(self):
        tex,profiles,prim,insts,nodes=args();profiles[0][1]['per_texture']={3:12}
        with self.assertRaises(ValueError):spatial_slot_profile(tex,profiles,prim,insts,nodes)

    def test_material_invalid_triangles(self):
        tex,profiles,prim,insts,nodes=args();profiles[0][1]['per_texture']={0:0}
        with self.assertRaises(ValueError):spatial_slot_profile(tex,profiles,prim,insts,nodes)

    def test_target_not_referenced(self):
        tex,profiles,prim,insts,nodes=args();prim[:]=[999]*4
        with self.assertRaises(ValueError):spatial_slot_profile(tex,profiles,prim,insts,nodes)

    def test_repeated_material_identity_not_multiple_instances(self):
        tex,profiles,prim,insts,nodes=args();profiles.append((101,{'texture_table':(20,), 'per_texture':{0:12}}))
        res=spatial_slot_profile(tex,profiles,prim,insts,nodes,slot=0)
        self.assertEqual(res['source_primary_scenery_instances'],4)
        self.assertEqual(res['source_material_models'],2)

    def test_bad_distance(self):
        with self.assertRaises(ValueError):self.run_profile(cluster_distance=float('inf'))

    def test_aggregate_no_source_hashes(self):
        d=self.run_profile()
        self.assertNotIn('texture_hash',d)
        self.assertNotIn('model_hashes',d)
        self.assertNotIn('positions',d)
        self.assertEqual(d['verdict'],'OFFLINE_SPATIAL_SOURCE_JOIN_NOT_DRIVE_LOCATION_OR_RUNTIME_VISIBILITY')


if __name__=='__main__':unittest.main()
