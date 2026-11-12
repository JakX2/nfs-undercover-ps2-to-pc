"""Source-free tests for PC DXT5 slot material and scenery prioritization."""
import unittest
from collections import Counter
from unittest.mock import patch

from carbon_pc_dxt5_material_target_rank import (
    validate_profiles, validate_links, rank_material_targets,
    source_material_profiles, source_scenery_links)


def records():
    return {
        10: {'codec': 38, 'width': 128, 'height': 64, 'mip_levels': 4},
        20: {'codec': 34, 'width': 256, 'height': 256, 'mip_levels': 6},
        30: {'codec': 38, 'width': 256, 'height': 256, 'mip_levels': 6},
        40: {'codec': 38, 'width': 512, 'height': 512, 'mip_levels': 7},
    }


def profiles():
    return [
        (100, {'texture_table': (10, 20), 'per_texture': Counter({0: 12, 1: 3})}),
        (200, {'texture_table': (30, 10), 'per_texture': Counter({0: 80, 1: 20})}),
        (300, {'texture_table': (10, 30000000), 'per_texture': Counter({0: 20, 1: 10})}),
    ]


def links():
    return [(100, (100, 100, 100, 0)), (100, (100, 100, 0, 0)),
            (200, (200, 200, 200, 200)), (300, (300, 300, 0, 0)),
            (400, (400, 100, 200, 0))]


class ValidateProfilesTests(unittest.TestCase):
    def test_ordinary(self):
        self.assertEqual(len(validate_profiles(profiles())), 3)

    def test_repeated_model_occurrences_preserved(self):
        xs = [profiles()[0], profiles()[0]]
        self.assertEqual(len(validate_profiles(xs)), 2)

    def test_duplicate_table_hash_entries_preserved(self):
        x = [(1, {'texture_table': (10, 10), 'per_texture': {0: 3, 1: 4}})]
        self.assertEqual(validate_profiles(x)[0][1], (10, 10))

    def test_missing_profiles(self):
        with self.assertRaisesRegex(ValueError, 'Missing'):
            validate_profiles([])

    def test_boolean_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            validate_profiles([(True, profiles()[0][1])])

    def test_zero_model_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(0, profiles()[0][1])])

    def test_malformed_entry_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, 2, 3)])

    def test_bad_empty_table_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, {'texture_table': (), 'per_texture': {0: 4}})])

    def test_invalid_texture_hash_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, {'texture_table': (0,), 'per_texture': {0: 4}})])

    def test_unindexed_per_material_slot_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, {'texture_table': (10,), 'per_texture': {1: 4}})])

    def test_zero_triangles_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, {'texture_table': (10,), 'per_texture': {0: 0}})])

    def test_bool_triangle_count_rejected(self):
        with self.assertRaises(ValueError):
            validate_profiles([(1, {'texture_table': (10,), 'per_texture': {0: True}})])


class ValidateInstanceTests(unittest.TestCase):
    def test_valid_links(self):
        self.assertEqual(len(validate_links(links())), 5)

    def test_duplicate_lods_collapsed(self):
        self.assertEqual(validate_links([(1, (1, 1, 1, 0))])[0][1], frozenset({1}))

    def test_no_links_rejected(self):
        with self.assertRaises(ValueError):
            validate_links([])

    def test_zero_primary_rejected(self):
        with self.assertRaises(ValueError):
            validate_links([(0, (0, 1, 0, 0))])

    def test_primary_missing_from_lod_set(self):
        with self.assertRaises(ValueError):
            validate_links([(1, (2, 2, 0, 0))])

    def test_five_lods_rejected(self):
        with self.assertRaises(ValueError):
            validate_links([(1, (1, 2, 3, 4, 5))])

    def test_bool_hash_rejected(self):
        with self.assertRaises(ValueError):
            validate_links([(1, (1, True))])

    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            validate_links([(1,)])


