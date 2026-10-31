"""V50 offline-format gate tests. No proprietary fixture is committed to GitHub.

Set NFS_UC_WII_SCENE to a locally extracted original 8488B Wii scene ROOT
to enable the authenticated source-level tests.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v50_scenery_index_crosscheck as m


def framed(chunks):
    payload=b''.join(struct.pack('<II',tag,len(data))+data for tag,data in chunks)
    return struct.pack('<II',m.ROOT,len(payload))+payload


def make_fixture(instances=2,aux_rows=2,prec_blocks=2):
    scene=b'\x00'*4
    # root8 + SCENE header8 + SCENE payload4 + INSTANCE header8 = 28
    # pad four bytes to align first instance to global offset32.
    rows=[]
    for i in range(instances):
        row=bytearray(96)
        struct.pack_into('<h',row,28,i % max(1,prec_blocks))
        rows.append(bytes(row))
    inst=b'\0'*4+b''.join(rows)
    aux=[]
    for i in range(aux_rows):
        aux.append(struct.pack('<8I',10*i,0,10*i+1,0,10*i+2,0,42+i,0))
    prec=b'\x00'*128 + b'\x11'*128 * (prec_blocks-1)
    return framed([(m.SCENE,scene),(m.INSTANCE,inst),(m.AUX,b''.join(aux)),(m.PRECULLER,prec)])


def mutate_child(source,tag,offset,bytes_new):
    parts=m.children_of(source)
    pos=parts[tag][0]+offset
    b=bytearray(source)
    b[pos:pos+len(bytes_new)]=bytes_new
    return bytes(b)

class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.blob=make_fixture()

    def test_basic_counts(self):
        r=m.audit(self.blob)
        self.assertEqual(r['instance_candidate_count'],2)
        self.assertEqual(r['preculler_candidate']['block_count'],2)
        self.assertEqual(r['auxiliary_candidate']['row_count'],2)

    def test_unknown_provenance(self):
        self.assertEqual(m.audit(self.blob)['source_provenance'],'unknown_root')

    def test_runtime_always_unverified(self):
        r=m.audit(self.blob)
        self.assertFalse(r['carbon_pc_serialized_layout_verified'])
        self.assertFalse(r['safe_to_install'])

    def test_aux_triad_consecutive(self):
        self.assertEqual(m.audit(self.blob)['auxiliary_candidate']['rows_with_first_three_low_32bit_words_consecutive_mod2_32'],2)

    def test_invalid_preculler_index_is_detected(self):
        b=mutate_child(self.blob,m.INSTANCE,4+28,struct.pack('<h',42))
        r=m.audit(b)
        self.assertEqual(r['preculler_candidate']['invalid_nonnegative_indices'],[42])
        self.assertFalse(r['preculler_candidate']['all_nonnegative_indices_in_range'])

    def test_negative_preculler_index_not_assumed_valid_block(self):
        b=mutate_child(self.blob,m.INSTANCE,4+28,struct.pack('<h',-1))
        r=m.audit(b)
        self.assertEqual(r['preculler_candidate']['negative_indices_histogram'],{'-1':1})

    def test_aux_highword_mutation_detected(self):
        b=mutate_child(self.blob,m.AUX,4,struct.pack('<I',15))
        self.assertEqual(m.audit(b)['auxiliary_candidate']['rows_with_four_zero_upper_32bits'],1)

    def test_aux_first_triad_mutation_detected(self):
        b=mutate_child(self.blob,m.AUX,8,struct.pack('<I',999))
        self.assertEqual(m.audit(b)['auxiliary_candidate']['rows_with_first_three_low_32bit_words_consecutive_mod2_32'],1)

    def test_size_invalid_preculler(self):
        parts=m.children_of(self.blob)
        chunks=[(tag,payload[:-1] if tag==m.PRECULLER else payload) for tag,(_off,payload) in parts.items()]
        with self.assertRaisesRegex(m.EvidenceError,'128'):
            m.audit(framed(chunks))

    def test_size_invalid_aux(self):
        parts=m.children_of(self.blob)
        chunks=[(tag,payload[:-1] if tag==m.AUX else payload) for tag,(_off,payload) in parts.items()]
        with self.assertRaisesRegex(m.EvidenceError,'32'):
            m.audit(framed(chunks))

    def test_sha_failure(self):
        with self.assertRaisesRegex(m.EvidenceError,'SHA-256 mismatch'):
            m.audit(self.blob,expected_sha256='0'*64)

    def test_duplicate_child_rejected(self):
        with self.assertRaisesRegex(m.EvidenceError,'Duplicate'):
            m.audit(framed([(m.SCENE,b'\0'*4),(m.SCENE,b'\0'*4)]))

    def test_truncated_root_rejected(self):
        with self.assertRaises(m.EvidenceError):
            m.audit(self.blob[:-1])

    def test_report_refuses_input_path(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'root.chunk';source.write_bytes(self.blob)
            p=subprocess.run([sys.executable,str(Path(m.__file__)), '--scene',str(source),'--json',str(source)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertEqual(source.read_bytes(),self.blob)

    def test_report_refuses_existing(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'root.chunk';source.write_bytes(self.blob)
            target=Path(d)/'out.json';target.write_text('ORIGINAL')
            p=subprocess.run([sys.executable,str(Path(m.__file__)), '--scene',str(source),'--json',str(target)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertEqual(target.read_text(),'ORIGINAL')

    def test_cli_reports_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'root.chunk';source.write_bytes(self.blob)
            target=Path(d)/'out.json'
            p=subprocess.run([sys.executable,str(Path(m.__file__)), '--scene',str(source),'--json',str(target)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(source.read_bytes(),self.blob)
            self.assertTrue(json.loads(target.read_text())['read_only'])

    def test_read_root_from_stream_at_offset(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'whole.bun';source.write_bytes(b'PREFIX'*4 +self.blob+b'SUFFIX')
            self.assertEqual(m.read_root(source,offset=24),self.blob)

    def test_wrong_stream_offset_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'whole.bun';source.write_bytes(b'PREFIX'*4+self.blob)
            with self.assertRaises(m.EvidenceError):m.read_root(source,offset=16)

class OriginalFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('NFS_UC_WII_SCENE')
        if not path or not Path(path).is_file():
            raise unittest.SkipTest('Original Wii scene not supplied; optional test')
        cls.scene=Path(path).read_bytes()
        if hashlib.sha256(cls.scene).hexdigest()!=m.KNOWN_WII_SHA256:
            raise unittest.SkipTest('Provided file not the pinned original Wii fixture')
        cls.report=m.audit(cls.scene,expected_sha256=m.KNOWN_WII_SHA256)

    def test_all_24_preculler_blocks_referenced(self):
        self.assertEqual(self.report['preculler_candidate']['referenced_block_indices'],list(range(24)))

    def test_only_block_zero_empty_and_referenced(self):
        self.assertEqual(self.report['preculler_candidate']['zero_block_indices'],[0])
        self.assertEqual(self.report['preculler_candidate']['candidate_block_0_referenced_by_instance_slots'],[1,2,30])

    def test_redbuilding_instance26_references_block20(self):
        parts=m.children_of(self.scene)
        self.assertEqual(m.rows_and_indices(self.scene,parts)[26],20)

    def test_aux_31_of_31_pattern(self):
        a=self.report['auxiliary_candidate']
        self.assertEqual((a['row_count'],a['rows_with_four_zero_upper_32bits'],a['rows_with_first_three_low_32bit_words_consecutive_mod2_32']),(31,31,31))

    def test_aux_repeated_first_three_only(self):
        a=self.report['auxiliary_candidate']
        self.assertEqual(a['distinct_32byte_rows'],29)
        self.assertEqual(a['repeated_row_multiplicities'],[3])

    def test_original_unchanged(self):
        self.assertTrue(self.report['wii_observed_invariants_verified'])
        self.assertEqual(hashlib.sha256(self.scene).hexdigest(),m.KNOWN_WII_SHA256)

if __name__=='__main__':unittest.main()