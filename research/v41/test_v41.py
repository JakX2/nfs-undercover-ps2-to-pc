"""Offline only, original source fixtures and independent readback assertions."""
import hashlib,struct,unittest
from pathlib import Path
from unittest.mock import patch
from carbon_pc_identity_v27 import root_parts,bin_hash,IdentityError
from carbon_pc_scenery_v19 import parse_component
from carbon_pc_bounds_v21 import inspect
from carbon_scenery_transform_v21 import locate_header
from wii_gx_v17_2 import read_model
from scenery_lod_bridge_v40 import first_instance_of_name,strict_require_complete,SceneReferenceError
from native_redbuilding_lods_v41 import (make_library,run,verify_scene_info,LODError,
         WII_SHA,DONOR_SHA,TEXTURE_HASH,modelname,sha,validate_face_attributes)

D=Path(__file__).parent
SOURCE=(D/'undercover_redbuilding_wii.chunk').read_bytes()
DONOR=(D/'UC_RedBuilding_Standalone_CarbonPC_V33.chunk').read_bytes()
SCENE=(D/'UC_Wii_RedBuilding_Original_Scene.chunk').read_bytes()
PROOF=(D/'samples/RedBuilding_1B_1C_1Z_Native_PC_V41.chunk').read_bytes()

class V41(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root,cls.report=make_library(DONOR,SOURCE)
        cls.entries={e['name']:e['bytes'] for e in root_parts(cls.root)['entries']}

    def test_01_source_fingerprints(self):
        self.assertEqual(sha(SOURCE),WII_SHA)
        self.assertEqual(sha(DONOR),DONOR_SHA)

    def test_02_deterministic_proof(self):
        self.assertEqual(self.root,PROOF)
        self.assertEqual(make_library(DONOR,SOURCE)[0],self.root)

    def test_03_catalogue_three_original_ids_sorted(self):
        parts=root_parts(self.root)
        self.assertEqual(parts['index'],sorted(bin_hash(modelname(x)) for x in ('1B','1C','1Z')))
        self.assertEqual(parts['index'],[0x80B4A527,0x80B53188,0x80C1CE3F])
        self.assertEqual(len(parts['entries']),3)

    def test_04_lod_wii_geometry_topology_and_attributes(self):
        for lod in ('1B','1C','1Z'):
            with self.subTest(lod=lod):
                name=modelname(lod);src,err=read_model(SOURCE,name)
                self.assertFalse(err);self.assertEqual(len(src),1)
                dst=parse_component(self.entries[name],8,len(self.entries[name]))
                result=validate_face_attributes(src[0],dst)
                self.assertEqual(result['source_faces'],len(src[0]['faces']))

    def test_05_positions_and_faces_count(self):
        self.assertEqual({x:(self.report['lods'][modelname(x)]['native_vertices'],
                              self.report['lods'][modelname(x)]['source_faces'])
                         for x in ('1B','1C','1Z')},
                         {'1B':(400,260),'1C':(239,146),'1Z':(92,58)})

    def test_06_original_wii_matrices_exact(self):
        for lod in ('1B','1C','1Z'):
            name=modelname(lod)
            self.assertEqual(locate_header(self.root,name)[2]['matrix_bytes'],
                             locate_header(SOURCE,name)[2]['matrix_bytes'])

    def test_07_all_native_aabb(self):
        for lod in ('1B','1C','1Z'):
            report=inspect(self.root,modelname(lod))
            self.assertTrue(report['header_equals_material_union'])
            self.assertTrue(report['header_vertex_extrema_plus_0_01'])
            self.assertTrue(all(x['vertex_extrema_plus_0_01'] for x in report['materials']))

    def test_08_same_texture_hash_all_lods(self):
        from carbon_texture_refs_v21 import refs_for_component
        for lod in ('1B','1C','1Z'):
            name=modelname(lod);chunk=self.entries[name]
            refs=refs_for_component(chunk,8,len(chunk))
            self.assertIn(TEXTURE_HASH,refs)
            material=parse_component(chunk,8,len(chunk))['materials'][0]
            self.assertEqual(struct.unpack_from('<I',bytes.fromhex(material['source_record_hex']),0x3c)[0],TEXTURE_HASH)

    def test_09_original_one_b_component_byte_identical(self):
        src=root_parts(DONOR)['entries'][0]['bytes']
        self.assertEqual(self.entries[modelname('1B')],src)

    def test_10_catalogue_pc_platform_settings_preserved(self):
        src=root_parts(DONOR)['info'];dst=root_parts(self.root)['info']
        self.assertEqual(src[:12],dst[:12]);self.assertEqual(src[16:],dst[16:])
        self.assertEqual(struct.unpack_from('<I',dst,0x48)[0],0x3058)
        self.assertEqual(struct.unpack_from('<I',dst,0x70)[0],0x80)
        self.assertEqual(struct.unpack_from('<I',dst,0x0c)[0],3)

    def test_11_source_info_lods_resolve_and_instance_unmodified(self):
        pcrow,instance,info=verify_scene_info(SCENE,self.root)
        srcrow,sourceinstance=first_instance_of_name(SCENE,'XBu_RedBuilding_1b_00')
        self.assertEqual(sourceinstance,instance)
        self.assertEqual(pcrow[:24],srcrow[:24]);self.assertEqual(pcrow[28:],srcrow[28:])
        self.assertEqual(struct.unpack_from('<4I',pcrow,24),
                         (0x80B4A527,0x80B4A527,0x80B53188,0x80C1CE3F))
        self.assertTrue(info['all_referenced_models_present'])

    def test_12_missing_lod_must_fail(self):
        candidate,_,_=verify_scene_info(SCENE,self.root)
        with self.assertRaises(SceneReferenceError):
            strict_require_complete(candidate,{0x80B4A527,0x80B53188})

    def test_13_corrupt_source_rejected(self):
        edited=bytearray(SOURCE);edited[-7]^=1
        with self.assertRaises(LODError):make_library(DONOR,bytes(edited))

    def test_14_corrupt_donor_rejected(self):
        edited=bytearray(DONOR);edited[-11]^=1
        with self.assertRaises(LODError):make_library(bytes(edited),SOURCE)

    def test_15_incomplete_source_scene_rejected(self):
        edited=bytearray(SCENE)
        edited[0:4]=b'BAD!'
        with self.assertRaises((SceneReferenceError,LODError)):verify_scene_info(bytes(edited),self.root)

    def test_16_readback_all_counts(self):
        self.assertEqual(len(PROOF),31132)
        self.assertEqual(sum(v['native_vertices'] for v in self.report['lods'].values()),731)
        self.assertEqual(sum(v['source_faces'] for v in self.report['lods'].values()),464)

    def test_17_no_world_files_modified(self):
        self.assertTrue(self.report['stage'].startswith('OFFLINE'))
        self.assertTrue(any('collision' in x for x in self.report['unresolved']))
        self.assertTrue(any('streaming' in x for x in self.report['unresolved']))

    def test_18_scene_preview_is_deterministic(self):
        root,row,instance,report=run(DONOR,SOURCE,SCENE)
        self.assertEqual(root,PROOF)
        self.assertEqual(row,(D/'samples/RedBuilding_1B_PC_InfoRow_PREVIEW_V41.bin').read_bytes())
        self.assertEqual(instance,(D/'samples/RedBuilding_Source_Instance_UNCHANGED_V41.bin').read_bytes())
        self.assertTrue(report['scenery_info_lod_references_all_resolve'])

if __name__=='__main__':unittest.main()
