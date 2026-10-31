"""V59 source-only regression tests for V55/V58 ROOT manifest handoff."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v55'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v58'))
import v55_cross_scene_hypothesis_gate as v55
import v58_stream_scene_bridge as v58
from test_v55 import make_scene


def prepared(tmp, *, offset=True):
    """Synthetic archive with bytes outside the real ROOT."""
    root=make_scene(n=3,nodes=2,blocks=3)
    archive=(b'FIRST_PREFIX__' if offset else b'')+root+(b'UNRELATED_TRAILER' if offset else b'')
    path=Path(tmp)/'archive.bin'
    path.write_bytes(archive)
    spec={
        'path':str(path),'label':'synthetic',
        'endian':'little','platform_hint':'wii',
        'expected_file_sha256':v55.sha256(archive),
        'expected_root_sha256':v55.sha256(root)
    }
    if offset:spec['offset']=len(b'FIRST_PREFIX__')
    return path,root,spec


class SameHandleManifestTests(unittest.TestCase):

    def test_standalone_root_verified(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td,offset=False)
            got,parsed,metadata=v55.read_verified_root(spec)
            self.assertEqual(got,root)
            self.assertIn(v55.SCENE,parsed)
            self.assertTrue(metadata['same_open_handle_hash_and_extract'])
            self.assertTrue(metadata['best_effort_file_change_check_passed'])
            self.assertFalse(metadata['atomic_filesystem_snapshot'])
            self.assertEqual(path.read_bytes(),root)

    def test_embedded_root_verified_with_trailer(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            got,parsed,metadata=v55.read_verified_root(spec)
            self.assertEqual(got,root)
            self.assertEqual(metadata['stream_offset'],len(b'FIRST_PREFIX__'))
            self.assertTrue(metadata['same_open_handle_hash_and_extract'])

    def test_reject_unexpected_whole_archive_sha(self):
        with tempfile.TemporaryDirectory() as td:
            _,root,spec=prepared(td)
            spec['expected_file_sha256']='a'*64
            with self.assertRaisesRegex(v55.GateError,'file fingerprint mismatch'):
                v55.read_verified_root(spec)

    def test_reject_root_sha_even_if_archive_matches(self):
        with tempfile.TemporaryDirectory() as td:
            _,root,spec=prepared(td)
            spec['expected_root_sha256']='b'*64
            with self.assertRaisesRegex(v55.GateError,'root fingerprint mismatch'):
                v55.read_verified_root(spec)

    def test_reject_mutation_outside_root_during_read(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            original=v55._read_framed_root
            def modify_trailer(fh, offset, size, order):
                result=original(fh,offset,size,order)
                with path.open('r+b') as out:
                    out.seek(-1,2)
                    out.write(b'Z')
                    out.flush()
                return result
            with mock.patch.object(v55,'_read_framed_root',side_effect=modify_trailer):
                with self.assertRaisesRegex(v55.GateError,'changed while extracting'):
                    v55.read_verified_root(spec)
            self.assertEqual(path.read_bytes()[spec['offset']:spec['offset']+len(root)],root)

    def test_reject_source_path_replaced_during_read(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            alternate=Path(td)/'replacement.bin'
            alternate.write_bytes(path.read_bytes())
            original=v55._read_framed_root
            def replace_source(fh,offset,size,order):
                result=original(fh,offset,size,order)
                alternate.replace(path)
                return result
            with mock.patch.object(v55,'_read_framed_root',side_effect=replace_source):
                with self.assertRaisesRegex(v55.GateError,'source path replaced'):
                    v55.read_verified_root(spec)

    def test_reject_metadata_change_even_without_byte_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            original=v55._read_framed_root
            def touch_source(fh,offset,size,order):
                result=original(fh,offset,size,order)
                path.touch()
                return result
            with mock.patch.object(v55,'_read_framed_root',side_effect=touch_source):
                with self.assertRaisesRegex(v55.GateError,'metadata changed'):
                    v55.read_verified_root(spec)

    def test_legacy_separate_open_digest_not_used(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,spec=prepared(td)
            with mock.patch.object(v55,'file_digest',
                                   side_effect=AssertionError('old second-open hash used')):
                got,_,meta=v55.read_verified_root(spec)
            self.assertEqual(v55.sha256(got),spec['expected_root_sha256'])
            self.assertTrue(meta['same_open_handle_hash_and_extract'])

    def test_v58_private_manifest_is_readable_by_v59_hardened_v55(self):
        with tempfile.TemporaryDirectory() as td:
            root=make_scene(n=3,nodes=2,blocks=3)
            path=Path(td)/'game-archive.bin'
            path.write_bytes(b'SECRET_PREFIX'+root+b'SECRET_SUFFIX')
            report=v58.scan_archive(path)
            manifest=v58.build_private_manifest(path,report)
            self.assertEqual(len(manifest['roots']),1)
            extracted,child,meta=v55.read_verified_root(manifest['roots'][0])
            self.assertEqual(extracted,root)
            self.assertIn(v55.INSTANCE,child)
            self.assertTrue(meta['best_effort_file_change_check_passed'])
            # Standalone metadata reports do not contain local archive paths.
            self.assertNotIn(str(path),json.dumps(report))

    def test_original_stream_is_never_written(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            before=path.read_bytes()
            for _ in range(2):
                v55.read_verified_root(spec)
            self.assertEqual(path.read_bytes(),before)

    def test_bad_offset_still_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,spec=prepared(td)
            spec['offset']=10_000_000
            with self.assertRaisesRegex(v55.GateError,'offset outside stream'):
                v55.read_verified_root(spec)

    def test_mutation_outside_root_after_scan_no_longer_matches_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            path,root,spec=prepared(td)
            with path.open('r+b') as out:
                out.seek(-1,2)
                out.write(b'X')
            with self.assertRaisesRegex(v55.GateError,'file fingerprint mismatch'):
                v55.read_verified_root(spec)


if __name__=='__main__':
    unittest.main()
