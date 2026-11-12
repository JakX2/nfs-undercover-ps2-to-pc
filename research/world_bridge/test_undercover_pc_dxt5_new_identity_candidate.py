"""Source-free PC DXT5 candidate identity and envelope tests, no game assets."""
import struct
import unittest
from unittest import mock

from test_texture_visual_pair_gate import make_pack
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from pc_texture_header_overlay_gate import _source_image_span
from pc_dxt_reference_decode import decode_dxt_base
from synthetic_dxt5_texture_writer import encode_dxt5_mips
from undercover_pc_dxt5_new_identity_candidate import (
    _ids, _padded_name, _assemble_pc_dxt5_entries,
    audit_registration_coverage, build_private_dxt5_candidate)

ONE=0x11111111
TWO=0x22222222
THREE=0x33333333


def ps2(bits=8):
    return make_pack('ps2',bits=bits,hashes=(ONE,TWO))


def entries():
    source=bytes((255,0,0,64))*64
    image,spans=encode_dxt5_mips(source,8,8,3)
    return [(ONE,b'SYNTH_FIRST',8,8,3,image),
            (TWO,b'SYNTH_SECOND',8,8,3,image)]


class CoverageTests(unittest.TestCase):
    def test_one_missing_used_id(self):
        p=ps2()
        r=audit_registration_coverage({ONE,TWO,THREE},{241:p,3401:p})
        self.assertEqual((r['used_distinct_material_identities'],r['used_identities_with_source_images'],r['used_identities_without_source_images']),(3,2,1))
        self.assertFalse(r['complete_material_image_coverage'])
        self.assertTrue(r['missing_identities_are_not_fabricated'])
    def test_all_used_images_present(self):
        p=ps2()
        self.assertTrue(audit_registration_coverage({ONE,TWO},{241:p,3401:p})['complete_material_image_coverage'])
    def test_carbon_presence_is_separate(self):
        p=ps2()
        r=audit_registration_coverage({ONE,TWO,THREE},{241:p,3401:p},{ONE,THREE})
        self.assertEqual(r['used_identities_with_carbon_rb_images'],2)
        self.assertEqual(r['used_identities_without_source_images'],1)
    def test_empty_explicit_carbon_registry_is_zero_matches(self):
        p=ps2()
        result=audit_registration_coverage({ONE,TWO},{241:p,3401:p},set())
        self.assertEqual(result['used_identities_with_carbon_rb_images'],0)
    def test_carbon_unknown_is_none(self):
        p=ps2()
        self.assertIsNone(audit_registration_coverage({ONE},{241:p,3401:p})['used_identities_with_carbon_rb_images'])
    def test_wrong_section_keys_refused(self):
        with self.assertRaisesRegex(ValueError,'both original'):
            audit_registration_coverage({ONE},{241:ps2()})
    def test_nonbytes_section_refused(self):
        with self.assertRaisesRegex(ValueError,'[Pp]rivate'):
            audit_registration_coverage({ONE},{241:bytearray(ps2()),3401:ps2()})
    def test_empty_material_set_refused(self):
        with self.assertRaisesRegex(ValueError,'Invalid source'):
            audit_registration_coverage(set(),{241:ps2(),3401:ps2()})
    def test_material_set_type_refused(self):
        with self.assertRaisesRegex(ValueError,'identity set'):
            audit_registration_coverage([ONE],{241:ps2(),3401:ps2()})
    def test_bool_material_identity_refused(self):
        with self.assertRaisesRegex(ValueError,'Invalid'):
            audit_registration_coverage({True},{241:ps2(),3401:ps2()})
    def test_corrupted_ps2_section_refused(self):
        with self.assertRaises(ValueError):
            audit_registration_coverage({ONE},{241:b'junk',3401:ps2()})
    def test_privacy_of_counts(self):
        r=audit_registration_coverage({ONE,TWO,THREE},{241:ps2(),3401:ps2()})
        text=str(r)
        for leak in (str(ONE),str(TWO),str(THREE),'SYNTHETIC_','0x11111111'):
            self.assertNotIn(leak,text)