class RankTests(unittest.TestCase):
    def get(self, donor=None):
        return rank_material_targets(records(), profiles(), links(), donor, section_id=142)

    def test_output_never_includes_hashes(self):
        report = self.get()
        self.assertEqual([x['pc_dxt5_slot'] for x in report['ranked_targets']], [0, 1, 2])
        self.assertNotIn('30000000', str(report))
        self.assertNotIn('model_hash', str(report))

    def test_dxt5_ordinal_excludes_dxt1(self):
        self.assertEqual(self.get()['candidate_dxt5_slots'], 3)

    def test_correct_triangles(self):
        r = {x['pc_dxt5_slot']: x for x in self.get()['ranked_targets']}
        self.assertEqual(r[0]['material_triangles'], 12 + 20 + 20)
        self.assertEqual(r[1]['material_triangles'], 80)
        self.assertEqual(r[2]['material_triangles'], 0)

    def test_distinct_models_and_instances(self):
        r = {x['pc_dxt5_slot']: x for x in self.get()['ranked_targets']}
        self.assertEqual(r[0]['distinct_models'], 3)
        self.assertEqual(r[0]['primary_lod_instance_refs'], 4)
        self.assertEqual(r[0]['any_lod_instance_refs'], 5)
        self.assertEqual(r[1]['primary_lod_instance_refs'], 1)
        self.assertEqual(r[1]['any_lod_instance_refs'], 2)

    def test_zero_use_slot_still_present(self):
        r = self.get()['ranked_targets'][-1]
        self.assertEqual(r['pc_dxt5_slot'], 2)
        self.assertEqual(r['primary_lod_instance_refs'], 0)

    def test_missing_local_texture_not_proved_missing_globally(self):
        self.assertEqual(self.get()['solid_texture_hashes_outside_local_pc_index'], 1)

    def test_all_counts(self):
        r = self.get()
        self.assertEqual(r['material_backed_dxt5_slots'], 2)
        self.assertEqual(r['scene_backed_dxt5_slots'], 2)
        self.assertEqual(r['source_solid_occurrences'], 3)
        self.assertEqual(r['source_scene_instances'], 5)

    def test_donor_dimension_matching(self):
        donor={111:{'codec':4,'width':128,'height':64},
               222:{'codec':8,'width':128,'height':64},
               333:{'codec':4,'width':512,'height':512}}
        r={x['pc_dxt5_slot']:x for x in self.get(donor)['ranked_targets']}
        self.assertEqual(r[0]['dimension_compatible_donor_count'], 2)
        self.assertEqual(r[0]['dimension_compatible_donor_ordinals'], [0,1])
        self.assertEqual(r[1]['dimension_compatible_donor_count'], 0)
        self.assertEqual(r[2]['dimension_compatible_donor_count'], 1)

    def test_no_donor_keeps_unknown(self):
        self.assertIsNone(self.get()['ranked_targets'][0]['dimension_compatible_donor_count'])

    def test_repeated_model_occurrences_not_double_scene_counted(self):
        p=profiles()+[profiles()[0]]
        report=rank_material_targets(records(),p,links())
        a=report['ranked_targets'][0]
        self.assertEqual(a['primary_lod_instance_refs'],4)
        self.assertEqual(a['material_triangles'], 64)
        self.assertEqual(a['material_solid_occurrences'], 4)

    def test_duplicate_texture_slot_in_one_mesh_table(self):
        p=[(1, {'texture_table':(10,10),'per_texture':{0:9,1:11}})]
        out=rank_material_targets(records(),p,[(1,(1,1,1,0))])
        a=out['ranked_targets'][0]
        self.assertEqual(a['distinct_models'],1)
        self.assertEqual(a['material_triangles'],20)
        self.assertEqual(a['primary_lod_instance_refs'],1)

    def test_wrong_section_rejected(self):
        with self.assertRaises(ValueError):
            rank_material_targets(records(),profiles(),links(),section_id=241)

    def test_boolean_codec_rejected(self):
        r=records();r[10]['codec']=True
        with self.assertRaises(ValueError):
            rank_material_targets(r,profiles(),links())

    def test_malformed_donor_rejected(self):
        with self.assertRaises(ValueError):
            self.get({1:{'codec':10,'width':100,'height':100}})

    def test_empty_texture_index_rejected(self):
        with self.assertRaises(ValueError):
            rank_material_targets({},profiles(),links())

    def test_unreferenced_scene_hash_does_not_fake_visibility(self):
        out=rank_material_targets(records(), profiles(), [(999,(999,999,0,0))])
        self.assertEqual(out['scene_backed_dxt5_slots'],0)
        self.assertEqual(out['material_backed_dxt5_slots'],2)

    def test_primaries_and_any_lod_are_distinct(self):
        out=rank_material_targets(records(),profiles(),[(999,(999,100,200,0))])
        self.assertEqual(out['ranked_targets'][0]['primary_lod_instance_refs'],0)
        self.assertEqual(out['ranked_targets'][0]['any_lod_instance_refs'],1)

    def test_order_prefers_scene_use_over_triangle_count(self):
        r=records()
        p=[(100,{'texture_table':(10,30),'per_texture':{0:3,1:10000}})]
        out=rank_material_targets(r,p,[(100,(100,0,0,0))])
        self.assertEqual(out['ranked_targets'][0]['pc_dxt5_slot'],1)
        self.assertEqual(out['ranked_targets'][1]['pc_dxt5_slot'],0)

    def test_null_size_rejected(self):
        r=records();r[10]['width']=None
        with self.assertRaises(ValueError):
            rank_material_targets(r,profiles(),links())


