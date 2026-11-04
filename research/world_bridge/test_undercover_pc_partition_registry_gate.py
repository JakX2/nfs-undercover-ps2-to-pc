"""Source-free regression tests for Undercover's original four-pack boundaries.

No original game assets or reconstructed model hashes are embedded. The tests
exercise the actual checked-in PC parsers on GitHub CI.
"""
import os
import tempfile
import struct
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from undercover_pc_partition_registry_gate import (
    source_partition_roots, merge_pc_pack_candidates, material_registry_coverage,
    scene_detail_registry_coverage, reconcile_cross_section_scene_registry, reconcile_cross_section_material_registry, convert_four_pack_section,
    _read_owner_zip_section, audit_original_four_pack_registry)
from undercover_pc_geometry_bridge import _chunk, _new_header, convert_decoded_ps2_model
from geometry_hash_control import read_chunks, parse_geometry_root, parse_solid, SOLID_ROOT


def triangle():
    xyz = ((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
    uv = ((0.,0.),(1.,0.),(0.,1.))
    return xyz,uv,((0,1,2),),(0,)


def pc_model(identity, textures=(0x1111,)):
    x,u,f,l = triangle()
    return convert_decoded_ps2_model(identity,textures,x,u,f,l)[0]


def ps2_pack(ids, textures=(0x1111,)):
    # Synthetic PS2 metadata/strip array, structurally valid but not game data.
    originals = []
    for identity in ids:
        header = _new_header(identity,len(textures))
        info = bytearray(b'\x11'*4+bytes(48))
        struct.pack_into('<III',info,4,0x20,1,16)
        rows=bytearray(b'\x11'*4+bytes(16))
        struct.pack_into('<HBBfHbbBBbb',rows,4,0,3,1,1.,0,0,0,1,0,0,0)
        platform = (_chunk(0x134a00,bytes(info))+
                    _chunk(0x134a01,bytes(rows))+
                    _chunk(0x134a02,b'\x11'*8+bytes(16)))
        solid = _chunk(0x80134010,_chunk(0x134011,header)+
                _chunk(0x134012,b''.join(struct.pack('<II',h,0) for h in textures))+
                _chunk(0x80134100,platform))
        originals.append(solid)
    geom_header = _chunk(0x80134001,
           _chunk(0x134002,bytes(144))+
           _chunk(0x134003,b''.join(struct.pack('<II',h,0) for h in sorted(ids)))+
           _chunk(0x80134008,b''))
    return _chunk(0x80134000,bytes(8)+geom_header+b''.join(originals))


def fake_groups(overlap=False):
    ids=[(11,12),(21,22),(31,32),(41,42)]
    if overlap:ids[-1]=(11,42)
    return tuple(tuple((h,_new_header(h,1),(0x1111,),()) for h in p) for p in ids)


class SourcePartitionTests(unittest.TestCase):
    def test_four_packs_retained(self):
        source=b''.join(ps2_pack((100*i+1,100*i+2)) for i in (1,2,3,4))
        result=source_partition_roots(source)
        self.assertEqual([len(p) for p in result],[2,2,2,2])
        self.assertEqual([r[0] for r in result[0]],[101,102])
    def test_repeat_across_separate_packs_retained(self):
        result=source_partition_roots(ps2_pack((100,))+ps2_pack((100,)))
        self.assertEqual(len(result),2)
        self.assertEqual(result[0][0][0],result[1][0][0])
        self.assertIsNot(result[0][0],result[1][0])
    def test_material_table_entries_retained(self):
        a=source_partition_roots(ps2_pack((100,),textures=(11,11,12)))
        self.assertEqual(a[0][0][2],(11,11,12))
    def test_original_resource_order_retained_unsorted(self):
        self.assertEqual([x[0] for x in source_partition_roots(ps2_pack((19,4,11)))[0]],[19,4,11])
    def test_reject_pc_as_source(self):
        with self.assertRaisesRegex(ValueError,'not PS2'):
            source_partition_roots(pc_model(101))
    def test_reject_invalid_section_inputs(self):
        for value in (b'',bytearray(ps2_pack((10,))),b'junk'*5):
            with self.subTest(t=type(value)),self.assertRaises(ValueError):
                source_partition_roots(value)
    def test_reject_duplicate_inside_source_pack(self):
        a=ps2_pack((10,10))
        with self.assertRaises(ValueError):source_partition_roots(a)
    def test_reject_truncated_source_pack(self):
        with self.assertRaises(ValueError):source_partition_roots(ps2_pack((10,))[:-2])
    def test_reject_wrong_source_platform(self):
        pack=ps2_pack((10,))
        with self.assertRaises(ValueError):source_partition_roots(pack.replace(struct.pack('<I',0x134a00),struct.pack('<I',0x134900),1))
    def test_parser_ignores_unanchored_geometry_magic(self):
        body=b'\xfe\xfe\xfe\xfe'+ps2_pack((10,))
        self.assertEqual(len(source_partition_roots(body)),1)
    def test_reject_excessive_pack_count(self):
        with self.assertRaisesRegex(ValueError,'Excessive'):
            source_partition_roots(ps2_pack((10,))*17)
    def test_source_root_contains_expected_identity_only(self):
        p=source_partition_roots(ps2_pack((10,20)))[0]
        self.assertEqual({x[0] for x in p},{10,20})


class PackAssemblerTests(unittest.TestCase):
    def test_one_complete_pack_two_solids(self):
        merged,s=merge_pc_pack_candidates([pc_model(20),pc_model(10)])
        self.assertEqual(s['pc_pack_solid_occurrences'],2)
        self.assertEqual(parse_geometry_root(merged)['hashes'],frozenset({10,20}))
        solids=[v for k,v in read_chunks(merged,16,len(merged)) if k==SOLID_ROOT]
        self.assertEqual([parse_solid(x)[0] for x in solids],[20,10])
    def test_preserve_serialized_children(self):
        a=pc_model(9);b=pc_model(8)
        merged,_=merge_pc_pack_candidates([a,b])
        before=[next(v for k,v in read_chunks(x,16,len(x)) if k==SOLID_ROOT) for x in (a,b)]
        after=[v for k,v in read_chunks(merged,16,len(merged)) if k==SOLID_ROOT]
        self.assertEqual(before,after)
    def test_deterministic_merged_bytes(self):
        roots=[pc_model(2),pc_model(1)]
        self.assertEqual(merge_pc_pack_candidates(roots)[0],merge_pc_pack_candidates(roots)[0])
    def test_same_identity_allowed_in_separate_packs(self):
        a,_=merge_pc_pack_candidates([pc_model(11)])
        b,_=merge_pc_pack_candidates([pc_model(11)])
        self.assertEqual(parse_geometry_root(a)['hashes'],parse_geometry_root(b)['hashes'])
    def test_duplicates_inside_pack_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            merge_pc_pack_candidates([pc_model(11),pc_model(11)])
    def test_reject_two_model_root_as_single_candidate(self):
        pack,_=merge_pc_pack_candidates([pc_model(11),pc_model(12)])
        with self.assertRaisesRegex(ValueError,'exactly one'):
            merge_pc_pack_candidates([pack])
    def test_reject_empty_pack(self):
        with self.assertRaises(ValueError):merge_pc_pack_candidates([])
    def test_reject_nonbytes_candidate(self):
        with self.assertRaises(ValueError):merge_pc_pack_candidates([bytearray(pc_model(1))])
    def test_reject_nonpc_geometry(self):
        with self.assertRaises(ValueError):merge_pc_pack_candidates([ps2_pack((1,))])
    def test_reject_corrupted_geometry_root(self):
        with self.assertRaises(ValueError):merge_pc_pack_candidates([pc_model(11)[:-1]])
    def test_reject_invalid_type(self):
        with self.assertRaises(ValueError):merge_pc_pack_candidates(None)
    def test_pack_index_is_hash_sorted_even_when_solids_are_not(self):
        a,_=merge_pc_pack_candidates([pc_model(300),pc_model(100),pc_model(200)])
        h=next(v for k,v in read_chunks(a,16,len(a)) if k==0x80134001)
        entries=list(read_chunks(h,0,len(h)))
        ids=[r[0] for r in struct.iter_unpack('<II',entries[1][1])]
        self.assertEqual(ids,[100,200,300])


class MaterialRegistryTests(unittest.TestCase):
    def test_no_material_identity_match(self):
        p=fake_groups()
        result=material_registry_coverage(p,{0xDEAD})
        self.assertEqual(result['used_distinct_identities_absent_from_carbon_rb'],1)
        self.assertTrue(result['new_texture_registration_or_fallback_still_required'])
    def test_all_material_identity_matches(self):
        p=fake_groups()
        result=material_registry_coverage(p,{0x1111})
        self.assertTrue(result['rb_local_material_identity_coverage_complete'])
        self.assertEqual(result['used_identity_occurrences_found_in_carbon_rb'],8)
    def test_duplicate_material_table_entries_are_counted(self):
        p=(((3,b'',(7,7,9),()),),)
        r=material_registry_coverage(p,{7},used_indices=(((0,1),),))
        self.assertEqual(r['original_material_table_entries'],3)
        self.assertEqual(r['used_material_identity_occurrences'],2)
        self.assertEqual(r['used_distinct_material_texture_ids'],1)
    def test_unused_unregistered_table_entry_not_called_used(self):
        p=(((3,b'',(7,9),()),),)
        r=material_registry_coverage(p,{7},used_indices=(((0,),),))
        self.assertTrue(r['rb_local_material_identity_coverage_complete'])
        self.assertEqual(r['original_distinct_material_texture_ids'],2)
    def test_reject_bad_used_material_index(self):
        p=(((3,b'',(7,),()),),)
        for bad in (True,-1,1):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                material_registry_coverage(p,{7},used_indices=(((bad,),),))
    def test_reject_wrong_partition_count(self):
        with self.assertRaises(ValueError):material_registry_coverage(fake_groups(),{7},used_indices=((),))
    def test_reject_wrong_occurrence_count(self):
        with self.assertRaises(ValueError):material_registry_coverage(fake_groups(),{7},used_indices=((),)*4)
    def test_reject_not_a_private_set(self):
        with self.assertRaises(ValueError):material_registry_coverage(fake_groups(),[7])
    def test_reject_invalid_texture_hash(self):
        with self.assertRaises(ValueError):material_registry_coverage(fake_groups(),{0})
    def test_aggregate_has_no_private_model_or_hash_lists(self):
        d=material_registry_coverage(fake_groups(),{0x1111})
        self.assertFalse(any(isinstance(v,(list,tuple,set)) for v in d.values()))
    def test_normalize_used_index_order_without_doublecount(self):
        p=(((3,b'',(7,8),()),),)
        r=material_registry_coverage(p,{7,8},used_indices=(((1,1,0),),))
        self.assertEqual(r['used_material_identity_occurrences'],2)


class SceneLookupTests(unittest.TestCase):
    def test_all_detail_model_ids_resolved(self):
        r=scene_detail_registry_coverage(fake_groups(),[11,22,31])
        self.assertEqual(r['source_scene_detail_references_backed_by_pack_model'],3)
        self.assertEqual(r['source_scene_detail_references_missing_local_pack_model'],0)
    def test_missing_detail_model_ids_counted(self):
        r=scene_detail_registry_coverage(fake_groups(),[11,404])
        self.assertEqual(r['source_scene_detail_references_missing_local_pack_model'],1)
    def test_cross_pack_repeated_hash_ambiguous(self):
        r=scene_detail_registry_coverage(fake_groups(overlap=True),[11,42,11])
        self.assertEqual(r['source_model_hashes_repeated_across_independent_packs'],1)
        self.assertEqual(r['source_scene_detail_references_with_multiple_pack_occurrences'],2)
    def test_reject_nonoccurrence_input(self):
        with self.assertRaises(ValueError):scene_detail_registry_coverage(fake_groups(),{11,22})
    def test_reject_invalid_source_hash(self):
        with self.assertRaises(ValueError):scene_detail_registry_coverage(fake_groups(),[0])
    def test_reject_missing_packs(self):
        with self.assertRaises(ValueError):scene_detail_registry_coverage((),[1])
    def test_aggregate_contains_no_source_hashes(self):
        d=scene_detail_registry_coverage(fake_groups(),[11,22,30])
        self.assertFalse(any(isinstance(v,(list,set,tuple)) for v in d.values()))


class CrossSectionRegistryTests(unittest.TestCase):
    def pack_map(self):
        return {241:fake_groups(overlap=True),3401:fake_groups()}
    def test_cross_section_resolution(self):
        p=self.pack_map()
        r=reconcile_cross_section_scene_registry(p,{241:[11,12,21],3401:[11,404]})
        self.assertEqual(r['per_section']['3401']['unresolved_across_both_source_sections'],1)
        self.assertEqual(r['per_section']['3401']['locally_resolvable'],1)
    def test_resolution_only_from_other_source_section(self):
        p=self.pack_map()
        # One synthetic identity exists only in source section 241.
        last=list(p[3401]);last[-1]=((41,_new_header(41,1),(0x1111,),()),)
        p[3401]=tuple(last)
        r=reconcile_cross_section_scene_registry(p,{241:[42],3401:[42,41]})
        self.assertEqual(r['per_section']['3401']['other_section_only_resolvable'],1)
        self.assertEqual(r['per_section']['3401']['unresolved_across_both_source_sections'],0)
        self.assertTrue(r['all_source_scene_model_hashes_accounted_for_by_either_section'])
    def test_missing_across_both_sections_is_not_hidden(self):
        r=reconcile_cross_section_scene_registry(self.pack_map(),{241:[999],3401:[11]})
        self.assertFalse(r['all_source_scene_model_hashes_accounted_for_by_either_section'])
    def test_nonunique_source_references_are_counted(self):
        r=reconcile_cross_section_scene_registry(self.pack_map(),{241:[11,11,11],3401:[11]})
        self.assertEqual(r['per_section']['241']['locally_resolvable'],3)
    def test_reject_wrong_source_sections(self):
        with self.assertRaises(ValueError):
            reconcile_cross_section_scene_registry({241:fake_groups()},{241:[11]})
    def test_reject_no_source_info_references(self):
        with self.assertRaises(ValueError):
            reconcile_cross_section_scene_registry(self.pack_map(),{241:[],3401:[11]})
    def test_reject_bad_referenced_hash(self):
        with self.assertRaises(ValueError):
            reconcile_cross_section_scene_registry(self.pack_map(),{241:[0],3401:[11]})
    def test_reject_empty_source_pack(self):
        p=self.pack_map();p[3401]=()
        with self.assertRaises(ValueError):
            reconcile_cross_section_scene_registry(p,{241:[11],3401:[11]})
    def test_only_aggregate_ids_returned(self):
        r=reconcile_cross_section_scene_registry(self.pack_map(),{241:[11,31],3401:[21]})
        self.assertFalse(any(isinstance(v,(set,list,tuple,bytes)) for v in r.values()))
        self.assertEqual(set(r['per_section']),{'241','3401'})


class CrossSectionMaterialTests(unittest.TestCase):
    def join(self,section_241=None,section_3401=None,pc=()):
        group_241 = fake_groups() if section_241 is None else section_241
        group_3401 = fake_groups() if section_3401 is None else section_3401
        with patch('triangle_corner_uv_control.ps2_geometry_attributes',return_value=triangle()):
            return reconcile_cross_section_material_registry(
                {241:group_241,3401:group_3401},set(pc))
    def test_shared_id_counted_once(self):
        r=self.join()
        self.assertEqual(r['used_distinct_source_material_texture_ids_combined'],1)
        self.assertEqual(r['used_distinct_source_material_texture_ids_shared_sections'],1)
    def test_unique_only_241_identity(self):
        p=fake_groups();q=list(fake_groups());part=list(p)
        first=list(part[0]);row=first[0]
        first[0]=(row[0],row[1],(0x2222,),row[3])
        part[0]=tuple(first)
        r=self.join(section_241=tuple(part),section_3401=tuple(q))
        self.assertEqual(r['used_distinct_source_material_texture_ids_combined'],2)
        self.assertEqual(r['used_distinct_source_material_texture_ids_only_section_241'],1)
    def test_matches_reported_separately(self):
        r=self.join(pc=(0x1111,))
        self.assertEqual(r['combined_used_material_ids_present_in_carbon_rb_texture_indexes'],1)
        self.assertFalse(r['additional_identity_registration_or_remap_required_for_rb_only'])
    def test_absent_carbon_registry_reported_as_gap(self):
        r=self.join(pc=())
        self.assertEqual(r['combined_used_material_ids_absent_from_carbon_rb_texture_indexes'],1)
        self.assertTrue(r['additional_identity_registration_or_remap_required_for_rb_only'])
    def test_reject_nonset_carbon_registry(self):
        with self.assertRaises(ValueError):
            reconcile_cross_section_material_registry({241:fake_groups(),3401:fake_groups()},[0x1111])
    def test_reject_invalid_section_set(self):
        with self.assertRaises(ValueError):
            reconcile_cross_section_material_registry({241:fake_groups()},set())
    def test_missing_material_face_refuses(self):
        with patch('triangle_corner_uv_control.ps2_geometry_attributes',return_value=((),(),(),())):
            with self.assertRaises(ValueError):
                reconcile_cross_section_material_registry({241:fake_groups(),3401:fake_groups()},set())
    def test_aggregate_is_private(self):
        r=self.join()
        self.assertFalse(any(isinstance(x,(bytes,list,tuple,set)) for x in r.values()))


class FullSectionGateTests(unittest.TestCase):
    def setUp(self):
        self.packs=fake_groups(overlap=True)
    def run_gate(self,registered=frozenset({0x1111}),scene=(11,12,21,22,31,32,41,42)):
        with patch('triangle_corner_uv_control.ps2_geometry_attributes',return_value=triangle()):
            return convert_four_pack_section(self.packs,registered,scene)
    def test_four_pack_build_and_triangle_count(self):
        r=self.run_gate()
        self.assertEqual(r['pc_candidate_pack_count'],4)
        self.assertEqual(r['source_models_per_pack'],[2,2,2,2])
        self.assertEqual(r['source_model_occurrences'],8)
        self.assertEqual(r['generated_pc_triangles'],8)
        self.assertTrue(r['all_pc_packs_pass_native_source_parser'])
    def test_duplicate_identity_across_pack_count(self):
        r=self.run_gate()
        self.assertEqual(r['distinct_source_model_identities'],7)
        self.assertEqual(r['cross_pack_duplicate_model_identity_count'],1)
    def test_no_registered_texture_reported_as_gap(self):
        r=self.run_gate(registered=frozenset())
        self.assertEqual(r['material_texture_identity_preflight']['used_distinct_identities_absent_from_carbon_rb'],1)
    def test_ambiguous_scene_reference_reported(self):
        r=self.run_gate()
        self.assertEqual(r['scene_primary_model_identity_preflight']['source_scene_detail_references_with_multiple_pack_occurrences'],1)
    def test_reject_wrong_pack_count(self):
        with self.assertRaisesRegex(ValueError,'exactly four'):
            convert_four_pack_section(self.packs[:3],set(),())
    def test_reject_empty_pack(self):
        with self.assertRaises(ValueError):convert_four_pack_section(((),*self.packs[1:]),set(),())
    def test_no_copyrighted_payload_returned(self):
        r=self.run_gate()
        self.assertNotIn('packed',r)
        self.assertFalse(any(isinstance(v,bytes) for v in r.values()))
        self.assertFalse(r['game_data_written'])
    def test_reproducible_aggregate(self):
        self.assertEqual(self.run_gate(),self.run_gate())
    def test_wrong_source_header_refused(self):
        bad=list(self.packs)
        g=list(bad[0]);g[0]=(g[0][0],_new_header(77,1),g[0][2],g[0][3]);bad[0]=tuple(g)
        with patch('triangle_corner_uv_control.ps2_geometry_attributes',return_value=triangle()):
            with self.assertRaisesRegex(ValueError,'source header'):
                convert_four_pack_section(tuple(bad),{0x1111})


class PrivateArchiveSafetyTests(unittest.TestCase):
    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):audit_original_four_pack_registry('/does/not/exist.zip','/nope.zip')
    def test_same_source_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'private.zip';p.write_bytes(b'placeholder')
            with self.assertRaises(ValueError):audit_original_four_pack_registry(p,[p,p])
    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'private.zip';p.write_bytes(b'data')
            target=Path(tmp)/'aliased.zip'
            target.symlink_to(p)
            with self.assertRaises(ValueError):audit_original_four_pack_registry(target,[p,p])
    def test_source_unmodified_in_mocked_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'uc.zip';b=Path(tmp)/'carbon.zip'
            a.write_bytes(b'owner private fixture one');b.write_bytes(b'fixture two');(Path(tmp)/'carbon_final.zip').write_bytes(b'other fixture')
            with (patch('undercover_pc_partition_registry_gate._read_owner_pc_registered_hashes',return_value=({0x1111},(2,3))),
                  patch('undercover_pc_partition_registry_gate._read_owner_zip_section',return_value=b'candidate'),
                  patch('undercover_pc_partition_registry_gate.source_partition_roots',return_value=self_dummy()),
                  patch('undercover_pc_partition_registry_gate._source_scene_detail_hashes',return_value=(11,)),
                  patch('undercover_pc_partition_registry_gate.convert_four_pack_section',return_value={'source_model_occurrences':8}),
                  patch('undercover_pc_partition_registry_gate.reconcile_cross_section_material_registry',return_value={'used_distinct_source_material_texture_ids_combined':1})):
                result=audit_original_four_pack_registry(a,[b,Path(tmp)/'carbon_final.zip'])
            self.assertEqual(result['original_carbon_rb_texture_records'],5)
            self.assertEqual(a.read_bytes(),b'owner private fixture one')
            self.assertEqual(b.read_bytes(),b'fixture two')
            self.assertTrue(result['originals_unchanged'])
    def test_archive_member_missing_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'original.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('unrelated',b'x')
            with self.assertRaises((KeyError,ValueError)):_read_owner_zip_section(p,241)


def self_dummy():
    return fake_groups()


if __name__=='__main__':unittest.main()
