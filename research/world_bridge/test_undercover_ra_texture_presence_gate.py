"""Synthetic-only original track RA/RB image-presence regression controls."""
import os
import sys
from types import SimpleNamespace
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import zipfile

import undercover_ra_texture_presence_gate as gate


def ch(cid, payload=b''):
    return struct.pack('<II', cid, len(payload)) + payload


def image_pack(h):
    assert 0 < h <= 0xffffffff
    meta = bytearray(92)
    struct.pack_into('<I', meta, 12, h)
    struct.pack_into('<IIIII', meta, 20, 0, 8, 8, 64, 8)
    struct.pack_into('<HH', meta, 40, 4, 4)
    meta[44:48] = bytes((2, 2, 4, 0))
    struct.pack_into('<H', meta, 48, 16)
    meta[50],meta[51],meta[88] = 1,0,3
    meta[89:92] = b'X\0\0'
    desc = (ch(0x33310001,bytes(124)) +
            ch(0x33310002,struct.pack('<II',h,0)) +
            ch(0x33310004,bytes(meta)) +
            ch(0x33310005,bytes(84)))
    before = ch(0) + ch(0xB3310000,desc) + ch(0)
    pixprefix = ch(0x33320001,bytes(24)) + ch(0)
    origin = 8 + len(before) + 8 + len(pixprefix) + 8
    padding = (-origin)%128
    pixels = b'\x11'*padding + bytes(8) + bytes(64)
    root = ch(gate.TEXTURE_ROOT,before + ch(0xB3320000,pixprefix + ch(0x33320002,pixels)))
    parsed = gate.validated_texture_ids(root)
    assert parsed == frozenset((h,))
    return root


def row(section, off, length):
    out = bytearray(92)
    out[:4]=b'Y0\0\0'
    struct.pack_into('<h',out,8,section)
    struct.pack_into('<II',out,20,off,length)
    return bytes(out)


def bun(rows):
    return ch(0x34110,b''.join(row(*x) for x in rows))


def fixture_zip(tmp, ra_ids=(201,), rb_id=101, dyn=b''):
    # Keep independent original sections at valid 2048 boundaries.
    ra_roots=[image_pack(i) for i in ra_ids]
    ra_stream=bytearray(2048*len(ra_roots))
    ra_rows=[]
    for i,root in enumerate(ra_roots):
        off=2048*i;ra_stream[off:off+len(root)]=root
        ra_rows.append((142+i,off,len(root)))
    rb_root=image_pack(rb_id)
    rb_stream=bytearray(4096)
    rb_stream[:len(rb_root)]=rb_root
    rb_stream[2048:2048+len(rb_root)]=rb_root
    rb_rows=[(241,0,len(rb_root)),(3401,2048,len(rb_root))]
    path=Path(tmp)/'PRIVATE_original_fixture.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('TRACKS/L2RA.BUN',bun(ra_rows))
        z.writestr('TRACKS/STREAML2RA.BUN',bytes(ra_stream))
        z.writestr('TRACKS/L2RB.BUN',bun(rb_rows))
        z.writestr('TRACKS/STREAML2RB.BUN',bytes(rb_stream))
        z.writestr('TRACKS/LOC2DYNTEX.BIN',dyn)
    return path