class DescriptorAndPackTests(unittest.TestCase):
    def test_names_padded_and_terminated(self):
        for n in (1,2,3,4,7,14,50,240):
            result=_padded_name(b'A'*n)
            self.assertEqual(len(result),result[0]+1)
            self.assertEqual(result[0]%4,3)
            self.assertEqual(result[1:1+n],b'A'*n)
            self.assertFalse(any(result[1+n:]))
    def test_empty_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'name'):_padded_name(b'')
    def test_embedded_nul_rejected(self):
        with self.assertRaisesRegex(ValueError,'name'):_padded_name(b'BAD\0NAME')
    def test_long_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'name'):_padded_name(b'B'*241)
    def test_nonascii_name_rejected(self):
        with self.assertRaisesRegex(ValueError,'name'):_padded_name(b'\xff')
    def test_two_entry_roundtrip_and_spans(self):
        pack,r=_assemble_pc_dxt5_entries(entries())
        self.assertEqual(r['pc_candidate_texture_identities'],2)
        self.assertTrue(r['all_names_identities_and_encoded_spans_read_back'])
        records=parse_pack(pack,'pc')['records']
        self.assertEqual(list(records),[ONE,TWO])
        aligned,padding=aligned_pixel_array(pack,records)
        self.assertEqual(padding,120)
        for key in (ONE,TWO):
            m=records[key];a,b=_source_image_span(pack,m)
            self.assertEqual(b-a,m['image_bytes'])
            self.assertEqual(len(decode_dxt_base(pack[a:a+m['base_image_bytes']],8,8,b'DXT5')),8*8*4)
    def test_unsorted_entries_become_sorted_index(self):
        a=entries();pack,r=_assemble_pc_dxt5_entries(list(reversed(a)))
        self.assertEqual(list(parse_pack(pack,'pc')['records']),[ONE,TWO])
    def test_duplicate_hash_rejected(self):
        e=entries();e[1]=(ONE,)+e[1][1:]
        with self.assertRaisesRegex(ValueError,'Duplicate'):_assemble_pc_dxt5_entries(e)
    def test_invalid_hash_rejected(self):
        e=entries();e[1]=(0,)+e[1][1:]
        with self.assertRaisesRegex(ValueError,'invalid'):_assemble_pc_dxt5_entries(e)
    def test_bool_hash_rejected(self):
        e=entries();e[1]=(True,)+e[1][1:]
        with self.assertRaisesRegex(ValueError,'invalid'):_assemble_pc_dxt5_entries(e)
    def test_short_dxt5_payload_rejected(self):
        e=entries();e[0]=e[0][:5]+(e[0][5][:-1],)
        with self.assertRaisesRegex(ValueError,'mip equation'):_assemble_pc_dxt5_entries(e)
    def test_bytes_payload_type_required(self):
        e=entries();e[0]=e[0][:5]+(bytearray(e[0][5]),)
        with self.assertRaisesRegex(ValueError,'mip equation'):_assemble_pc_dxt5_entries(e)
    def test_wrong_mip_count_rejected(self):
        e=entries();e[0]=e[0][:4]+(0,)+e[0][5:]
        with self.assertRaisesRegex(ValueError,'mip'):_assemble_pc_dxt5_entries(e)
    def test_wrong_dimensions_rejected(self):
        e=entries();e[0]=e[0][:2]+(7,)+e[0][3:]
        with self.assertRaisesRegex(ValueError,'dimensions'):_assemble_pc_dxt5_entries(e)
    def test_empty_entries_rejected(self):
        with self.assertRaisesRegex(ValueError,'count'):_assemble_pc_dxt5_entries([])
    def test_tuple_shape_rejected(self):
        with self.assertRaisesRegex(ValueError,'tuple'):_assemble_pc_dxt5_entries([(ONE,b'A')])
    def test_packed_name_preserved(self):
        pack,_=_assemble_pc_dxt5_entries(entries())
        self.assertEqual(parse_pack(pack,'pc')['records'][TWO]['name'],b'SYNTH_SECOND')
    def test_no_source_meta_names_in_public_report(self):
        _,r=_assemble_pc_dxt5_entries(entries())
        self.assertNotIn('SYNTH_',str(r))
        self.assertNotIn(str(ONE),str(r))


