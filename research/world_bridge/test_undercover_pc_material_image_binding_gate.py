"""Synthetic-only PC-shaped geometry→DXT5 texture identity binding regression tests.

No original game file, model/texture ID, proprietary pixel, path or coordinate
is embedded. GitHub CI uses the actual checked-in Carbon PC parse modules.
"""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from undercover_pc_geometry_bridge import convert_decoded_ps2_model
from undercover_pc_partition_registry_gate import merge_pc_pack_candidates
from undercover_pc_dxt5_new_identity_candidate import _assemble_pc_dxt5_entries
from synthetic_dxt5_texture_writer import encode_dxt5_mips
from geometry_hash_control import parse_geometry_root, SOLID_ROOT, read_chunks
from undercover_pc_material_image_binding_gate import (
    audit_candidate_material_bindings, _private_identity_set,
    _native_mesh_material_triangle_budget,
    _convert_owner_geometry_section, audit_private_owner_archive,
)

TEX_A = 0x10101
TEX_B = 0x20202
TEX_C = 0x30303
MODEL_BASE = 0x90909
SRC_POS = ((0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.))
SRC_UV = ((0.,0.),(1.,0.),(1.,1.),(0.,1.))
FACES = ((0,1,2),(0,2,3))


def make_model(identity=MODEL_BASE, table=(TEX_A,TEX_B), labels=(0,1)):
    blob, stats = convert_decoded_ps2_model(identity, table, SRC_POS, SRC_UV,
                                           FACES, labels)
    assert stats['source_triangles'] == 2
    return blob


def pack(*roots):
    return merge_pc_pack_candidates(list(roots))[0]


def texture_root(identities=(TEX_A,)):
    rgba = bytes((235,105,25,128))*16
    image,_=encode_dxt5_mips(rgba,4,4,1)
    entries=[(h,('TEST_RGBA_%d' % k).encode('ascii'),4,4,1,image)
             for k,h in enumerate(identities)]
    return _assemble_pc_dxt5_entries(entries)[0]


def geometry(packs=None):
    if packs is None:
        a = pack(make_model())
        packs={241:(a,)*4, 3401:(a,)*4}
    return packs


class SyntheticJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack=pack(make_model())
        cls.geo=geometry()
        cls.tex=texture_root()
        cls.all_tex=texture_root((TEX_A,TEX_B))
        cls.one=audit_candidate_material_bindings(cls.geo,cls.tex,{TEX_A})

    def test_two_materials_one_missing(self):
        s=self.one
        self.assertEqual((s['pc_total_triangles'],s['pc_triangles_with_candidate_dxt5_identity'],
                          s['pc_triangles_without_candidate_dxt5_identity']),(16,8,8))
    def test_none_of_eight_packs_claim_complete_when_each_has_missing_images(self):
        self.assertEqual(self.one['fully_image_bound_geometry_pack_count'],0)
        self.assertEqual(self.one['triangles_in_fully_image_bound_geometry_packs'],0)
    def test_six_pack_like_subset_does_not_drop_incomplete_pack_faces(self):
        present=pack(make_model(table=(TEX_A,TEX_A)))
        g=geometry({241:(present,present,present,self.pack),
                    3401:(present,present,present,self.pack)})
        r=audit_candidate_material_bindings(g,self.tex,{TEX_A})
        self.assertEqual(r['fully_image_bound_geometry_pack_count'],6)
        self.assertEqual(r['triangles_in_fully_image_bound_geometry_packs'],12)
        self.assertEqual(r['triangles_in_partially_bound_geometry_packs'],4)
        self.assertEqual(r['pc_triangles_without_candidate_dxt5_identity'],2)
        self.assertFalse(r['offline_material_image_identity_coverage_complete'])
    def test_all_eight_packs_claim_complete_only_with_both_images(self):
        r=audit_candidate_material_bindings(self.geo,self.all_tex,{TEX_A,TEX_B},True)
        self.assertEqual(r['fully_image_bound_geometry_pack_count'],8)
        self.assertEqual(r['triangles_in_fully_image_bound_geometry_packs'],16)
    def test_missing_not_fabricated(self):
        self.assertEqual(self.one['source_material_identities_without_candidate_image'],1)
        self.assertFalse(self.one['offline_material_image_identity_coverage_complete'])
        self.assertTrue(self.one['no_missing_textures_fabricated'])
    def test_complete_candidate_all_materials(self):
        r=audit_candidate_material_bindings(self.geo,self.all_tex,{TEX_A,TEX_B},True)
        self.assertEqual(r['pc_triangles_without_candidate_dxt5_identity'],0)
        self.assertTrue(r['offline_material_image_identity_coverage_complete'])
        self.assertEqual(r['source_material_identities_with_candidate_image'],2)
    def test_strict_refuses_missing(self):
        with self.assertRaisesRegex(ValueError,'complete PC registration refused'):
            audit_candidate_material_bindings(self.geo,self.tex,{TEX_A},True)
    def test_per_section_separate(self):
        for key in ('241','3401'):
            s=self.one['per_source_section'][key]
            self.assertEqual((s['source_geometry_pack_count'],s['triangles'],
                s['triangles_with_candidate_dxt5_identity'],s['triangles_without_candidate_dxt5_identity']),
                (4,8,4,4))
    def test_pack_order_preserved(self):
        self.assertEqual([r['triangles'] for r in self.one['per_source_section']['241']['per_pack']],
                         [2,2,2,2])
    def test_model_occurrences_preserved(self):
        self.assertEqual((self.one['pc_model_occurrences'],self.one['distinct_pc_model_identities']),
                         (8,1))
    def test_duplicate_identities_across_packs_allowed(self):
        self.assertEqual(self.one['repeated_model_identities_across_source_packs_or_sections'],1)
    def test_material_mesh_counts(self):
        self.assertEqual((self.one['pc_material_meshes'],self.one['pc_material_meshes_without_candidate_dxt5_identity']),
                         (16,8))
    def test_no_private_ids_in_json(self):
        dump=json.dumps(self.one)
        self.assertNotIn(str(TEX_A),dump)
        self.assertNotIn(str(TEX_B),dump)
        self.assertNotIn(str(MODEL_BASE),dump)
        self.assertNotIn('TEST_RGBA',dump)
    def test_unknown_runtime_scope(self):
        self.assertFalse(self.one['safe_for_game_install'])
        self.assertEqual(self.one['engine_registration'],'UNVERIFIED')
    def test_private_provenance_flag(self):
        self.assertTrue(self.one['candidate_ids_exactly_equal_to_validated_source_image_ids'])
    def test_unknown_provenance_flag_false(self):
        r=audit_candidate_material_bindings(self.geo,self.tex)
        self.assertFalse(r['candidate_ids_exactly_equal_to_validated_source_image_ids'])
    def test_disjoint_material_table_repetitions(self):
        p=pack(make_model(table=(TEX_A,TEX_A),labels=(0,1)))
        g=geometry({241:(p,)*4,3401:(p,)*4})
        r=audit_candidate_material_bindings(g,self.tex,{TEX_A},True)
        self.assertEqual(r['source_material_identities_used'],1)
        self.assertEqual(r['pc_material_meshes'],16)
    def test_unused_original_material_index_is_not_a_missing_binding(self):
        p=pack(make_model(table=(TEX_A,TEX_B),labels=(0,0)))
        g=geometry({241:(p,)*4,3401:(p,)*4})
        r=audit_candidate_material_bindings(g,self.tex,{TEX_A},True)
        self.assertEqual((r['source_material_identities_used'],r['pc_triangles_without_candidate_dxt5_identity']), (1,0))
    def test_model_identity_repeated_only_across_independent_packs(self):
        a=make_model(0x5001)
        b=make_model(0x5002)
        ab=pack(b,a)
        g=geometry({241:(ab,)*4,3401:(ab,)*4})
        r=audit_candidate_material_bindings(g,self.tex,{TEX_A})
        self.assertEqual(r['pc_model_occurrences'],16)
        self.assertEqual(r['pc_total_triangles'],32)
        self.assertEqual(r['distinct_pc_model_identities'],2)
    def test_second_section_can_use_different_source_models(self):
        other=pack(make_model(0x50505,table=(TEX_B,TEX_B)))
        g=geometry({241:(self.pack,)*4,3401:(other,)*4})
        r=audit_candidate_material_bindings(g,self.tex,{TEX_A})
        self.assertEqual((r['per_source_section']['241']['triangles_without_candidate_dxt5_identity'],
                          r['per_source_section']['3401']['triangles_without_candidate_dxt5_identity']), (4,8))
    def test_dxt5_index_accepts_ordinal_order_independent(self):
        t=texture_root((TEX_B,TEX_A))
        r=audit_candidate_material_bindings(self.geo,t,{TEX_A,TEX_B},True)
        self.assertEqual(r['source_material_identities_with_candidate_image'],2)
    def test_original_source_image_ids_can_be_frozenset(self):
        self.assertEqual(audit_candidate_material_bindings(self.geo,self.tex,frozenset({TEX_A}))['pc_candidate_dxt5_image_identity_count'],1)


class FailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=pack(make_model())
        cls.g=geometry({241:(cls.p,)*4,3401:(cls.p,)*4})
        cls.tex=texture_root()
    _UNSET = object()
    def call(self,geom=_UNSET,texture=_UNSET,src=_UNSET,strict=False):
        return audit_candidate_material_bindings(self.g if geom is self._UNSET else geom,
                   self.tex if texture is self._UNSET else texture,
                   {TEX_A} if src is self._UNSET else src,strict)
    def test_wrong_source_section_keys(self):
        for bad in ({241:(self.p,)*4},{141:(self.p,)*4,142:(self.p,)*4},[],None):
            with self.subTest(bad_type=type(bad)),self.assertRaises(ValueError):
                self.call(geom=bad)
    def test_section_needs_four_packs(self):
        for n in (0,1,3,5):
            with self.subTest(n=n),self.assertRaisesRegex(ValueError,'four independent'):
                self.call(geom={241:(self.p,)*n,3401:(self.p,)*4})
    def test_pack_bytes_required(self):
        for bad in (None, 123, bytearray(self.p), self.p[:10]):
            with self.subTest(kind=type(bad)),self.assertRaises(ValueError):
                self.call(geom={241:(bad,)*4,3401:(self.p,)*4})
    def test_wrong_texture_type(self):
        for bad in (None,bytearray(self.tex),'not a pack',b'',0):
            with self.subTest(kind=type(bad)),self.assertRaises(ValueError):
                self.call(texture=bad)
    def test_corrupt_texture_root_rejected(self):
        for bad in (self.tex[:-1], bytes(64),self.tex[:10]+bytes(16)+self.tex[26:]):
            with self.subTest(sz=len(bad)),self.assertRaises(ValueError):
                self.call(texture=bad)
    def test_original_image_id_mismatch(self):
        for ids in ({TEX_B},{TEX_A,TEX_B},set()):
            with self.subTest(ids=len(ids)),self.assertRaises(ValueError):
                self.call(src=ids)
    def test_original_image_identity_must_be_set(self):
        for ids in ([TEX_A],(TEX_A,),{True},{-1},{0},'identity'):
            with self.subTest(ids=repr(ids)),self.assertRaises(ValueError):
                self.call(src=ids)
    def test_bool_flag_refused(self):
        for f in ('yes',None,1,[],{}):
            with self.subTest(f=f),self.assertRaises(ValueError):
                self.call(strict=f)
    def test_model_header_corruption_rejected(self):
        bad=bytearray(self.p);bad[0]=0xff
        with self.assertRaises(ValueError):
            self.call(geom={241:(bytes(bad),)*4,3401:(self.p,)*4})
    def test_model_payload_truncation_refused(self):
        with self.assertRaises(ValueError):
            self.call(geom={241:(self.p[:-4],)*4,3401:(self.p,)*4})
    def test_corrupt_packed_material_word_rejected(self):
        # Locate the source synthetic PC mesh chunk and alter only a material index.
        root=bytearray(self.p)
        needle=struct.pack('<II',0x00134b02,4+144*2)
        at=root.find(needle)
        self.assertGreater(at,0)
        struct.pack_into('<I',root,at+8+4+0x18,0x02010000)
        with self.assertRaises(ValueError):
            self.call(geom={241:(bytes(root),)*4,3401:(self.p,)*4})
    def test_bad_triangle_count_refused(self):
        root=bytearray(self.p)
        needle=struct.pack('<II',0x00134b02,4+144*2)
        at=root.find(needle)
        self.assertGreater(at,0)
        struct.pack_into('<I',root,at+8+4+0x60,0)
        with self.assertRaises(ValueError):
            self.call(geom={241:(bytes(root),)*4,3401:(self.p,)*4})
    def test_bad_mesh_index_offset_refused(self):
        root=bytearray(self.p)
        at=root.find(struct.pack('<II',0x00134b02,4+144*2))
        self.assertGreater(at,0)
        struct.pack_into('<I',root,at+8+4+0x64,100)
        with self.assertRaises(ValueError):
            self.call(geom={241:(bytes(root),)*4,3401:(self.p,)*4})
    def test_pc_geometry_platform_not_ps2(self):
        # Our correct input is PC. Mutating its platform tag must fail native parsing.
        root=bytearray(self.p)
        offset=root.find(struct.pack('<I',0x00134900))
        self.assertGreater(offset,0)
        struct.pack_into('<I',root,offset,0x00134a00)
        with self.assertRaises(ValueError):
            self.call(geom={241:(bytes(root),)*4,3401:(self.p,)*4})
    def test_duplicate_identities_within_same_pack_rejected_by_assembler(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            pack(make_model(),make_model())
    def test_no_raw_private_hashes_in_errors(self):
        try:self.call(strict=True)
        except ValueError as err:
            self.assertNotIn(str(TEX_B),str(err))
            self.assertNotIn(str(MODEL_BASE),str(err))
        else:self.fail('Strict incomplete coverage did not refuse')
    def test_missing_owner_zip_fails_without_creating_files(self):
        with tempfile.TemporaryDirectory() as p:
            target=Path(p)/'not_found.zip'
            with self.assertRaises(ValueError):audit_private_owner_archive(target)
            self.assertFalse(target.exists())
    def test_symlinked_owner_zip_fails(self):
        with tempfile.TemporaryDirectory() as p:
            first=Path(p)/'original.zip';first.write_bytes(b'not_real_zip')
            link=Path(p)/'link.zip'
            try:link.symlink_to(first)
            except (OSError,NotImplementedError):self.skipTest('Symlinks unsupported')
            with self.assertRaisesRegex(ValueError,'Symlinked'):
                audit_private_owner_archive(link)
    def test_bad_owner_archive_zip_fails(self):
        with tempfile.TemporaryDirectory() as p:
            target=Path(p)/'not_zip.bin';target.write_bytes(b'NOT A ZIP')
            with self.assertRaises(Exception):audit_private_owner_archive(target)
    def test_private_set_utility(self):
        self.assertEqual(_private_identity_set({TEX_A,TEX_B}),{TEX_A,TEX_B})
        for bad in ([],set(),{0},{-10},{True},{'abc'}):
            with self.assertRaises(ValueError):_private_identity_set(bad)


if __name__=='__main__':unittest.main()