class TextureRootValidation(unittest.TestCase):
    def setUp(self):self.root=image_pack(17)
    def test_original_ps2_root_accepted(self):self.assertEqual(gate.validated_texture_ids(self.root),frozenset({17}))
    def test_bad_root_id_rejected(self):
        b=bytearray(self.root);b[2]=0
        with self.assertRaises(ValueError):gate.validated_texture_ids(bytes(b))
    def test_wrong_declared_length_rejected(self):
        b=bytearray(self.root);struct.pack_into('<I',b,4,len(b))
        with self.assertRaises(ValueError):gate.validated_texture_ids(bytes(b))
    def test_zero_hash_rejected(self):
        with self.assertRaises(AssertionError):image_pack(0)
    def test_negative_hash_rejected(self):
        with self.assertRaises(AssertionError):image_pack(-1)
    def test_non_bytes_rejected(self):
        with self.assertRaises(ValueError):gate.validated_texture_ids(bytearray(self.root))
    def test_short_root_rejected(self):
        with self.assertRaises(ValueError):gate.validated_texture_ids(self.root[:20])
    def test_truncated_image_rejected(self):
        with self.assertRaises(ValueError):gate.validated_texture_ids(self.root[:-10])
    def test_bad_pixel_alignment_rejected(self):
        b=bytearray(self.root)
        a=b.find(b'\x11'*8)
        self.assertGreater(a,0)
        b[a]=0
        with self.assertRaises(ValueError):gate.validated_texture_ids(bytes(b))
    def test_bad_platform_stride_rejected(self):
        b=bytearray(self.root)
        pos=b.find(struct.pack('<I',0x33310005))
        self.assertGreater(pos,0)
        struct.pack_into('<I',b,pos+4,20)
        with self.assertRaises(ValueError):gate.validated_texture_ids(bytes(b))


class SectionRowValidation(unittest.TestCase):
    def test_good_rows_sorted(self):
        rows,ids=gate.parse_stream_section_rows(bun(((12,2048,64),(11,0,100))),4096)
        self.assertEqual([r[2] for r in rows],[11,12]);self.assertEqual(ids[12],(2048,2112))
    def test_duplicate_sections_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,50),(11,2048,50))),4096)
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,2600),(12,2048,50))),4096)
    def test_out_of_bounds_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,2048,3000),)),4096)
    def test_misaligned_offset_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,4,50),)),4096)
    def test_truncated_rows_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(ch(0x34110,bytes(91)),4096)
    def test_missing_table_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(ch(0x1234),4096)
    def test_multiple_tables_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,50),))*2,4096)
    def test_wrong_total_bundle_size_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,50),))[:-2],4096)
    def test_zero_section_length_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,0),)),4096)
    def test_invalid_stream_length_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bun(((11,0,50),)),0)
    def test_invalid_bundle_type_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(bytearray(bun(((11,0,50),))),4096)
    def test_too_many_rows_rejected(self):
        with self.assertRaises(ValueError):gate.parse_stream_section_rows(ch(0x34110,bytes(92*(gate.MAX_SECTIONS+1))),8192)