class SourceBridgeTests(unittest.TestCase):
    def test_8bit_source_two_images(self):
        data,r=build_private_dxt5_candidate(ps2(bits=8),mip_levels=3)
        self.assertEqual((r['source_donors_converted'],r['pc_candidate_texture_identities']),(2,2))
        self.assertEqual(list(parse_pack(data,'pc')['records']),[ONE,TWO])
        self.assertEqual(r['source_indexed_bits'],{8:2})
    def test_4bit_source_two_images(self):
        data,r=build_private_dxt5_candidate(ps2(bits=4),mip_levels=4)
        self.assertEqual(r['source_indexed_bits'],{4:2})
        self.assertEqual(r['pc_candidate_mip_level_counts'],{4:2})
    def test_8bit_source_transparent_alpha(self):
        p=bytearray(ps2(bits=8))
        # Different palette alpha in source: independent candidate decoder.
        from texture_pixel_base_alignment import _chunks
        root=_chunks(p,8,8+struct.unpack_from('<I',p,4)[0]);pix=_chunks(p,root[3][1],root[3][2]);base=pix[2][1]+(-pix[2][1]%128)
        p[base+7]=40
        data,r=build_private_dxt5_candidate(bytes(p),mip_levels=2)
        m=parse_pack(data,'pc')['records'][ONE];start,end=_source_image_span(data,m)
        rgba=decode_dxt_base(data[start:start+m['base_image_bytes']],8,8,b'DXT5')
        self.assertTrue(any(a!=255 for a in rgba[3::4]))
    def test_used_id_absence_is_explicit(self):
        data,r=build_private_dxt5_candidate(ps2(),{ONE,TWO,THREE},mip_levels=3)
        self.assertEqual(r['source_material_ids_absent_from_this_pack'],1)
        self.assertFalse(r['complete_material_identity_coverage'])
        self.assertEqual(len(parse_pack(data,'pc')['records']),2)
    def test_full_used_coverage_only_for_all_requested(self):
        _,r=build_private_dxt5_candidate(ps2(),{ONE,TWO},mip_levels=3)
        self.assertTrue(r['complete_material_identity_coverage'])
    def test_select_only_one_material_image(self):
        data,r=build_private_dxt5_candidate(ps2(),{ONE,THREE},mip_levels=2)
        self.assertEqual(list(parse_pack(data,'pc')['records']),[ONE])
        self.assertEqual((r['source_donors_converted'],r['source_material_ids_absent_from_this_pack']),(1,1))
    def test_partial_batch_explicitly_marked(self):
        data,r=build_private_dxt5_candidate(ps2(),{ONE,TWO},mip_levels=2,max_textures=1)
        self.assertTrue(r['partial_ordinal_batch'])
        self.assertFalse(r['complete_material_identity_coverage'])
        self.assertEqual(len(parse_pack(data,'pc')['records']),1)
    def test_invalid_mip_count_refused(self):
        for v in (0,17,True,2.5):
            with self.subTest(v=v),self.assertRaisesRegex(ValueError,'mip'):
                build_private_dxt5_candidate(ps2(),mip_levels=v)
    def test_invalid_limit_refused(self):
        for v in (0,513,True,1.0):
            with self.subTest(v=v),self.assertRaisesRegex(ValueError,'max'):
                build_private_dxt5_candidate(ps2(),max_textures=v)
    def test_no_matching_material_refused(self):
        with self.assertRaisesRegex(ValueError,'No source'):
            build_private_dxt5_candidate(ps2(),{THREE})
    def test_corrupt_input_refused(self):
        with self.assertRaises(ValueError):build_private_dxt5_candidate(b'corrupt')
    def test_reproducible_identical_candidate_bytes(self):
        a,_=build_private_dxt5_candidate(ps2(),mip_levels=2)
        b,_=build_private_dxt5_candidate(ps2(),mip_levels=2)
        self.assertEqual(a,b)
    def test_report_never_claims_runtime_registration(self):
        _,r=build_private_dxt5_candidate(ps2(),mip_levels=2)
        self.assertEqual(r['runtime_registration'],'UNVERIFIED')
        self.assertFalse(r['safe_for_direct_game_install'])


if __name__=='__main__':unittest.main()
