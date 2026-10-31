#!/usr/bin/env python3
"""Asset-free synthetic regression tests for V49; NOT original PC validation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from v49_native_culling_gate import *


def node(minv,maxv,refs,endian='<'):
    b=bytearray(48)
    struct.pack_into(endian+'3f',b,0,*minv)
    struct.pack_into(endian+'H',b,12,len(refs))
    struct.pack_into(endian+'3f',b,16,*maxv)
    if refs:struct.pack_into(endian+str(len(refs))+'h',b,28,*refs)
    return bytes(b)

def make_root(n=2,endian='<',tree=None,prec=None,extra=None):
    def child(k,v):return struct.pack(endian+'II',k,len(v))+v
    infos=bytes(72*n)
    inst=bytearray(96*n)
    for i in range(n):
        x=float(2*i)
        struct.pack_into(endian+'3f',inst,i*96,*(x,0.,0.))
        struct.pack_into(endian+'3f',inst,i*96+16,*(x+1.,1.,1.))
        struct.pack_into(endian+'3f',inst,i*96+32,*(x+.5,0.,0.))
        struct.pack_into(endian+'h',inst,i*96+28,0)
        struct.pack_into(endian+'h',inst,i*96+84,i)
    if tree is None:
        tree=node((0.,0.,0.),(float(2*n-1),1.,1.),list(range(n)),endian)
    if prec is None:prec=bytes(128)
    children=[(SCENE,struct.pack(endian+'I',0x343447)),(INFO,infos),(INSTANCE,bytes(inst)),
              (TREE,tree),(PRECULL,prec),(AUX,bytes(32*n))]
    if extra:children.extend(extra)
    payload=b''.join(child(k,v) for k,v in children)
    return struct.pack(endian+'II',ROOT,len(payload))+payload

def append_row(b,endian='<',prec_idx=0):
    """Only a synthetic in-memory test fixture constructor, not a game writer."""
    ch=parse_root(b,'little' if endian=='<' else 'big')
    n=len(ch[INSTANCE])//96
    row=bytearray(96)
    struct.pack_into(endian+'3f',row,0,*(float(2*n),0.,0.))
    struct.pack_into(endian+'3f',row,16,*(float(2*n+1),1.,1.))
    struct.pack_into(endian+'3f',row,32,*(float(2*n)+.5,0.,0.))
    struct.pack_into(endian+'h',row,28,prec_idx)
    struct.pack_into(endian+'h',row,84,n)
    data=[]
    for k,v in ch.items():
        if k==INFO:v+=bytes(72)
        elif k==INSTANCE:v+=row
        elif k==AUX:v+=bytes(32)
        data.append(struct.pack(endian+'II',k,len(v))+v)
    payload=b''.join(data)
    return struct.pack(endian+'II',ROOT,len(payload))+payload

class V49Synthetic(unittest.TestCase):
    def setUp(self):self.a=make_root()
    def test_01_header(self):self.assertEqual(struct.unpack_from('<I',self.a)[0],ROOT)
    def test_02_valid_root(self):self.assertEqual(len(parse_root(self.a,'little')),6)
    def test_03_scene_id(self):self.assertEqual(audit_root(self.a,'little')['section_id'],'0x00343447')
    def test_04_info(self):self.assertEqual(audit_root(self.a,'little')['info_count_72'],2)
    def test_05_instance(self):self.assertEqual(len(instances96(parse_root(self.a,'little'),'little')),2)
    def test_06_tree(self):self.assertEqual(audit_root(self.a,'little')['tree48']['status'],'candidate_48_byte_tree_pass')
    def test_07_precull(self):self.assertEqual(audit_root(self.a,'little')['preculler128']['blocks'],1)
    def test_08_zero_precull(self):self.assertEqual(audit_root(self.a,'little')['preculler128']['zero_blocks'],1)
    def test_09_aux(self):self.assertTrue(audit_root(self.a,'little')['aux32']['count_matches_instance96'])
    def test_10_false_install(self):self.assertFalse(audit_root(self.a,'little')['safe_to_install'])
    def test_11_384_little_bits(self):
        b=bytearray(128);struct.pack_into('<II',b,120,384,384)
        self.assertEqual(bit_positions(b),[967,968,999,1000])
    def test_12_384_big_bits(self):
        b=bytearray(128);struct.pack_into('>II',b,120,384,384)
        self.assertEqual(bit_positions(b),[976,991,1008,1023])
    def test_13_little_footer(self):
        b=bytearray(128);struct.pack_into('<II',b,120,384,384)
        r=audit_root(make_root(prec=bytes(b)),'little')
        self.assertEqual(r['preculler128']['footer_u32_pair_histogram'],{'(384, 384)':1})
    def test_14_precull_index_invalid(self):
        b=bytearray(self.a);pos=b.find(struct.pack('<II',INSTANCE,192))+8
        struct.pack_into('<h',b,pos+28,5)
        self.assertEqual(audit_root(b,'little')['preculler128']['invalid_nonnegative_indices'],[5])
    def test_15_precull_negative_preserved(self):
        b=bytearray(self.a);pos=b.find(struct.pack('<II',INSTANCE,192))+8
        struct.pack_into('<h',b,pos+28,-1)
        self.assertEqual(audit_root(b,'little')['preculler128']['negative_instance_index_histogram'],{'-1':1})
    def test_16_tree_child_node(self):
        t=node((0,0,0),(3,1,1),[0,-1])+node((2,0,0),(3,1,1),[1])
        r=audit_root(make_root(tree=t),'little')
        self.assertEqual(r['tree48']['nodes'],2)
    def test_17_tree_cycle(self):
        t=node((0,0,0),(3,1,1),[-1])+node((2,0,0),(3,1,1),[-1])
        self.assertEqual(audit_root(make_root(tree=t),'little')['tree48']['status'],'candidate_rejected')
    def test_18_tree_missing_instance(self):
        t=node((0,0,0),(1,1,1),[0])
        self.assertEqual(audit_root(make_root(tree=t),'little')['tree48']['status'],'candidate_rejected')
    def test_19_tree_reused_instance(self):
        t=node((0,0,0),(3,1,1),[0,0])
        self.assertEqual(audit_root(make_root(tree=t),'little')['tree48']['status'],'candidate_rejected')
    def test_20_tree_invalid_node_count(self):
        t=bytearray(node((0,0,0),(3,1,1),[0,1]));struct.pack_into('<H',t,12,11)
        self.assertEqual(audit_root(make_root(tree=bytes(t)),'little')['tree48']['status'],'candidate_rejected')
    def test_21_tree_invalid_aabb(self):
        t=node((0,0,0),(100,1,1),[0,1])
        self.assertEqual(audit_root(make_root(tree=t),'little')['tree48']['status'],'candidate_rejected')
    def test_22_bad_root_sha(self):
        with self.assertRaises(GateError):audit_root(self.a,'little','0'*64)
    def test_23_bad_endian(self):
        with self.assertRaises(GateError):audit_root(self.a,'big')
    def test_24_duplicate_child(self):
        with self.assertRaises(GateError):parse_root(make_root(extra=[(INFO,bytes(72))]),'little')
    def test_25_nested_child(self):
        with self.assertRaises(GateError):parse_root(make_root(extra=[(0x80000001,b'xx')]),'little')
    def test_26_malformed_root_length(self):
        b=bytearray(self.a);struct.pack_into('<I',b,4,9999)
        with self.assertRaises(GateError):parse_root(b,'little')
    def test_27_invalid_info_index(self):
        b=bytearray(self.a);pos=b.find(struct.pack('<II',INSTANCE,192))+8
        struct.pack_into('<h',b,pos+84,9)
        self.assertEqual(audit_root(b,'little')['instance96']['status'],'candidate_rejected')
    def test_28_append_preserves(self):
        r=audit_append(self.a,append_row(self.a),'little')
        self.assertTrue(r['tree_bytes_unchanged']);self.assertTrue(r['preculler_bytes_unchanged'])
        self.assertFalse(r['safe_to_install'])
    def test_29_append_tree_stale(self):
        r=audit_append(self.a,append_row(self.a),'little')
        self.assertEqual(r['tree_original']['status'],'candidate_48_byte_tree_pass')
        self.assertEqual(r['tree_candidate']['status'],'candidate_rejected')
    def test_30_append_extra_child_rejected(self):
        with self.assertRaises(GateError):audit_append(self.a,make_root(extra=[(0x3410E,b'')]),'little')
    def test_31_append_existing_mutation_rejected(self):
        b=bytearray(append_row(self.a));b[20]^=1
        with self.assertRaises(GateError):audit_append(self.a,b,'little')
    def test_32_append_new_precull_out_of_range(self):
        r=audit_append(self.a,append_row(self.a,prec_idx=42),'little')
        self.assertEqual(r['preculler_candidate']['invalid_nonnegative_indices'],[42])
    def test_33_big_endian(self):
        self.assertEqual(audit_root(make_root(endian='>'),'big')['tree48']['status'],'candidate_48_byte_tree_pass')
    def test_34_offset_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.bin';p.write_bytes(b'abc'+self.a)
            self.assertEqual(extract_root(p,'little',3),self.a)
            self.assertEqual(p.read_bytes(),b'abc'+self.a)
    def test_35_file_sha_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.bin';p.write_bytes(self.a)
            with self.assertRaises(GateError):extract_root(p,'little',expected_file_sha='0'*64)
    def test_36_stream_census(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.bin';p.write_bytes(b'prefix'+self.a+b'suffix'+self.a)
            r=scan_stream(p,'little')
            self.assertEqual(len(r['accepted']),2)
    def test_37_stream_limit_not_exhaustive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.bin';p.write_bytes(self.a+self.a)
            r=scan_stream(p,'little',limit=1)
            self.assertEqual(len(r['accepted']),1)
            self.assertTrue(r['accepted_count_is_NOT_exhaustive_if_limit_set'])
    def test_38_cli_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.chunk';p.write_bytes(self.a)
            q=subprocess.run([sys.executable,str(Path(__file__).with_name('v49_native_culling_gate.py')),
                '--original',str(p),'--endian','little','--report',str(p)],capture_output=True)
            self.assertNotEqual(q.returncode,0)
            self.assertEqual(p.read_bytes(),self.a)
    def test_39_cli_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'original.chunk';p.write_bytes(self.a)
            out=Path(d)/'report.json'
            q=subprocess.run([sys.executable,str(Path(__file__).with_name('v49_native_culling_gate.py')),
                '--original',str(p),'--endian','little','--report',str(out)],capture_output=True)
            self.assertEqual(q.returncode,0,q.stderr.decode())
            self.assertFalse(json.loads(out.read_text())['safe_to_install'])
    def test_40_no_fixture_claim(self):
        self.assertNotEqual(digest(self.a),WII_REDBUILDING_SHA)
        self.assertFalse(audit_root(self.a,'little')['pc_serialized_abi_proven'])

if __name__=='__main__':unittest.main(verbosity=2)