class RAIndexEnumeration(unittest.TestCase):
    def test_two_root_sections_found(self):
        a=image_pack(11);b=image_pack(22)
        stream=bytearray(4096);stream[:len(a)]=a;stream[2048:2048+len(b)]=b
        rows=((0,len(a),141),(2048,2048+len(b),142))
        summary=gate.enumerate_ra_texture_indexes(bytes(stream),rows)
        self.assertEqual(summary['fully_validated_image_roots'],2)
        self.assertEqual(summary['roots_contained_in_declared_ra_stream_rows'],2)
        self.assertEqual(summary['declared_section_ra_ids'],frozenset((11,22)))
    def test_validated_unassigned_gap_classified_separately(self):
        root=image_pack(44)
        stream=bytearray(4096);stream[1024:1024+len(root)]=root
        summary=gate.enumerate_ra_texture_indexes(bytes(stream),((0,32,141),))
        self.assertEqual(summary['fully_validated_image_roots'],1)
        self.assertEqual(summary['roots_not_contained_in_declared_stream_rows'],1)
        self.assertFalse(summary['declared_section_ra_ids'])
    def test_invalid_fake_root_not_promoted(self):
        raw=bytearray(4096);raw[:8]=struct.pack('<II',gate.TEXTURE_ROOT,512)
        result=gate.enumerate_ra_texture_indexes(bytes(raw),((0,2048,1),))
        self.assertEqual(result['fully_validated_image_roots'],0)
        self.assertEqual(result['candidate_markers_examined'],1)
    def test_4byte_magic_inside_payload_not_new_resource(self):
        root=image_pack(55)
        stream=bytearray(4096);stream[:len(root)]=root
        # Put fake root marker into gap but without valid framing.
        stream[1024:1028]=struct.pack('<I',gate.TEXTURE_ROOT)
        result=gate.enumerate_ra_texture_indexes(bytes(stream),((0,len(root),141),))
        self.assertEqual(result['fully_validated_image_roots'],1)
    def test_bad_root_order_rejected(self):
        with self.assertRaises(ValueError):gate.enumerate_ra_texture_indexes(bytes(2048),((100,200,4),(0,50,5)))
    def test_overlapping_input_rows_rejected(self):
        with self.assertRaises(ValueError):gate.enumerate_ra_texture_indexes(bytes(2048),((0,200,4),(128,256,5)))
    def test_empty_stream_rejected(self):
        with self.assertRaises(ValueError):gate.enumerate_ra_texture_indexes(b'',((0,10,5),))
    def test_empty_row_table_rejected(self):
        with self.assertRaises(ValueError):gate.enumerate_ra_texture_indexes(bytes(2048),())
    def test_oversize_frame_skipped(self):
        b=bytearray(2048);struct.pack_into('<II',b,0,gate.TEXTURE_ROOT,gate.MAX_PACK)
        result=gate.enumerate_ra_texture_indexes(bytes(b),((0,100,1),))
        self.assertEqual(result['fully_validated_image_roots'],0)
    def test_nested_overlap_failclosed(self):
        a=image_pack(11)
        def fake_validate(root):return frozenset((11,))
        b=bytearray(4096)
        b[:len(a)]=a
        # If an overlapping marker exists, scanner advances to end of the
        # earlier validated root, never counting opaque interior as a resource.
        b[80:84]=struct.pack('<I',gate.TEXTURE_ROOT)
        with mock.patch.object(gate,'validated_texture_ids',fake_validate):
            x=gate.enumerate_ra_texture_indexes(bytes(b),((0,2048,1),))
        self.assertEqual(x['fully_validated_image_roots'],1)


