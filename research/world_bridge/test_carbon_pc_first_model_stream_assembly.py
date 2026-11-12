"""Source-only PC-shaped one-model chunk-stream assembly regressions.

Only fictional triangles, synthetic 8x8 RGBA and synthetic model/texture
IDs. No retail originals or external loader required by GitHub CI.
"""
import json
from pathlib import Path
import tempfile
import struct
import unittest
from unittest.mock import patch

from carbon_pc_first_model_stream_assembly import (
    build_private_pc_first_model_stream,
    export_private_pc_candidate_stream,
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
        self.assertEqual(blob, t + g)
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
        self.assertTrue(report['native_carbon_section_texture_before_geometry'])
        self.assertTrue(report['native_carbon_geometry_start_aligned_16'])
        self.assertTrue(report['missing_carbon_scenery_root'])
        self.assertTrue(report['missing_carbon_postscene_control'])
        self.assertFalse(report['complete_native_carbon_stream_section'])
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
        self.assertEqual(blob[:len(t)], t)
        self.assertEqual(len(t) % 16, 0)

    def test_no_unresolved_or_extra_texture_identity(self):
        g = geometry((IMG1, IMG2))
        for bad in (dxt5(IMG1), dxt5(IMG1, IMG2, 0x12345678)):
            with self.subTest(textures=len(parse_pack(bad,'pc')['records'])):
                with self.assertRaisesRegex(ValueError, 'exactly match'):
                    build_private_pc_first_model_stream(g, bad)

    def test_wrong_texture_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            build_private_pc_first_model_stream(geometry(), dxt5(IMG2))

    def test_private_stream_uses_observed_carbon_pc_root_order(self):
        g, t = geometry(), dxt5(IMG1)
        b, report = build_private_pc_first_model_stream(g, t)
        self.assertEqual(struct.unpack_from('<I', b, 0)[0], 0xB3300000)
        self.assertEqual(struct.unpack_from('<I', b, len(t))[0], 0x80134000)
        self.assertEqual(len(t) % 16, 0)
        self.assertFalse(report['complete_native_carbon_stream_section'])

    def test_unaligned_native_texture_root_not_silently_padded(self):
        # A synthetically malformed alignment must fail closed,
        # rather than invent an unknown inter-root padding chunk.
        g, t = geometry(), dxt5(IMG1)
        with patch('carbon_pc_first_model_stream_assembly._texture_ids',
                   return_value=frozenset({IMG1})), \
             patch('carbon_pc_first_model_stream_assembly.parse_pack',
                   return_value={'records': {IMG1: {'codec': 38}}}):
            malformed = t[:4] + struct.pack('<I', len(t) - 7) + t[8:] + b'X'
            with self.assertRaises(ValueError):
                build_private_pc_first_model_stream(g, malformed)

    def test_previous_geometry_first_export_rejected(self):
        g, t = geometry(), dxt5(IMG1)
        with tempfile.TemporaryDirectory() as td:
            candidate = Path(td) / 'legacy.pcchunk'
            with self.assertRaisesRegex(ValueError, 'texture-first'):
                export_private_pc_candidate_stream(g+t, candidate, apply=True)
            self.assertFalse(candidate.exists())

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
        actual = inspect_carbon_pc_chunk_stream(dxt5(IMG1)+geometry(), 'either')
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


class PrivateCandidateExportTests(unittest.TestCase):
    def setUp(self):
        self.owned = tempfile.TemporaryDirectory()
        self.addCleanup(self.owned.cleanup)
        self.path = Path(self.owned.name) / 'undercover-one-model.pcchunk'
        self.source, _ = build_private_pc_first_model_stream(
            geometry(), dxt5(IMG1))

    def test_explicit_private_new_file_only(self):
        result = export_private_pc_candidate_stream(
            self.source, self.path, apply=True)
        self.assertEqual(self.path.read_bytes(), self.source)
        self.assertEqual(result['private_file_bytes'], len(self.source))
        self.assertTrue(result['private_file_created'])
        self.assertFalse(result['carbon_loader_accepted_file'])
        self.assertFalse(result['stock_carbon_files_modified'])
        self.assertFalse(result['in_game_model_rendered'])
        self.assertNotIn(str(self.path), json.dumps(result))
        self.assertNotIn(str(MODEL), json.dumps(result))

    def test_default_no_private_write(self):
        with self.assertRaisesRegex(ValueError, 'explicit'):
            export_private_pc_candidate_stream(self.source, self.path)
        self.assertFalse(self.path.exists())

    def test_existing_candidate_never_overwritten_or_deleted(self):
        self.path.write_bytes(b'KEEP MY USER FILE')
        with self.assertRaises(FileExistsError):
            export_private_pc_candidate_stream(
                self.source, self.path, apply=True)
        self.assertEqual(self.path.read_bytes(), b'KEEP MY USER FILE')

    def test_wrong_extension_never_written(self):
        for ext in ('.bun', '.exe', '.bin', ''):
            other = Path(self.owned.name) / ('test' + ext)
            with self.subTest(ext=ext), self.assertRaises(ValueError):
                export_private_pc_candidate_stream(
                    self.source, other, apply=True)
            self.assertFalse(other.exists())

    def test_corrupt_stream_refused_before_file_creation(self):
        for corrupted in (
            self.source[:-1], self.source + b'extra',
            self.source[:20] + b'corrupt' + self.source[27:],
            bytearray(self.source),
        ):
            with self.subTest(type=type(corrupted).__name__), self.assertRaises(ValueError):
                export_private_pc_candidate_stream(
                    corrupted, self.path, apply=True)
        self.assertFalse(self.path.exists())

    def test_unresolved_material_candidate_cannot_be_exported(self):
        wrong = dxt5(IMG1) + geometry((IMG1, IMG2))
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            export_private_pc_candidate_stream(wrong, self.path, apply=True)
        self.assertFalse(self.path.exists())

    def test_rejects_output_symlinks(self):
        existing = Path(self.owned.name) / 'target.pcchunk'
        existing.write_bytes(b'keep')
        alias = Path(self.owned.name) / 'alias.pcchunk'
        try:
            alias.symlink_to(existing)
        except (OSError, NotImplementedError):
            self.skipTest('Host cannot create symlinks')
        with self.assertRaises(ValueError):
            export_private_pc_candidate_stream(self.source, alias, apply=True)
        self.assertEqual(existing.read_bytes(), b'keep')

    def test_rejects_absent_output_directory(self):
        missing = Path(self.owned.name) / 'missing' / 'first.pcchunk'
        with self.assertRaises(ValueError):
            export_private_pc_candidate_stream(self.source, missing, apply=True)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
