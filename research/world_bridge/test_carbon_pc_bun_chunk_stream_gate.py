"""Synthetic-only tests for the complete Carbon PC BUN chunk-stream gate."""
import json
import struct
import unittest
from unittest.mock import patch

from carbon_pc_bun_chunk_stream_gate import inspect_carbon_pc_chunk_stream
from test_carbon_pc_external_resource_read_gate import synthetic_carbon_geometry
from test_texture_visual_pair_gate import make_pack

GEOMETRY = synthetic_carbon_geometry()
TEXTURE = make_pack('pc', hashes=(0x11223344,))
OTHER = struct.pack('<II', 0x00123456, 3) + b'xyz'


class CarbonPcChunkStreamTests(unittest.TestCase):
    def test_standalone_original_free_geometry_root(self):
        r = inspect_carbon_pc_chunk_stream(GEOMETRY, 'geometry')
        self.assertEqual((r['top_level_frames'], r['native_pc_geometry_roots'],
                          r['native_pc_texture_roots']), (1, 1, 0))
        self.assertEqual(r['native_pc_distinct_model_records'], 1)
        self.assertFalse(r['carbon_bun_loader_acceptance_verified'])
        self.assertFalse(r['carbon_runtime_registration_verified'])

    def test_standalone_original_free_texture_root(self):
        r = inspect_carbon_pc_chunk_stream(TEXTURE, 'texture')
        self.assertEqual(r['native_pc_distinct_texture_records'], 1)
        self.assertEqual(r['native_pc_geometry_roots'], 0)

    def test_concatenated_multiple_root_controls(self):
        b = OTHER + GEOMETRY + OTHER + TEXTURE
        r = inspect_carbon_pc_chunk_stream(b, 'either')
        self.assertEqual(r['top_level_frames'], 4)
        self.assertEqual(r['top_level_unknown_frames'], 2)
        self.assertEqual(r['native_pc_geometry_roots'], 1)
        self.assertEqual(r['native_pc_texture_roots'], 1)
        self.assertEqual(r['native_pc_distinct_model_records'], 1)
        self.assertEqual(r['native_pc_distinct_texture_records'], 1)
        self.assertEqual(r['source_total_bytes'], len(b))
        self.assertTrue(r['complete_top_level_chunk_stream'])

    def test_kind_requirement_prevents_wrong_control(self):
        for source, expected in ((TEXTURE, 'geometry'), (GEOMETRY, 'texture')):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                inspect_carbon_pc_chunk_stream(source, expected)

    def test_rejects_repeated_model_and_texture_identity_across_roots(self):
        for b in (GEOMETRY + GEOMETRY, TEXTURE + TEXTURE):
            with self.subTest(size=len(b)), self.assertRaises(ValueError):
                inspect_carbon_pc_chunk_stream(b, 'either')

    def test_unrecognized_chunk_alone_not_proof_of_native_pc(self):
        with self.assertRaises(ValueError):
            inspect_carbon_pc_chunk_stream(OTHER * 6, 'either')

    def test_never_signature_scans_inside_an_unknown_chunk(self):
        disguised = struct.pack('<II', 0x00123456, len(GEOMETRY)) + GEOMETRY
        with self.assertRaises(ValueError):
            inspect_carbon_pc_chunk_stream(disguised, 'geometry')

    def test_truncated_and_oversized_frames_fail(self):
        for corrupted in (GEOMETRY + b'\x01',
                          GEOMETRY + struct.pack('<II', 0x11223344, 100),
                          GEOMETRY[:-3],
                          b'\x00' * 100):
            with self.subTest(length=len(corrupted)), self.assertRaises(ValueError):
                inspect_carbon_pc_chunk_stream(corrupted, 'either')

    def test_nested_pc_root_with_invalid_resource_fails_closed(self):
        wrong = bytearray(GEOMETRY)
        wrong[3] ^= 0x01  # GEOM 0x80134000 low byte is already zero
        with self.assertRaises(ValueError):
            inspect_carbon_pc_chunk_stream(bytes(wrong), 'geometry')
        with patch('carbon_pc_bun_chunk_stream_gate.parse_geometry_root',
                   return_value={'platform': 0x00134A00}):
            with self.assertRaises(ValueError):
                inspect_carbon_pc_chunk_stream(GEOMETRY, 'geometry')

    def test_unsupported_inputs(self):
        for bad in (bytearray(GEOMETRY), None, GEOMETRY[:10], b'', b'X' * (32*1024*1024 + 1)):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                inspect_carbon_pc_chunk_stream(bad, 'geometry')
        with self.assertRaises(ValueError):
            inspect_carbon_pc_chunk_stream(GEOMETRY, 'unknown')

    def test_no_original_resource_ids_leak_to_result(self):
        r = inspect_carbon_pc_chunk_stream(GEOMETRY + TEXTURE, 'either')
        encoded = json.dumps(r)
        for sensitive in ('0xA0B0C0D0', '0x11223344',
                          str(0xA0B0C0D0), str(0x11223344)):
            self.assertNotIn(sensitive, encoded)
        self.assertFalse(r['private_resource_identifiers_disclosed'])


if __name__ == '__main__':
    unittest.main()