# The source scanners below invoke the repository's existing parsers through
# local imports. Fake modules exercise the new orchestration only; full original
# parser invariants are tested by those modules' own regression suites.
class ScannerOrchestrationTests(unittest.TestCase):
    @staticmethod
    def chunk(cid, data):
        import struct
        return struct.pack('<II', cid, len(data)) + data

    def _fake_geom(self, hashes=(100,), valid=True):
        import sys, types, struct
        geo=types.ModuleType('geometry_hash_control')
        geo.GEOM=0x80134000;geo.SOLID_ROOT=0x80134010;geo.PLATFORM_PC=0x134900
        geo.parse_geometry_root=lambda root: ({'hashes':frozenset(hashes),'platform':geo.PLATFORM_PC}
                                             if valid else (_ for _ in ()).throw(ValueError('bad geometry')))
        def children(blob,start,end):
            while start<end:
                tag,n=struct.unpack_from('<II',blob,start)
                yield tag,blob[start+8:start+8+n]
                start+=8+n
        geo.read_chunks=children
        binding=types.ModuleType('texture_binding_control')
        binding.parse_solid_material=lambda solid, platform: (100,{'texture_table':(10,), 'per_texture':{0:12}})
        source=(struct.pack('<II', geo.GEOM, 8 + len(self.chunk(0x80134001,b'hhhh'))+
                   len(self.chunk(geo.SOLID_ROOT,b'ssss')))+ bytes(8)+
                   self.chunk(0x80134001,b'hhhh') + self.chunk(geo.SOLID_ROOT,b'ssss'))
        return {'geometry_hash_control':geo,'texture_binding_control':binding},source

    def test_geometry_scanner_accepts_one_validated_pack(self):
        import sys
        modules,source=self._fake_geom()
        with patch.dict(sys.modules,modules):
            result=source_material_profiles(b'abcde\x00\x00\x00'+source)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0][0],100)

    def test_geometry_scanner_preserves_model_occurrences_across_packs(self):
        import sys
        mods,src=self._fake_geom()
        with patch.dict(sys.modules,mods):
            result = source_material_profiles(src+src)
        self.assertEqual(len(result),2)
        self.assertEqual([x[0] for x in result], [100,100])

    def test_geometry_scanner_rejects_invalid_index(self):
        import sys
        mods,src=self._fake_geom(hashes=(200,))
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'Unindexed'):
                source_material_profiles(src)

    def test_geometry_scanner_rejects_unknown_platform(self):
        import sys
        mods,src=self._fake_geom()
        mods['geometry_hash_control'].PLATFORM_PC=0x134900
        mods['geometry_hash_control'].parse_geometry_root=lambda root: {'hashes':frozenset({100}),'platform':0x134a00}
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'platform'):
                source_material_profiles(src)

    def test_geometry_scanner_rejects_missing(self):
        import sys
        mods,_=self._fake_geom()
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'No indexed'):
                source_material_profiles(bytes(80))

    def _fake_scene(self, indexed=(0,), bad=False):
        import types,struct
        z=types.ModuleType('z0_tree_graph_probe');z.MAX_Z0_FRAME=65536
        info=bytearray(72)
        struct.pack_into('<4I',info,0x18,100,100,0,0)
        instances=b'\x11'*4+bytes(96)
        z.scene_children=lambda blob: ({0x34102:bytes(info),0x34103:instances},8)
        z.inspect_scene=lambda blob: None
        bridge=types.ModuleType('scenery_model_hash_bridge')
        bridge.parse_info_records=lambda blob: (blob,)
        bridge.validate_instance_links=lambda instances,info_blob: indexed
        payload=(struct.pack('<II',0x80034100,48)+bytes(48))
        return {'z0_tree_graph_probe':z,'scenery_model_hash_bridge':bridge},payload

    def test_scenery_scanner_gets_primary_and_lod_hashes(self):
        import sys
        mods,blob=self._fake_scene()
        with patch.dict(sys.modules,mods):
            result=source_scenery_links(blob)
        self.assertEqual(result,[(100,(100,100,0,0))])

    def test_scenery_scanner_rejects_duplicate_root(self):
        import sys
        mods,blob=self._fake_scene()
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'Ambiguous'):
                source_scenery_links(blob+blob)

    def test_scenery_scanner_rejects_missing_root(self):
        import sys
        mods,_=self._fake_scene()
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'Missing'):
                source_scenery_links(bytes(100))

    def test_scenery_scanner_rejects_zero_primary(self):
        import sys
        mods,blob=self._fake_scene()
        mods['scenery_model_hash_bridge'].parse_info_records=lambda payload:(bytes(72),)
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'primary'):
                source_scenery_links(blob)

    def test_scenery_scanner_rejects_out_of_range_link(self):
        import sys
        mods,blob=self._fake_scene(indexed=(3,))
        with patch.dict(sys.modules,mods):
            with self.assertRaisesRegex(ValueError,'info index'):
                source_scenery_links(blob)

if __name__ == '__main__':
    unittest.main()
