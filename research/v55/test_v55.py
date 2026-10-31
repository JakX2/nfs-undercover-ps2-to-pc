"""Offline synthetic-only V55 test suite. No proprietary fixture or packages."""
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v55_scene_inventory as v55


def chunk(tag, payload):
    return struct.pack('<II', tag, len(payload)) + payload


def root(*, change=0, pad_override=None, miss_preculler=False, corrupt=False):
    children = [chunk(v55.SCENE, b'\0' * 68)]
    # Parent ROOT header is 8 bytes. After SCENE chunk, child payload starts
    # at root-relative offset 92, so four pad bytes align instance rows at 96.
    instance_start = 8 + len(children[0]) + 8
    pad = (-instance_start) & 15 if pad_override is None else pad_override
    row = bytearray(96)
    struct.pack_into('<h', row, 28, 1)
    struct.pack_into('<3f', row, 32, 3.0 + change, 4.0, 5.0)
    children.append(chunk(v55.INSTANCE, b'\x11'*pad + bytes(row)))
    children.append(chunk(v55.AUX, bytes(32)))
    if not miss_preculler:
        children.append(chunk(v55.PRECULLER, bytes(128 * 2)))
    payload = b''.join(children)
    if corrupt:
        return struct.pack('<II', v55.ROOT, len(payload)+17) + payload
    return struct.pack('<II', v55.ROOT, len(payload)) + payload


def write(path, content):
    path.write_bytes(content)
    return path


class InventoryTests(unittest.TestCase):
    def test_root_at_zero_and_offset_and_hash(self):
        with tempfile.TemporaryDirectory() as td:
            b = root()
            p = write(Path(td)/'stream.bin', b + b'junk' + b)
            r = v55.scan_stream(p)
            self.assertEqual(r['root_count'], 2)
            self.assertEqual([x['offset'] for x in r['roots']], [0, len(b)+4])
            self.assertEqual([x['sha256'] for x in r['roots']], [hashlib.sha256(b).hexdigest()]*2)

    def test_little_endian_and_root_ending(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', b'abc'+root(change=9))
            r = v55.scan_stream(p)
            self.assertEqual(r['root_count'], 1)
            self.assertEqual(r['roots'][0]['length_bytes'], len(root(change=9)))
            self.assertEqual(r['roots'][0]['offset'], 3)

    def test_candidate_counts_alignment_relative_to_root(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', b'12345' + root())
            x = v55.scan_stream(p)['roots'][0]
            self.assertTrue(x['Wii_candidate_stride_consistent'])
            self.assertEqual(x['candidate_96_byte_instance_rows'], 1)
            self.assertEqual(x['candidate_128_byte_preculler_blocks'], 2)
            self.assertEqual(x['candidate_32_byte_aux_rows'], 1)

    def test_wii_candidate_not_genuine_proven(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            x = v55.inventory([p])
            self.assertEqual(x['streams'][0]['roots'][0]['source_class'], 'unverified_candidate')
            self.assertFalse(x['independent_original_scenes_authenticated'])
            self.assertFalse(x['safe_to_install'])

    def test_corrupt_root_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root(corrupt=True))
            self.assertEqual(v55.scan_stream(p)['root_count'], 0)

    def test_non_wii_root_still_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root(miss_preculler=True))
            x = v55.scan_stream(p)['roots'][0]
            self.assertFalse(x['has_required_Wii_candidate_children'])
            self.assertIsNone(x['Wii_candidate_stride_consistent'])

    def test_wrong_alignment_rejected_only_as_wii_stride(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root(pad_override=3))
            x = v55.scan_stream(p)['roots'][0]
            self.assertFalse(x['Wii_candidate_stride_consistent'])

    def test_same_bytes_not_independent_scenes(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = write(Path(td)/'a', root())
            p2 = write(Path(td)/'b', root())
            result = v55.inventory([p1, p2])
            self.assertEqual(result['total_root_occurrences'], 2)
            self.assertEqual(result['distinct_root_sha256s'], 1)
            self.assertEqual(result['repeated_root_digests'], 1)

    def test_distinct_hashes_not_proven_original(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = write(Path(td)/'a', root())
            p2 = write(Path(td)/'b', root(change=2))
            result = v55.inventory([p1, p2])
            self.assertEqual(result['distinct_root_sha256s'], 2)
            self.assertFalse(result['independent_original_scenes_authenticated'])

    def test_guard_correct_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            x = v55.scan_stream(p, expected_sha256=v55.digest_stream(p))
            self.assertTrue(x['integrity_hash_guard_applied'])

    def test_guard_bad_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            with self.assertRaisesRegex(v55.InventoryError, 'mismatch'):
                v55.scan_stream(p, expected_sha256='a'*64)

    def test_guard_malformed_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            with self.assertRaisesRegex(v55.InventoryError, 'malformed'):
                v55.scan_stream(p, expected_sha256='x')

    def test_reject_missing_expected_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            with self.assertRaises(v55.InventoryError):
                v55.inventory([p, p], expected_hashes=['0'*64])

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'empty', b'')
            self.assertEqual(v55.scan_stream(p)['root_count'], 0)

    def test_false_root_magic_does_not_validate(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', b'junk'+v55.ROOT_MAGIC+bytes(100))
            self.assertEqual(v55.scan_stream(p)['root_count'], 0)

    def test_limit_no_partial_scan(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root()+root())
            with self.assertRaisesRegex(v55.InventoryError, 'limit'):
                v55.scan_stream(p, max_roots=1)

    def test_cli_success_and_content_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            original = p.read_bytes()
            out = Path(td)/'results'/'report.json'
            run = subprocess.run([sys.executable, str(Path(v55.__file__)), '--stream', str(p),
                       '--expected-stream-sha256', v55.digest_stream(p), '--report', str(out)],
                       capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual(json.loads(out.read_text())['total_root_occurrences'], 1)

    def test_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            run = subprocess.run([sys.executable, str(Path(v55.__file__)), '--stream', str(p),
                       '--report', str(p)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('refusing overwrite', run.stderr)

    def test_cli_bad_guard_no_report(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            out = Path(td)/'report.json'
            run = subprocess.run([sys.executable, str(Path(v55.__file__)), '--stream', str(p),
                       '--expected-stream-sha256', '0'*64, '--report', str(out)],
                       capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(out.exists())

    def test_no_game_data_in_reports(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td)/'stream', root())
            result = v55.inventory([p])
            encoded = json.dumps(result)
            self.assertNotIn('C:\\', encoded)
            self.assertNotIn('scenery_vertex', encoded)


if __name__ == '__main__':
    unittest.main()
