"""Synthetic-only owner ZIP and private PC section gate end-to-end checks."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from test_texture_visual_pair_gate import make_pack
from test_undercover_to_pc_dxt5_bridge import dxt5_pc_fixture
from private_undercover_dxt5_archive_audit import (
    _slice_section,_private_uc_section,_private_pc_section,analyze_archives)


def bundle(section_id, payload, off=2048):
    row=bytearray(92)
    struct.pack_into('<h',row,8,section_id)
    struct.pack_into('<II',row,0x14,off,len(payload))
    bun=struct.pack('<II',0x34110,len(row))+row
    stream=bytearray(off+len(payload))
    stream[off:off+len(payload)]=payload
    return bun,bytes(stream)


def fixture(folder,with_pc=False):
    uc=make_pack('ps2',bits=8)
    bun,stream=bundle(3401,uc)
    archive=folder/'uc_tracks.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('TRACKS/L2RB.BUN',bun)
        z.writestr('TRACKS/STREAML2RB.BUN',stream)
    if not with_pc:
        return archive,None,None
    pc=dxt5_pc_fixture()
    pc_bun,pc_stream=bundle(142,pc)
    bb=folder/'pc_L5RB.BUN';ss=folder/'pc_STREAML5RB.BUN'
    bb.write_bytes(pc_bun);ss.write_bytes(pc_stream)
    return archive,bb,ss

class OriginalArchiveGateTests(unittest.TestCase):
    def test_one_section_is_extracted_without_files_written(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);archive,_,_=fixture(folder)
            before=list(folder.iterdir())
            sec=_private_uc_section(archive,3401)
            self.assertEqual(sec,make_pack('ps2',bits=8))
            self.assertEqual(before,list(folder.iterdir()))
    def test_synthetic_original_zip_all_decodes(self):
        with tempfile.TemporaryDirectory() as d:
            archive,_,_=fixture(Path(d))
            r=analyze_archives(archive,3401,2)
            self.assertEqual(r['dxt5_codec']['sampled_textures'],2)
            self.assertEqual(r['dxt5_codec']['mean_alpha_mae'],0)
            self.assertNotIn('pc_section',r)
            self.assertNotIn('286331153',json.dumps(r))
    def test_synthetic_original_uc_to_pc_entire_memory_gate(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);archive,pcbun,pcstream=fixture(folder,with_pc=True)
            before={p.name:p.read_bytes() for p in folder.iterdir()}
            report=analyze_archives(archive,3401,2,pcbun,pcstream,142,0,0)
            p=report['carbon_existing_slot_probe']
            self.assertTrue(p['only_one_existing_image_span_changed'])
            self.assertEqual(p['alpha_mae_against_decoded_ps2'],0)
            self.assertEqual(report['scope'],'PRIVATE_READ_ONLY_OFFLINE_NOT_GAME_LOADED')
            self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir()})
    def test_missing_source_zip_rejected(self):
        with self.assertRaises(ValueError):
            analyze_archives('/bad/original.zip')
    def test_only_one_pc_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=fixture(Path(d),with_pc=True)
            with self.assertRaisesRegex(ValueError,'together'):
                analyze_archives(a,pc_bun=b)
    def test_unsupported_uc_section_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,_,_=fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'Unsupported Undercover'):
                _private_uc_section(a,500)
    def test_unsupported_pc_section_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=fixture(Path(d),with_pc=True)
            with self.assertRaisesRegex(ValueError,'Unsupported Carbon'):
                _private_pc_section(b,c,143)
    def test_missing_id_in_bun_rejected(self):
        a,b=bundle(241,make_pack('ps2'))
        with self.assertRaisesRegex(ValueError,'not found'):
            _slice_section(a,b,3401)
    def test_duplicate_section_table_rejected(self):
        a,b=bundle(3401,make_pack('ps2'))
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            _slice_section(a+a,b,3401)
    def test_unsafe_section_offset_rejected(self):
        a,b=bundle(3401,make_pack('ps2'),off=123)
        with self.assertRaisesRegex(ValueError,'Unsafe Undercover'):
            _slice_section(a,b,3401)
    def test_extra_pc_slot_missing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=fixture(Path(d),with_pc=True)
            with self.assertRaisesRegex(ValueError,'ordinal outside'):
                analyze_archives(a,3401,2,b,c,142,0,42)
    def test_missing_zip_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'zip.zip'
            with zipfile.ZipFile(a,'w') as z:
                z.writestr('TRACKS/L2RB.BUN',b'irrelevant')
            with self.assertRaises(KeyError):
                _private_uc_section(a,3401)

if __name__=='__main__':unittest.main()