class IdentityReconciliation(unittest.TestCase):
    @staticmethod
    def summary(ra=(3,),bounded=(3,)):
        return {'all_validated_ra_ids':frozenset(ra),
                'declared_section_ra_ids':frozenset(bounded),
                'candidate_markers_examined':2,'fully_validated_image_roots':2,
                'roots_contained_in_declared_ra_stream_rows':1,
                'roots_not_contained_in_declared_stream_rows':1}
    def test_ra_resolves_only_missing_rb_id(self):
        report=gate.reconcile_image_presence({241:{1,2,3},3401:{1,2}},
                 {241:{1,2},3401:{1,2}},self.summary())
        self.assertEqual(report['distinct_material_ids_absent_from_rb_image_indexes'],1)
        self.assertEqual(report['missing_rb_ids_resolved_in_declared_ra_texture_roots'],1)
        self.assertTrue(report['all_used_ids_within_examined_ra_or_rb_image_indexes'])
    def test_unassigned_root_is_not_source_section_registration(self):
        r=gate.reconcile_image_presence({241:{1,2},3401:{1}},
                     {241:{1},3401:{1}},self.summary((2,3),(3,)))
        self.assertEqual(r['missing_rb_ids_found_only_in_unassigned_ra_root_frames'],1)
        self.assertFalse(r['all_used_ids_within_examined_ra_or_rb_image_indexes'])
    def test_genuinely_unresolved_count(self):
        r=gate.reconcile_image_presence({241:{1,2,3},3401:{1,2}},
                     {241:{1},3401:{1}},self.summary((9,),(9,)))
        self.assertEqual(r['missing_rb_ids_not_in_any_validated_ra_texture_root'],2)
    def test_overlapping_ra_and_rb_not_double_counted(self):
        r=gate.reconcile_image_presence({241:{1,3},3401:{1,3}},
                     {241:{1},3401:{1}},self.summary((1,3),(1,3)))
        self.assertEqual(r['missing_rb_ids_resolved_in_declared_ra_texture_roots'],1)
    def test_deduplicate_two_source_sections(self):
        r=gate.reconcile_image_presence({241:{1,2},3401:{1,2}},
                     {241:{1},3401:{1}},self.summary((9,),(9,)))
        self.assertEqual(r['distinct_used_undercover_rb_scenery_material_ids'],2)
    def test_missing_source_section_rejected(self):
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{1}},{241:{1}},self.summary())
    def test_zero_identity_rejected(self):
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{0},3401:{1}},{241:{1},3401:{1}},self.summary())
    def test_string_identity_rejected(self):
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{'1'},3401:{1}},{241:{1},3401:{1}},self.summary())
    def test_no_ra_validated_images_rejected(self):
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{1},3401:{1}},{241:{1},3401:{1}},self.summary((),()))
    def test_bounded_ra_not_subset_rejected(self):
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{1},3401:{1}},{241:{1},3401:{1}},self.summary((5,),(9,)))
    def test_incoherent_root_count_rejected(self):
        s=self.summary();s['fully_validated_image_roots']=3
        with self.assertRaises(ValueError):gate.reconcile_image_presence({241:{1},3401:{1}},{241:{1},3401:{1}},s)
    def test_report_has_no_hash_inventory(self):
        r=gate.reconcile_image_presence({241:{1,2},3401:{1}},
                     {241:{1},3401:{1}},self.summary((2,),(2,)))
        self.assertTrue(all(not isinstance(v,(set,frozenset,bytes)) for v in r.values()))
        self.assertFalse(any('source_path' in k for k in r))
    def test_absence_from_ra_does_not_claim_global_absence(self):
        r=gate.reconcile_image_presence({241:{1,2},3401:{1}},
                     {241:{1},3401:{1}},self.summary((5,),(5,)))
        self.assertTrue(r['other_original_resource_archives_or_special_material_semantics_still_unchecked'])
        self.assertEqual(r['carbon_pc_runtime_registration'],'NOT_TESTED')


class OriginalPrivateZipWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=fixture_zip(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_full_zip_harness_private_material_source_mock(self):
        before=self.path.read_bytes()
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            r=gate.audit_original_undercover_archive(self.path)
        self.assertEqual(r['missing_rb_ids_resolved_in_declared_ra_texture_roots'],1)
        self.assertEqual(r['original_ra_declared_stream_sections'],1)
        self.assertTrue(r['owner_original_zip_crc_verified'])
        self.assertEqual(self.path.read_bytes(),before)
    def test_non_original_extra_file_not_read(self):
        with zipfile.ZipFile(self.path,'a') as z:z.writestr('MALICIOUS_EXTRA.TXT','do not execute')
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            r=gate.audit_original_undercover_archive(self.path)
        self.assertEqual(r['missing_rb_ids_not_in_any_validated_ra_texture_root'],0)
    def test_symlink_archive_rejected(self):
        q=Path(self.tmp.name)/'symlink.zip'
        try:q.symlink_to(self.path)
        except OSError:self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):gate._owner_archive(q)
    def test_missing_archive_rejected(self):
        with self.assertRaises(ValueError):gate._owner_archive(Path(self.tmp.name)/'no.zip')
    def test_archive_source_change_detected(self):
        count=0
        original=gate._fingerprint
        def mutated(path):
            nonlocal count
            count+=1
            if count==2:return (0,0,b'not same')
            return original(path)
        with mock.patch.object(gate,'_fingerprint',side_effect=mutated):
            with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
                with self.assertRaises(ValueError):gate.audit_original_undercover_archive(self.path)
    def test_missing_dynamic_member_fails_closed(self):
        other=Path(self.tmp.name)/'missing_dynamic.zip'
        with zipfile.ZipFile(self.path) as source,zipfile.ZipFile(other,'w') as target:
            for row in source.infolist():
                if row.filename != 'TRACKS/LOC2DYNTEX.BIN':target.writestr(row,source.read(row))
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            with self.assertRaises(KeyError):gate.audit_original_undercover_archive(other)
    def test_missing_one_rb_section_fails_closed(self):
        other=Path(self.tmp.name)/'bad_rb_sections.zip'
        with zipfile.ZipFile(self.path) as source,zipfile.ZipFile(other,'w') as target:
            for row in source.infolist():
                data=source.read(row)
                if row.filename=='TRACKS/L2RB.BUN':data=bun(((241,0,len(image_pack(101))),))
                target.writestr(row,data)
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            with self.assertRaises(ValueError):gate.audit_original_undercover_archive(other)
    def test_private_zip_does_not_write_sidecars(self):
        before=set(Path(self.tmp.name).iterdir())
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            gate.audit_original_undercover_archive(self.path)
        self.assertEqual(before,set(Path(self.tmp.name).iterdir()))
    def test_dynamic_entry_can_be_nonempty(self):
        p=fixture_zip(self.tmp.name,dyn=b'PRIVATE_FIXTURE')
        with mock.patch.object(gate,'used_material_ids_from_original_rb',return_value=frozenset((101,201))):
            result=gate.audit_original_undercover_archive(p)
        self.assertFalse(result['dynamic_texture_entry_zero_bytes'])


