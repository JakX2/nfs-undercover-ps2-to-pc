#!/usr/bin/env python3
"""Synthetic-only fixture geometry and generator guards."""
import struct
import unittest
from pathlib import Path
from restore_stm_ioctl_v86 import IOCTL,SIZE,EDGES,EXPECTED,restore,validate_body
from derive_v86_stm_ioctl_generator import OLD,NEW,derive
HERE=Path(__file__).resolve().parent

def body():
    result=bytearray(EXPECTED)
    # Independently encoded test branches; no original guest code.
    for pc,dst in EDGES:
        disp=dst-pc
        assert disp%4==0 and -(1<<25)<=disp<(1<<25)
        struct.pack_into(">I",result,pc-IOCTL,0x48000001|(disp&0x03fffffc))
    return bytes(result)

def fixture():
    header=bytearray(256)
    struct.pack_into(">I",header,0,256)
    struct.pack_into(">I",header,0x48,IOCTL)
    struct.pack_into(">I",header,0x90,SIZE)
    return bytes(header)+EXPECTED

class RestoreTests(unittest.TestCase):
    def test_only_selected_span_changes(self):
        original=fixture()
        updated=restore(original,body())
        self.assertEqual(updated[:256],original[:256])
        self.assertEqual(updated[256:],body())
        self.assertEqual(original[256:],EXPECTED)
    def test_each_wrong_edge_fails_closed(self):
        for pc,_ in EDGES:
            bad=bytearray(body())
            struct.pack_into(">I",bad,pc-IOCTL,0x60000000)
            with self.subTest(pc=pc),self.assertRaises(ValueError):
                validate_body(bytes(bad))
    def test_wrong_length_or_fixture_rejected(self):
        with self.assertRaises(ValueError):
            restore(fixture(),body()[:-4])
        wrong=bytearray(fixture())
        wrong[256]^=1
        with self.assertRaises(ValueError):
            restore(bytes(wrong),body())
    def test_generator(self):
        source=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text()
        result=derive(source)
        self.assertEqual(result.count(NEW),1)
        self.assertNotIn(OLD,result)
        self.assertIn("V79 original context load RFI missing",result)
        for corrupted in (source.replace(OLD,"",1),source.replace(OLD,OLD+OLD,1)):
            with self.assertRaises(ValueError):
                derive(corrupted)
if __name__=="__main__":
    unittest.main()
