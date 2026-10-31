"""Synthetic V58 regression suite. Original game files are never committed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v56'))
import v58_stream_scene_bridge as v58
from test_v56 import fixture


def create(directory,name,data):
    path=Path(directory)/name
    path.write_bytes(data)
    return path


class SyntheticStreamBridge(unittest.TestCase):

    def test_one_root_at_arbitrary_offset(self):
        with tempfile.TemporaryDirectory() as td:
            root=fixture()
            path=create(td,'source.bin',b'padding123'+root+b'trailer')
            result=v58.scan_archive(path)
            self.assertEqual(result['candidate_root_occurrences'],1)
            self.assertEqual(result['records'][0]['offset'],10)
            self.assertEqual(result['records'][0]['root_sha256'],hashlib.sha256(root).hexdigest())
            self.assertEqual(result['records'][0]['candidate_wii_graph_status'],'candidate_internally_consistent')
            self.assertEqual(result['records'][0]['candidate_instance_count'],3)
            self.assertEqual(result['records'][0]['candidate_tree_node_count'],1)

    def test_repeated_identical_roots_not_independent(self):
        with tempfile.TemporaryDirectory() as td:
            root=fixture()
            path=create(td,'source.bin',root+b'between'+root)
            result=v58.scan_archive(path)
            self.assertEqual(result['candidate_root_occurrences'],2)
            self.assertEqual(result['distinct_candidate_root_sha256s'],1)
            self.assertEqual(result['duplicate_candidate_root_occurrences'],1)
            self.assertFalse(result['independent_original_scenes_authenticated'])

    def test_distinct_synthetic_roots_not_authenticated(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture()+fixture(n=2))
            r=v58.scan_archive(path)
            self.assertEqual(r['distinct_candidate_root_sha256s'],2)
            self.assertFalse(r['source_identity_independently_authenticated'])
            self.assertFalse(r['carbon_pc_disk_abi_verified'])

    def test_framed_root_rejected_graph_when_bad_preculler(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture(bad_prec=999))
            r=v58.scan_archive(path)
            self.assertEqual(r['candidate_root_occurrences'],1)
            self.assertEqual(r['records'][0]['candidate_wii_graph_status'],'rejected')
            self.assertIn('preculler',r['records'][0]['candidate_wii_rejection'])

    def test_carbon_hint_does_not_apply_wii_graph_to_unknown_PC(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture())
            r=v58.scan_archive(path,source_hint='carbon_pc')
            self.assertEqual(r['records'][0]['candidate_wii_graph_status'],'not_evaluated_for_non_Wii_source')
            self.assertFalse(r['carbon_pc_disk_abi_verified'])

    def test_unknown_hint_also_skips_wii_graph(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture(),)
            r=v58.scan_archive(path,source_hint='unknown')
            self.assertEqual(r['records'][0]['candidate_wii_graph_status'],'not_evaluated_for_non_Wii_source')

    def test_big_endian_synthetic_framing(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',b'xyz'+fixture(endian='big'))
            r=v58.scan_archive(path,order='big')
            self.assertEqual(r['candidate_root_occurrences'],1)
            self.assertEqual(r['records'][0]['candidate_wii_graph_status'],'candidate_internally_consistent')

    def test_big_endian_source_not_identified_as_known_wii(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture(endian='big'))
            r=v58.scan_archive(path,order='big')
            self.assertEqual(r['records'][0]['source_class'],'unverified_candidate')

    def test_wrong_endian_misses_synthetic(self):
        with tempfile.TemporaryDirectory() as td:
            path=create(td,'source.bin',fixture(endian='big'))
            self.assertEqual(v58.scan_archive(path,order='little')['candidate_root_occurrences'],0)

    def test_false_magic_only_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',struct.pack('<I',v58.prior.ROOT)+bytes(160))
            r=v58.scan_archive(p)
            self.assertEqual(r['candidate_root_occurrences'],0)
            self.assertEqual(r['signature_matches_not_matching_expected_layout'],1)

    def test_truncated_root_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            raw=fixture()
            p=create(td,'source.bin',raw[:-20])
            r=v58.scan_archive(p)
            self.assertEqual(r['candidate_root_occurrences'],0)

    def test_empty_source(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',b'')
            r=v58.scan_archive(p)
            self.assertEqual(r['archive_size_bytes'],0)
            self.assertEqual(r['candidate_root_occurrences'],0)
            self.assertEqual(r['archive_sha256'],hashlib.sha256(b'').hexdigest())

    def test_archive_sha_guard_good_and_bad(self):
        with tempfile.TemporaryDirectory() as td:
            raw=fixture();p=create(td,'source.bin',raw)
            good=hashlib.sha256(raw).hexdigest()
            self.assertTrue(v58.scan_archive(p,expected_stream_sha256=good)['archive_integrity_guard_applied'])
            with self.assertRaisesRegex(v58.ScanError,'mismatch'):
                v58.scan_archive(p,expected_stream_sha256='0'*64)

    def test_reject_malformed_guard(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            with self.assertRaises(v58.prior.GateError):
                v58.scan_archive(p,expected_stream_sha256='nonsense')

    def test_reject_invalid_limits_and_hint(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            with self.assertRaises(v58.ScanError):v58.scan_archive(p,max_roots=0)
            with self.assertRaises(v58.ScanError):v58.scan_archive(p,max_hits=0)
            with self.assertRaises(v58.ScanError):v58.scan_archive(p,source_hint='definitely_PC')

    def test_reject_max_roots_no_partial_output(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture()+fixture(n=2))
            with self.assertRaisesRegex(v58.ScanError,'limit'):
                v58.scan_archive(p,max_roots=1)

    def test_reject_max_hits_no_partial_output(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture()+fixture(n=2))
            with self.assertRaisesRegex(v58.ScanError,'limit'):
                v58.scan_archive(p,max_hits=1)

    def test_manifest_opened_by_existing_v55_reader(self):
        with tempfile.TemporaryDirectory() as td:
            root=fixture()
            p=create(td,'source.bin',b'lead'+root)
            manifest=v58.build_private_manifest(p,v58.scan_archive(p))
            self.assertEqual(len(manifest['roots']),1)
            self.assertEqual(manifest['roots'][0]['offset'],4)
            rr,ch,meta=v58.prior.read_verified_root(manifest['roots'][0])
            self.assertEqual(rr,root)
            self.assertEqual(meta['root_sha256'],hashlib.sha256(root).hexdigest())

    def test_cli_metadata_report_has_no_private_path_or_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'hidden-unauthorized-game-stream.bin',fixture())
            report=Path(td)/'meta.json'
            run=subprocess.run([sys.executable,str(Path(v58.__file__)),'--archive',str(p),
                    '--report',str(report)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads(report.read_text())
            self.assertEqual(data['candidate_root_occurrences'],1)
            self.assertNotIn(p.name,report.read_text())
            self.assertNotIn(str(p),report.read_text())
            self.assertFalse(data['safe_to_install'])

    def test_cli_private_manifest_has_path_intentionally(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            report=Path(td)/'meta.json';manifest=Path(td)/'private.json'
            run=subprocess.run([sys.executable,str(Path(v58.__file__)),'--archive',str(p),
                  '--report',str(report),'--private-manifest',str(manifest)],
                  capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(manifest.read_text())['roots'][0]['path'],str(p.resolve()))
            self.assertNotIn(str(p.resolve()),report.read_text())

    def test_cli_refuses_source_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            original=p.read_bytes()
            run=subprocess.run([sys.executable,str(Path(v58.__file__)),'--archive',str(p),
                    '--report',str(p)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('Refusing overwrite',run.stderr)
            self.assertEqual(p.read_bytes(),original)

    def test_cli_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            report=create(td,'report.json',b'do-not-overwrite')
            run=subprocess.run([sys.executable,str(Path(v58.__file__)),'--archive',str(p),
                    '--report',str(report)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(report.read_bytes(),b'do-not-overwrite')

    def test_cli_bad_hash_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            p=create(td,'source.bin',fixture())
            report=Path(td)/'report.json'
            run=subprocess.run([sys.executable,str(Path(v58.__file__)),'--archive',str(p),
                    '--expected-archive-sha256','0'*64,'--report',str(report)],
                    capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertFalse(report.exists())

    def test_source_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            original=fixture()+fixture(n=2)
            p=create(td,'source.bin',original)
            v58.scan_archive(p)
            self.assertEqual(p.read_bytes(),original)


if __name__=='__main__':
    unittest.main()