class ExistingSourceMaterialExtraction(unittest.TestCase):
    """Integration contract against the previously committed pack/mesh readers."""
    @staticmethod
    def source_with(index=1, hashes=(101, 201), ns=1):
        rows = bytearray(4+16*ns)
        for i in range(ns):struct.pack_into('<b',rows,4+16*i+14,index)
        return (((123,bytes(28),hashes,[(0x134A01, bytes(rows))]),),)

    def run_with_mocks(self, packs, triangles=1):
        fake_part=SimpleNamespace(source_partition_roots=lambda s:packs)
        fake_mesh=SimpleNamespace(PS2_STRIPS=0x134A01,
            parse_ps2_mesh=lambda children:{'strip_entries':triangles})
        with mock.patch.dict(sys.modules,{
            'undercover_pc_partition_registry_gate':fake_part,
            'mesh_topology_control':fake_mesh,
        }):
            return gate.used_material_ids_from_original_rb(bytes(128))

    def test_used_indices_resolved_by_private_table(self):
        self.assertEqual(self.run_with_mocks(self.source_with()),frozenset((201,)))
    def test_no_materials_refused(self):
        with self.assertRaises(ValueError):self.run_with_mocks(())
    def test_negative_strip_material_index_refused(self):
        with self.assertRaises(ValueError):self.run_with_mocks(self.source_with(index=-1))
    def test_index_equal_to_table_length_refused(self):
        with self.assertRaises(ValueError):self.run_with_mocks(self.source_with(index=2))
    def test_strip_record_count_disagreement_refused(self):
        with self.assertRaises(ValueError):self.run_with_mocks(self.source_with(),triangles=2)
    def test_duplicate_material_hash_deduplicated(self):
        a=self.source_with(index=0,hashes=(100,100))
        self.assertEqual(self.run_with_mocks(a),frozenset((100,)))
    def test_cross_pack_occurrences_retained_as_material_set(self):
        a=self.source_with(index=0,hashes=(100,200))[0]
        b=self.source_with(index=1,hashes=(100,200))[0]
        self.assertEqual(self.run_with_mocks((a,b)),frozenset((100,200)))
    def test_missing_strip_chunk_refused(self):
        a=((123,bytes(28),(100,),[(0xdead,bytes(20))]),)
        with self.assertRaises(ValueError):self.run_with_mocks((a,))


if __name__=='__main__':unittest.main()
