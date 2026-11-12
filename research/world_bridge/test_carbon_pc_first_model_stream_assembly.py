"""Source-only PC-shaped one-model chunk-stream assembly regressions.

Only fictional triangles, synthetic 8x8 RGBA and synthetic model/texture
IDs. No retail originals or external loader required by GitHub CI.
"""
import json
import struct
import unittest
from unittest.mock import patch

from carbon_pc_first_model_stream_assembly import (
    build_private_pc_first_model_stream,
)
from undercover_pc_geometry_bridge import convert_decoded_ps2_model
from undercover_pc_dxt5_new_identity_candidate import _assemble_pc_dxt5_entries
from synthetic_dxt5_texture_writer import encode_dxt5_base
from texture_metadata_pixel_bridge import parse_pack
from test_texture_visual_pair_gate import make_pack

MODEL = 0xABCD1234
IMG1 = 0xAABB1234
IMG2 = 0xAABB1235


def geometry(materials=(IMG1,)):
    points = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    uv = ((0., 0.), (1., 0.), (0., 1.))
    blob, _ = convert_decoded_ps2_model(
        MODEL, tuple(materials), points, uv, ((0, 1, 2),), (0,), None)
    return blob


def dxt5(*ids):
    rgba = bytes((100, 90, 200, 125)) * 64
    packed = encode_dxt5_base(rgba, 8, 8)
    entries = [
        (key, b'SYNTHETIC_IMAGE' + str(idx).encode('ascii'), 8, 8, 1, packed)
        for idx, key in enumerate(ids)
    ]
    blob, _ = _assemble_pc_dxt5_entries(tuple(entries))
    return blob


class FirstModelChunkStreamTests(unittest.TestCase):
    def test_original_free_one_model_and_dxt5_texture(self):
        g, t = geometry(), dxt5(IMG1)
        blob, report = build_private_pc_first_model_stream(g, t)
        self.assertEqual(blob, g + t)
        self.assertEqual(report['pc_candidate_chunk_stream_bytes_in_memory'],
                         len(g) + len(t))
        self.assertEqual(report['pc_candidate_model_records'], 1)
        self.assertEqual(report['pc_candidate_texture_records'], 1)
        self.assertEqual(report['top_level_frames'], 2)
        self.assertEqual(report['native_pc_geometry_roots'], 1)
        self.assertEqual(report['native_pc_texture_roots'], 1)
        self.assertTrue(report['full_material_table_identities_backed'])
        self.assertTrue(report['complete_pc_chunk_framing_reparsed'])
        self.assertTrue(report['pc_dxt5_only'])
        for key in ('retail_carbon_bun_container_abi_verified',
                    'retail_carbon_runtime_registration_verified',
                    'pc_loader_accepted_candidate_verified',
                    'undercover_model_rendered_in_game',
                    'installed_or_exported_candidate',
                    'private_model_texture_ids_and_pixels_disclosed'):
            self.assertFalse(report[key])

    def test_full_local_material_table_supported_even_unused_slot(self):
        g, t = geometry((IMG1, IMG2)), dxt5(IMG1, IMG2)
        blob, report = build_private_pc_first_model_stream(g, t)
        self.assertEqual(report['pc_candidate_texture_records'], 2)
        self.assertEqual(blob[:len(g)], g)

    def test_no_unresolved_or_extra_texture_identity(self):
        g = geometry((IMG1, IMG2))
        for bad in (dxt5(IMG1), dxt5(IMG1, IMG2, 0x12345678)):
            with self.subTest(textures=len(parse_pack(bad,'pc')['records'])):
                with self.assertRaisesRegex(ValueError, 'exactly match'):
                    build_private_pc_first_model_stream(g, bad)

    def test_wrong_texture_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            build_private_pc_first_model_stream(geometry(), dxt5(IMG2))

    def test_dxt1_texture_rejected_by_default(self):
        native_dxt1 = make_pack('pc', hashes=(IMG1,))
        with self.assertRaisesRegex(ValueError, 'DXT5-only'):
            build_private_pc_first_model_stream(geometry(), native_dxt1)
        blob, report = build_private_pc_first_model_stream(
            geometry(), native_dxt1, require_dxt5=False)
        self.assertFalse(report['pc_dxt5_only'])
        self.assertEqual(len(blob), report['pc_candidate_chunk_stream_bytes_in_memory'])

    def test_trailing_geometry_root_rejected(self):
        with self.assertRaisesRegex(ValueError, 'one exact'):
            build_private_pc_first_model_stream(geometry()+b'BAD!', dxt5(IMG1))

    def test_trailing_texture_root_rejected(self):
        with self.assertRaisesRegex(ValueError, 'one exact'):
            build_private_pc_first_model_stream(geometry(), dxt5(IMG1)+b'BAD!')

    def test_swapped_resource_types_rejected(self):
        with self.assertRaises(ValueError):
            build_private_pc_first_model_stream(dxt5(IMG1), geometry())

    def test_invalid_source_types_rejected(self):
        for g,t,flag in (
            (None,dxt5(IMG1),True),
            (bytearray(geometry()),dxt5(IMG1),True),
            (geometry(),bytearray(dxt5(IMG1)),True),
            (geometry(),dxt5(IMG1),'True'),
        ):
            with self.subTest(g=type(g).__name__,t=type(t).__name__,flag=flag):
                with self.assertRaises(ValueError):
                    build_private_pc_first_model_stream(g,t,flag)

    def test_oversized_stream_rejected_before_allocation(self):
        with patch('carbon_pc_first_model_stream_assembly.MAX_BUN_BYTES', 100):
            with self.assertRaisesRegex(ValueError, 'bounded'):
                build_private_pc_first_model_stream(geometry(), dxt5(IMG1))

    def test_independent_stream_readback_mismatch_refused(self):
        from carbon_pc_bun_chunk_stream_gate import inspect_carbon_pc_chunk_stream
        actual = inspect_carbon_pc_chunk_stream(geometry()+dxt5(IMG1), 'either')
        with patch('carbon_pc_first_model_stream_assembly.inspect_carbon_pc_chunk_stream',
                   return_value={**actual, 'native_pc_distinct_texture_records': 77}):
            with self.assertRaisesRegex(ValueError, 'disagrees'):
                build_private_pc_first_model_stream(geometry(), dxt5(IMG1))

    def test_unverified_claims_and_private_identities_not_disclosed(self):
        _, report = build_private_pc_first_model_stream(geometry(), dxt5(IMG1))
        output = json.dumps(report)
        for value in (MODEL, IMG1, IMG2):
            self.assertNotIn(hex(value), output)
            self.assertNotIn(str(value), output)
        self.assertNotIn('SYNTHETIC_IMAGE', output)
        self.assertNotIn('100, 90, 200', output)
        self.assertIn('NOT_LOADABLE_PROOF', output)

    def test_identical_inputs_produce_identical_private_stream(self):
        g,t = geometry(),dxt5(IMG1)
        first = build_private_pc_first_model_stream(g,t)
        second = build_private_pc_first_model_stream(g,t)
        self.assertEqual(first,second)


if __name__ == '__main__':
    unittest.main()
