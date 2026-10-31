"""V51 source-only tests for the V49 candidate 96-byte scenery reader.

Public tests generate synthetic roots. Optional fixture tests require an
AUTHORIZED original Wii ROOT supplied via NFS_UC_WII_SCENE; no binary fixtures
are distributed here. Wii format observations are not Carbon PC loader proof.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v49'))
import v49_native_culling_gate as v49

WII_SHA = 'cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'


def frame(children, endian='little'):
    e = '<' if endian == 'little' else '>'
    data = b''.join(struct.pack(e+'II', tag, len(payload)) + payload for tag, payload in children)
    return struct.pack(e+'II', v49.ROOT, len(data)) + data


def instance(info=0, prec=0, endian='little'):
    e = '<' if endian == 'little' else '>'
    b = bytearray(96)
    struct.pack_into(e+'3f', b, 0, -1.0, -2.0, -3.0)
    struct.pack_into(e+'3f', b, 16, 1.0, 2.0, 3.0)
    struct.pack_into(e+'h', b, 28, prec)
    struct.pack_into(e+'3f', b, 32, 23.0, 25.0, 27.0)
    struct.pack_into(e+'h', b, 84, info)
    return bytes(b)


def node(endian='little'):
    e = '<' if endian == 'little' else '>'
    b = bytearray(48)
    struct.pack_into(e+'3f', b, 0, -1.0, -2.0, -3.0)
    struct.pack_into(e+'H', b, 12, 1)
    struct.pack_into(e+'3f', b, 16, 1.0, 2.0, 3.0)
    struct.pack_into(e+'h', b, 28, 0)
    return bytes(b)


def fixture(scene_len=4, endian='little', add_second=False):
    e = '<' if endian == 'little' else '>'
    # 34103 is intentionally BEFORE 34102 so appends to the later info table
    # do not change absolute instance-row alignment.
    start = 8 + (8+scene_len) + 8
    pad = (-start) & 15
    rows = instance(endian=endian)
    if add_second:
        rows += instance(info=1, endian=endian)
    c = [
        (v49.SCENE, b'\x00' * scene_len),
        (v49.INSTANCE, b'\x11' * pad + rows),
        (v49.INFO, b'\x00' * (144 if add_second else 72)),
        (v49.TREE, node(endian)),
        (v49.PRECULL, b'\x00' * 128),
        (v49.AUX, b'\x00' * (64 if add_second else 32)),
    ]
    return frame(c, endian)


class PublicSyntheticTests(unittest.TestCase):
    def test_offset_4(self):
        b=fixture(4)
        self.assertEqual(v49.instance96_padding(b,'little'),4)
        self.assertEqual(v49.child_payload_offset(b,'little',v49.INSTANCE),28)
        self.assertEqual(len(v49.parse_root(b,'little')[v49.INSTANCE]),100)
        self.assertEqual(v49.audit_root(b,'little')['instance96']['count'],1)

    def test_offset_0(self):
        b=fixture(8)
        self.assertEqual(v49.instance96_padding(b,'little'),0)
        self.assertEqual(v49.audit_root(b,'little')['instance96']['count'],1)

    def test_offset_12(self):
        b=fixture(12)
        self.assertEqual(v49.instance96_padding(b,'little'),12)
        self.assertEqual(v49.audit_root(b,'little')['instance96']['count'],1)

    def test_offset_8(self):
        b=fixture(16)
        self.assertEqual(v49.instance96_padding(b,'little'),8)
        self.assertEqual(v49.audit_root(b,'little')['instance96']['count'],1)

    def test_be_4(self):
        b=fixture(4,'big')
        self.assertEqual(v49.instance96_padding(b,'big'),4)
        self.assertEqual(v49.audit_root(b,'big')['instance96']['count'],1)

    def test_wrong_endianness_rejected(self):
        with self.assertRaises(v49.GateError):
            v49.audit_root(fixture(4,'big'),'little')

    def test_tree_valid(self):
        r=v49.audit_root(fixture(4),'little')
        self.assertEqual(r['tree48']['status'],'candidate_48_byte_tree_pass')
        self.assertFalse(r['pc_serialized_abi_proven'])
        self.assertFalse(r['safe_to_install'])

    def test_padding_prefix_preserved_as_opaque(self):
        b=fixture(4)
        ch=v49.parse_root(b,'little')
        self.assertEqual(ch[v49.INSTANCE][:4],b'\x11'*4)
        self.assertEqual(v49.instances96(ch,'little',b)[0]['position'],(23.0,25.0,27.0))

    def test_padding_only_is_zero_instances_not_one(self):
        b=frame([(v49.SCENE,b'\x00'*4),
                 (v49.INSTANCE,b'\x11'*4),
                 (v49.INFO,b'\x00'*72)],'little')
        r=v49.audit_root(b,'little')
        self.assertEqual(r['instance96']['count'],0)

    def test_missing_padding_rejected(self):
        b=frame([(v49.SCENE,b'\x00'*4),
                 (v49.INSTANCE,instance()),
                 (v49.INFO,b'\x00'*72)],'little')
        self.assertEqual(v49.audit_root(b,'little')['instance96']['status'],'candidate_rejected')

    def test_extra_byte_rejected(self):
        b=frame([(v49.SCENE,b'\x00'*4),
                 (v49.INSTANCE,b'\x11'*4+instance()+b'\x00'),
                 (v49.INFO,b'\x00'*72)],'little')
        self.assertEqual(v49.audit_root(b,'little')['instance96']['status'],'candidate_rejected')

    def test_multiple_rows_from_append(self):
        r=v49.audit_root(fixture(4,add_second=True),'little')
        self.assertEqual(r['instance96']['count'],2)
        self.assertEqual(r['instance96']['status'],'candidate_structurally_accepted')
        self.assertEqual(r['tree48']['status'],'candidate_rejected')
        self.assertIn('coverage',r['tree48']['reason'])

    def test_append_guard_reports_unchanged_tree_risk(self):
        x=v49.audit_append(fixture(4),fixture(4,add_second=True),'little')
        self.assertEqual((x['old_instance_count'],x['new_instance_count']),(1,2))
        self.assertEqual((x['original_instance_padding_bytes'],x['candidate_instance_padding_bytes']),(4,4))
        self.assertTrue(x['tree_bytes_unchanged'])
        self.assertEqual(x['tree_original']['status'],'candidate_48_byte_tree_pass')
        self.assertEqual(x['tree_candidate']['status'],'candidate_rejected')
        self.assertFalse(x['safe_to_install'])

    def test_parse_root_fails_corruption(self):
        b=fixture(4)
        with self.assertRaises(v49.GateError):
            v49.parse_root(b[:-1],'little')

    def test_nonexistent_child_lookup_fails_closed(self):
        with self.assertRaisesRegex(v49.GateError,'absent'):
            v49.child_payload_offset(fixture(4),'little',0x341FF)


class PrivateOriginalFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('NFS_UC_WII_SCENE')
        if not path or not Path(path).is_file():
            raise unittest.SkipTest('Original Wii fixture not provided locally')
        cls.data=Path(path).read_bytes()
        if hashlib.sha256(cls.data).hexdigest()!=WII_SHA:
            raise unittest.SkipTest('Local fixture does not match pinned Wii source SHA-256')

    def test_wii_source_31_rows(self):
        r=v49.audit_root(self.data,'little',expected_sha=WII_SHA)
        self.assertEqual(r['instance96']['count'],31)
        self.assertEqual(r['candidate_instance96_root_alignment_padding_bytes'],4)

    def test_wii_source_tree_exact_coverage(self):
        r=v49.audit_root(self.data,'little',expected_sha=WII_SHA)
        self.assertEqual(r['tree48']['status'],'candidate_48_byte_tree_pass')
        self.assertEqual((r['tree48']['nodes'],r['tree48']['covered_instances']),(8,31))

    def test_wii_source_info_index_26(self):
        ch=v49.parse_root(self.data,'little')
        rows=v49.instances96(ch,'little',self.data)
        self.assertEqual(rows[26]['info'],8)
        self.assertEqual(rows[26]['preculler'],20)

    def test_padding_byte_signature_is_observed_not_semantic(self):
        ch=v49.parse_root(self.data,'little')
        self.assertEqual(ch[v49.INSTANCE][:4],b'\x11'*4)
        self.assertFalse(v49.audit_root(self.data,'little')['pc_serialized_abi_proven'])


if __name__=='__main__':
    unittest.main()