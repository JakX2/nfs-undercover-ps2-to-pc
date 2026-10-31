"""V61 asset-free embedded ROOT inventory regression tests (+ optional pinned Wii)."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v61_root_candidate_inventory as m

WII_SHA='cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'


def digest(b):return hashlib.sha256(b).hexdigest()


def child(tag,data,endian='<'):
    return struct.pack(endian+'II',tag,len(data))+data


def root(seed=1,endian='<',scenery=True,children=None):
    if children is None:
        children=([child(m.SCENE,struct.pack(endian+'I',seed),endian),
                   child(m.INSTANCE,b'X'*96,endian)] if scenery
                  else [child(0x999, b'F'*8, endian)])
    b=b''.join(children)
    return struct.pack(endian+'II',m.ROOT,len(b))+b


class V61Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.a=root(11);self.b=root(22)
        self.src=b'P'*64+self.a+b'Q'*32+self.b+b'Z'*16
        self.source=self.dir/'world.bin'
        self.source.write_bytes(self.src)

    def audit(self,**kw):
        return m.audit_file(self.source,expected_sha256=digest(self.source.read_bytes()),endian='little',**kw)

    def test_two_nested_in_envelope(self):
        x=self.audit()
        self.assertEqual(x['valid_candidate_root_count'],2)
        self.assertEqual(x['scenery_direct_TLV_candidate_count'],2)
        self.assertEqual(x['candidate_roots'][0]['offset'],64)
        self.assertEqual(x['candidate_roots'][1]['offset'],64+len(self.a)+32)
        self.assertEqual(x['distinct_candidate_root_byte_hashes'],2)
        self.assertTrue(x['scan_complete_within_window'])

    def test_shortlist_roundtrip_to_existing_v60_index_gate(self):
        # The index table is entirely SYNTHETIC.  This checks interoperability,
        # not Carbon's actual 0x34110 layout or loader behavior.
        import importlib
        v60_dir=Path(__file__).resolve().parents[1] / 'v60'
        sys.path.insert(0,str(v60_dir))
        v60=importlib.import_module('v60_multi_anchor_index_gate')
        scan=self.audit()
        anchors=scan['v60_anchor_shortlist_unverified_provenance']
        row=bytearray(3*92)
        struct.pack_into('<I',row,92+20,anchors[0]['offset'])
        struct.pack_into('<I',row,2*92+20,anchors[1]['offset'])
        master=b'Z'*24+struct.pack('<II',0x34110,len(row))+row
        master_file=self.dir/'synthetic_master.bin'
        master_file.write_bytes(master)
        manifest={
            'stream': {'path':str(self.source),'expected_file_sha256':digest(self.src),'endian':'little'},
            'master': {'path':str(master_file),'expected_file_sha256':digest(master),
                       'chunk_header_offset':24,'endian':'little'},
            'roots': anchors,
            'hypotheses': [{'id':'synthetic_92_at_20','row_stride':92,'row_count':3,'offset_field':20}],
        }
        result=v60.evaluate_layouts(manifest)
        self.assertEqual(result['candidate_layouts'][0]['structural_status'],
                         'multiple_distinct_roots_structurally_match_NOT_loader_proof')
        self.assertFalse(result['carbon_PC_master_index_semantics_proven'])
        self.assertFalse(result['safe_to_install'])

    def test_absolute_child_offsets(self):
        x=self.audit()['candidate_roots'][0]
        self.assertEqual(x['children'][0]['payload_offset_in_root'],16)
        self.assertEqual(x['children'][1]['payload_offset_in_root'],28)
        self.assertEqual(x['children'][0]['bytes'],4)
        self.assertEqual(x['children'][1]['bytes'],96)

    def test_shortlist_is_v60_anchor_shape(self):
        a=self.audit()['v60_anchor_shortlist_unverified_provenance']
        self.assertEqual(len(a),2)
        self.assertEqual(a[0]['offset'],64)
        self.assertEqual(a[0]['expected_root_sha256'],digest(self.a))
        self.assertEqual(set(a[0]),{'label','offset','expected_root_sha256'})

    def test_distinct_sha_does_not_approve_install(self):
        r=self.audit()
        self.assertFalse(r['source_provenance_authenticated_by_file_hash_alone'])
        self.assertFalse(r['carbon_PC_root_or_master_schema_proven'])
        self.assertFalse(r['native_loader_or_relocations_verified'])
        self.assertFalse(r['safe_to_install'])

    def test_duplicate_bytes_are_one_shortlist_anchor(self):
        self.source.write_bytes(b'P'*64+self.a+b'Q'*32+self.a)
        x=self.audit()
        self.assertEqual(x['valid_candidate_root_count'],2)
        self.assertEqual(x['distinct_candidate_root_byte_hashes'],1)
        self.assertEqual(len(x['repeated_identical_candidate_roots']),1)
        self.assertEqual(len(x['v60_anchor_shortlist_unverified_provenance']),1)

    def test_unknown_children_not_asserted_invalid_carbon(self):
        other=root(scenery=False)
        self.source.write_bytes(other)
        x=self.audit()
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['classification'],'other_direct_TLV_candidate')
        self.assertFalse(x['v60_anchor_shortlist_unverified_provenance'])

    def test_missing_required_scenery_child_classified_other(self):
        self.source.write_bytes(root(children=[child(m.SCENE,b'0000')]))
        self.assertEqual(self.audit()['candidate_roots'][0]['classification'],'other_direct_TLV_candidate')

    def test_empty_scenery_identifier_classified_other(self):
        self.source.write_bytes(root(children=[child(m.SCENE,b''),child(m.INSTANCE,b'')]))
        self.assertEqual(self.audit()['candidate_roots'][0]['classification'],'other_direct_TLV_candidate')

    def test_malformed_child_length_never_shortlisted(self):
        b=child(m.SCENE,b'')+struct.pack('<II',m.INSTANCE,999999)
        self.source.write_bytes(struct.pack('<II',m.ROOT,len(b))+b)
        x=self.audit()
        self.assertEqual(x['rejected_unparsed_direct_TLV'],1)
        self.assertEqual(x['valid_candidate_root_count'],0)

    def test_nested_child_high_bit_fails_tlv(self):
        self.source.write_bytes(root(children=[child(0x80000001,b'abcd')]))
        self.assertEqual(self.audit()['rejected_unparsed_direct_TLV'],1)

    def test_duplicate_child_id_fails_tlv(self):
        self.source.write_bytes(root(children=[child(m.SCENE,b'aaaa'),child(m.SCENE,b'bbbb')]))
        self.assertEqual(self.audit()['rejected_unparsed_direct_TLV'],1)

    def test_empty_root_frame_rejected(self):
        self.source.write_bytes(struct.pack('<II',m.ROOT,0))
        self.assertEqual(self.audit()['rejected_invalid_frame'],1)

    def test_oversize_root_frame_rejected(self):
        self.source.write_bytes(struct.pack('<II',m.ROOT,m.MAX_ROOT_BYTES+1))
        self.assertEqual(self.audit()['rejected_invalid_frame'],1)

    def test_truncated_root_frame_rejected(self):
        self.source.write_bytes(struct.pack('<II',m.ROOT,200)+b'0'*6)
        self.assertEqual(self.audit()['rejected_invalid_frame'],1)

    def test_truncated_child_header_rejected(self):
        self.source.write_bytes(root(children=[child(m.SCENE,b'0000'),b'X']))
        self.assertEqual(self.audit()['rejected_unparsed_direct_TLV'],1)

    def test_big_endian_frame(self):
        blob=root(11,endian='>')
        self.source.write_bytes(blob)
        x=m.audit_file(self.source,expected_sha256=digest(blob),endian='big')
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['root_sha256'],digest(blob))

    def test_wrong_endian_rejects_all(self):
        self.assertEqual(m.audit_file(self.source,expected_sha256=digest(self.src),endian='big')['valid_candidate_root_count'],0)

    def test_search_window_limits_starts_not_frame_ends(self):
        x=self.audit(start_offset=64,stop_offset=67)
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['root_sha256'],digest(self.a))

    def test_scan_window_excludes_first(self):
        x=self.audit(start_offset=65)
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['root_sha256'],digest(self.b))

    def test_candidate_limit_declares_truncation(self):
        x=self.audit(max_candidates=1)
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertFalse(x['scan_complete_within_window'])
        self.assertEqual(x['candidate_limit'],1)

    def test_limit_of_exact_number_is_complete(self):
        self.assertTrue(self.audit(max_candidates=2)['scan_complete_within_window'])

    def test_marker_hit_without_frame_counted(self):
        self.source.write_bytes(self.a+b'XXX'+struct.pack('<II',m.ROOT,70000000))
        x=self.audit()
        self.assertEqual(x['marker_hits_examined'],2)
        self.assertEqual(x['rejected_invalid_frame'],1)

    def test_nested_valid_root_overlap_flag(self):
        inner=root(33)
        outer=root(44,children=[child(m.SCENE,b'ABCD'),child(m.INSTANCE,inner)])
        self.source.write_bytes(outer)
        x=self.audit()
        self.assertEqual(x['valid_candidate_root_count'],2)
        self.assertEqual(len(x['overlapping_root_candidates']),1)
        self.assertEqual(x['overlapping_root_candidates'][0]['overlaps_offset'],0)

    def test_many_children_bounded(self):
        children=[child(0x50000+i,b'') for i in range(m.MAX_CHILDREN+1)]
        self.source.write_bytes(root(children=children))
        self.assertEqual(self.audit()['rejected_unparsed_direct_TLV'],1)

    def test_sha_guard_rejects_other_file(self):
        with self.assertRaises(m.InventoryError):
            m.audit_file(self.source,expected_sha256='0'*64,endian='little')

    def test_no_bare_filename_leak(self):
        rep=json.dumps(self.audit())
        self.assertNotIn(str(self.dir),rep)
        self.assertNotIn(self.source.name,rep)
        self.assertNotIn('P'*64,rep)

    def test_empty_file_supported(self):
        self.source.write_bytes(b'')
        self.assertEqual(self.audit()['valid_candidate_root_count'],0)

    def test_invalid_integer_rejects_bool(self):
        for kw in ({'start_offset':True},{'max_candidates':True},{'stop_offset':True},
                   {'start_offset':-1},{'max_candidates':0},{'max_candidates':m.MAX_CANDIDATES+1},
                   {'stop_offset':len(self.src)+1},{'start_offset':25,'stop_offset':24}):
            with self.subTest(kw=kw),self.assertRaises(m.InventoryError):
                self.audit(**kw)

    def test_invalid_sha_and_endian(self):
        for sha in ('oops','z'*64,11):
            with self.subTest(sha=sha),self.assertRaises(m.InventoryError):
                m.audit_file(self.source,expected_sha256=sha,endian='little')
        with self.assertRaises(m.InventoryError):
            m.audit_file(self.source,expected_sha256=digest(self.src),endian='middle')

    def test_source_file_hashed_once(self):
        with mock.patch.object(m,'file_sha256',wraps=m.file_sha256) as spy:
            self.audit()
        self.assertEqual(spy.call_count,1)

    def test_cli_new_report_and_source_unchanged(self):
        out=self.dir/'report.json';old=self.source.read_bytes()
        command=[sys.executable,str(Path(m.__file__)),'--source',str(self.source),
                 '--expected-file-sha256',digest(old),'--endian','little','--report',str(out)]
        p=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(out.read_text())['valid_candidate_root_count'],2)
        self.assertEqual(self.source.read_bytes(),old)
        p2=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(p2.returncode,0)

    def test_cli_refuses_output_over_source(self):
        data=self.source.read_bytes()
        command=[sys.executable,str(Path(m.__file__)),'--source',str(self.source),
                 '--expected-file-sha256',digest(data),'--endian','little','--report',str(self.source)]
        p=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(self.source.read_bytes(),data)

    def test_cli_hex_search_offsets(self):
        out=self.dir/'report.json'
        p=subprocess.run([sys.executable,str(Path(m.__file__)),'--source',str(self.source),
             '--expected-file-sha256',digest(self.src),'--endian','little',
             '--start-offset','0x40','--stop-offset','0x44','--report',str(out)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(out.read_text())['valid_candidate_root_count'],1)


class V61PinnedWiiFixtureTests(unittest.TestCase):
    def setUp(self):
        source=os.environ.get('NFS_UC_WII_SCENE')
        if not source:self.skipTest('original Wii scene not supplied in public CI')
        self.blob=Path(source).read_bytes()
        if digest(self.blob)!=WII_SHA:self.skipTest('not the exact original Wii RedBuilding ROOT')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.path=self.base/'embedded_world'
        self.offset=2048
        self.path.write_bytes(b'P'*self.offset+self.blob+b'Z'*200)

    def test_exact_source_original_root_scanned(self):
        x=m.audit_file(self.path,expected_sha256=digest(self.path.read_bytes()),endian='little')
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['offset'],self.offset)
        self.assertEqual(x['candidate_roots'][0]['root_sha256'],WII_SHA)
        self.assertEqual(x['candidate_roots'][0]['root_bytes'],8488)

    def test_original_chunk_order_reported_without_semantics(self):
        x=m.audit_file(self.path,expected_sha256=digest(self.path.read_bytes()),endian='little')
        c=x['candidate_roots'][0]
        self.assertEqual([v['id'] for v in c['children']],
                         ['0x34101','0x34103','0x34102','0x3410D','0x34105','0x34107'])
        self.assertFalse(x['carbon_PC_root_or_master_schema_proven'])

    def test_original_source_duplicated_not_independent(self):
        raw=self.blob+self.blob
        self.path.write_bytes(raw)
        x=m.audit_file(self.path,expected_sha256=digest(raw),endian='little')
        self.assertEqual(x['valid_candidate_root_count'],2)
        self.assertEqual(x['distinct_candidate_root_byte_hashes'],1)
        self.assertEqual(len(x['v60_anchor_shortlist_unverified_provenance']),1)

    def test_original_source_window_and_hash(self):
        x=m.audit_file(self.path,expected_sha256=digest(self.path.read_bytes()),
                       endian='little',start_offset=self.offset,stop_offset=self.offset+4)
        self.assertEqual(x['valid_candidate_root_count'],1)
        self.assertEqual(x['candidate_roots'][0]['root_sha256'],WII_SHA)


if __name__=='__main__':unittest.main()