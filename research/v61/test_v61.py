"""Synthetic-only tests for V61 format-neutral archive probing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v61_carbon_chunk_probe as v61


def chunk(tag:int,payload:bytes,order='little',mode='payload')->bytes:
    e=v61.ENDIAN[order]
    n=len(payload) if mode=='payload' else 8+len(payload)
    return struct.pack(e+'II',tag,n)+payload


def make_source(tmp,data):
    p=Path(tmp)/'private_original_game.BUN'
    p.write_bytes(data)
    return p


class ChunkProbeTests(unittest.TestCase):
    def test_root_payload_framing_little(self):
        with tempfile.TemporaryDirectory() as td:
            child=chunk(0x34101,b'ABCD')
            root=chunk(v61.ROOT,child)
            p=make_source(td,b'noise'+root)
            a=v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertEqual(a['signature_hits'],1)
            self.assertEqual(a['candidate_variants'],1)
            r=a['candidates'][0]
            self.assertEqual(r['offset'],5)
            self.assertEqual(r['tag'],'0x80034100')
            self.assertEqual(r['child_framing_probe']['status'],'contiguous_candidate_children')
            self.assertEqual(r['child_framing_probe']['count'],1)
            self.assertEqual(r['child_framing_probe']['records'][0]['id'],'0x00034101')

    def test_root_total_framing_big(self):
        with tempfile.TemporaryDirectory() as td:
            child=chunk(0x34103,b'Q'*16,'big','total')
            root=chunk(v61.ROOT,child,'big','total')
            p=make_source(td,root)
            a=v61.scan_archive(p,orders=('big',),modes=('total',))
            self.assertEqual(a['candidate_variants'],1)
            self.assertEqual(a['candidates'][0]['child_framing_probe']['status'],'contiguous_candidate_children')

    def test_index_header_little(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'\0'*32))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertEqual(r['candidate_variants'],1)
            self.assertEqual(r['candidates'][0]['tag'],'0x00034110')
            self.assertIsNone(r['candidates'][0]['candidate_row_probe'])

    def test_index_header_big(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'hello world!','big'))
            r=v61.scan_archive(p,orders=('big',),modes=('payload',))
            self.assertEqual(r['candidate_variants'],1)
            self.assertEqual(r['candidates'][0]['endian'],'big')

    def test_both_length_modes_report_ambiguity_not_proof(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'\0'*64))
            r=v61.scan_archive(p,orders=('little',),modes=('payload','total'))
            self.assertEqual(r['candidate_variants'],2)
            self.assertEqual(r['ambiguous_candidate_offsets'],1)
            self.assertFalse(r['Carbon_PC_index_layout_proven'])

    def test_wrong_order_does_not_parse(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'0'*16,'big'))
            self.assertEqual(v61.scan_archive(p,orders=('little',))['signature_hits'],0)

    def test_two_targets_in_same_binary(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.ROOT,b'opaque')+chunk(v61.MASTER,b'table'))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertEqual(r['signature_hits'],2)
            self.assertEqual(r['candidate_variants'],2)
            self.assertEqual(r['candidates'][0]['child_framing_probe']['status'],'unparsed')
            self.assertEqual(r['candidates'][1]['tag'],'0x00034110')

    def test_root_without_wii_children_is_still_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.ROOT,chunk(0x34180,b'\0'*16)))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertEqual(r['candidate_variants'],1)
            self.assertEqual(r['candidates'][0]['child_framing_probe']['status'],'contiguous_candidate_children')
            self.assertFalse(r['original_game_provenance_authenticated'])

    def test_malformed_root_children_do_not_invalidate_bounded_header(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.ROOT,b'not_legal_subrecords'))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertEqual(r['candidate_variants'],1)
            self.assertEqual(r['candidates'][0]['child_framing_probe']['status'],'unparsed')

    def test_truncated_root_header_not_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,struct.pack('<I',v61.ROOT)+b'\0'*3)
            r=v61.scan_archive(p,orders=('little',))
            self.assertEqual(r['signature_hits'],1)
            self.assertEqual(r['candidate_variants'],0)

    def test_out_of_bounds_length_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,struct.pack('<II',v61.ROOT,0x7fffffff)+b'x'*32)
            r=v61.scan_archive(p,orders=('little',))
            self.assertEqual(r['candidate_variants'],0)

    def test_framed_root_carries_child_sha_only(self):
        with tempfile.TemporaryDirectory() as td:
            payload=b'a proprietary-looking source byte string'
            p=make_source(td,chunk(v61.ROOT,chunk(0x34102,payload)))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',))
            x=json.dumps(r)
            self.assertNotIn('proprietary-looking',x)
            self.assertIn(hashlib.sha256(payload).hexdigest(),x)

    def test_row_hypothesis_requires_explicit_params(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'\0'*32))
            with self.assertRaises(v61.ProbeError):
                v61.scan_archive(p,row_stride=12)
            with self.assertRaises(v61.ProbeError):
                v61.scan_archive(p,field_offset=0)
            with self.assertRaises(v61.ProbeError):
                v61.scan_archive(p,row_start=8)

    def test_raw_integer_reference_match_little(self):
        with tempfile.TemporaryDirectory() as td:
            rows=bytearray(36)
            struct.pack_into('<I',rows,4,0x120)
            struct.pack_into('<I',rows,16,0x340)
            struct.pack_into('<I',rows,28,0x120)
            p=make_source(td,chunk(v61.MASTER,bytes(rows)))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',),
                 row_stride=12,field_offset=4,reference_offsets=(0x120,))
            probe=r['candidates'][0]['candidate_row_probe']
            self.assertEqual(probe['row_count_if_hypothesis'],3)
            self.assertEqual([v['row'] for v in probe['matching_raw_integer_values_capped_50']],[0,2])
            self.assertFalse(probe['proven_pointer_or_relocation'])

    def test_raw_integer_reference_match_big(self):
        with tempfile.TemporaryDirectory() as td:
            rows=bytearray(20)
            struct.pack_into('>I',rows,8,0x2345)
            p=make_source(td,chunk(v61.MASTER,bytes(rows),'big'))
            r=v61.scan_archive(p,orders=('big',),modes=('payload',),
                 row_stride=20,field_offset=8,reference_offsets=(0x2345,))
            self.assertEqual(r['candidates'][0]['candidate_row_probe']['matching_raw_integer_values_capped_50'][0]['row'],0)

    def test_row_start_explicit_header_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'\xAA'*4+b'\0'*12))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',),
                 row_stride=12,field_offset=0,row_start=4)
            pr=r['candidates'][0]['candidate_row_probe']
            self.assertEqual(pr['row_count_if_hypothesis'],1)
            self.assertEqual(pr['trailing_bytes_if_hypothesis'],0)

    def test_invalid_stride_field_range(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'\0'*32))
            for stride,off in [(3,0),(10,7),(4097,0),(12,-1)]:
                with self.subTest(stride=stride,off=off):
                    with self.assertRaises(v61.ProbeError):
                        v61.scan_archive(p,row_stride=stride,field_offset=off)

    def test_row_limit_truncates_only_hypothesis(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,bytes(120)))
            r=v61.scan_archive(p,orders=('little',),modes=('payload',),
                 row_stride=12,field_offset=0,reference_offsets=(0,),max_rows=2)
            pr=r['candidates'][0]['candidate_row_probe']
            self.assertEqual(pr['rows_examined'],2)
            self.assertTrue(pr['rows_truncated'])
            self.assertEqual(len(pr['matching_raw_integer_values_capped_50']),2)

    def test_empty_file_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,b'')
            r=v61.scan_archive(p)
            self.assertEqual(r['archive_sha256'],hashlib.sha256(b'').hexdigest())
            self.assertEqual(r['signature_hits'],0)

    def test_sha_guard_good(self):
        with tempfile.TemporaryDirectory() as td:
            data=chunk(v61.MASTER,b'0123456789')
            p=make_source(td,data)
            r=v61.scan_archive(p,expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertTrue(r['trusted_expected_archive_digest_checked'])

    def test_sha_guard_bad(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'A'*16))
            with self.assertRaisesRegex(v61.ProbeError,'mismatch'):
                v61.scan_archive(p,expected_sha256='1'*64)

    def test_malformed_guard(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,b'')
            with self.assertRaises(v61.ProbeError):
                v61.scan_archive(p,expected_sha256='oops')

    def test_signature_limit_no_partial_report(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'abc')*3)
            with self.assertRaisesRegex(v61.ProbeError,'hit limit'):
                v61.scan_archive(p,orders=('little',),max_hits=1)

    def test_candidate_limit_no_partial_report(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'x'*48))
            with self.assertRaisesRegex(v61.ProbeError,'variant limit'):
                v61.scan_archive(p,orders=('little',),max_candidates=1)

    def test_no_source_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            raw=chunk(v61.MASTER,b'ABCD'*16)
            p=make_source(td,raw)
            v61.scan_archive(p)
            self.assertEqual(p.read_bytes(),raw)

    def test_modify_source_while_parsing_detected(self):
        with tempfile.TemporaryDirectory() as td:
            raw=chunk(v61.ROOT,chunk(0x34101,b'ABC')+b'originaltail')
            p=make_source(td,raw)
            original=v61._children
            altered=[False]
            def tamper(*args,**kwargs):
                if not altered[0]:
                    altered[0]=True
                    with p.open('r+b') as f:
                        f.seek(-1,2)
                        f.write(b'X')
                        f.flush()
                return original(*args,**kwargs)
            with mock.patch.object(v61,'_children',side_effect=tamper):
                with self.assertRaisesRegex(v61.ProbeError,'changed while scanning'):
                    v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertTrue(altered[0])

    def test_path_replacement_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.ROOT,chunk(0x34101,b'ABCD')))
            other=Path(td)/'new-archive.bin'
            other.write_bytes(p.read_bytes())
            orig=v61._children
            happened=[False]
            def swap(*args,**kwargs):
                if not happened[0]:
                    happened[0]=True
                    other.replace(p)
                return orig(*args,**kwargs)
            with mock.patch.object(v61,'_children',side_effect=swap):
                with self.assertRaisesRegex(v61.ProbeError,'path replaced'):
                    v61.scan_archive(p,orders=('little',),modes=('payload',))
            self.assertTrue(happened[0])

    def test_cli_report_and_exclusive_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'A'*32))
            out=Path(td)/'report.json'
            command=[sys.executable,str(Path(v61.__file__)),'--archive',str(p),
                     '--report',str(out),'--endian','little','--length-mode','payload']
            r=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(out.read_text())['candidate_variants'],1)
            rerun=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(rerun.returncode,0)
            self.assertEqual(p.read_bytes(),chunk(v61.MASTER,b'A'*32))

    def test_cli_rejects_source_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'A'*16))
            cmd=[sys.executable,str(Path(v61.__file__)),'--archive',str(p),'--report',str(p)]
            run=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('refusing overwrite',run.stderr)

    def test_no_private_paths_in_report(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_source(td,chunk(v61.MASTER,b'A'*40))
            report=json.dumps(v61.scan_archive(p))
            self.assertNotIn(str(p),report)
            self.assertNotIn('private_original_game.BUN',report)
            self.assertFalse(json.loads(report)['safe_to_install'])


if __name__=='__main__':
    unittest.main()
