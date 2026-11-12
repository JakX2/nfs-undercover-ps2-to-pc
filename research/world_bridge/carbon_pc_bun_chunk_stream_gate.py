#!/usr/bin/env python3
"""Offline bounded Carbon PC chunk-stream inventory for original .BUN controls.

A complete file may contain several top-level resource frames, not just
one extracted 0x80134000 eSolid or 0xB3300000 texture root. Parse only
successive top-level little-endian (type, payload-size) frames; NEVER
signature-scan arbitrary bytes for an embedded resource.

This confirms independently parsed PC resource structure, not that any
given file is accepted by Carbon's external loader or renders in game.
No copyrighted source bytes, model hashes, texture hashes or names are
included in the returned summary.
"""
import struct

from geometry_hash_control import GEOM, PLATFORM_PC, parse_geometry_root
from texture_metadata_pixel_bridge import ROOT as TEXTURE, parse_pack

MAX_BUN_BYTES = 32 * 1024 * 1024
MAX_FRAMES = 4096


def inspect_carbon_pc_chunk_stream(blob, expected_kind):
    """Return redacted structural counts for a bounded complete PC chunk stream.

    expected_kind is geometry, texture, or either. The strict caller
    can require its known-good original Carbon control to contain the
    expected native resource type. Unknown top-level chunks are counted
    but never treated as proof of registration or renderability.
    """
    if (type(blob) is not bytes or not 40 <= len(blob) <= MAX_BUN_BYTES or
            expected_kind not in ('geometry', 'texture', 'either')):
        raise ValueError('Invalid bounded Carbon PC chunk-stream input')

    offset = 0
    frames = 0
    other_frames = 0
    geometry_roots = 0
    texture_roots = 0
    model_ids = set()
    texture_ids = set()
    while offset < len(blob):
        if len(blob) - offset < 8:
            raise ValueError('Truncated Carbon PC chunk-stream tail')
        if frames >= MAX_FRAMES:
            raise ValueError('Too many Carbon PC top-level frames')
        tag, length = struct.unpack_from('<II', blob, offset)
        if length > len(blob) - offset - 8:
            raise ValueError('Carbon PC top-level frame exceeds file bounds')
        end = offset + 8 + length
        frame = blob[offset:end]
        if tag == GEOM:
            info = parse_geometry_root(frame)
            if info['platform'] != PLATFORM_PC:
                raise ValueError('Non-PC geometry root inside Carbon control')
            if model_ids & info['hashes']:
                raise ValueError('Duplicate model identities across PC roots')
            model_ids.update(info['hashes'])
            geometry_roots += 1
        elif tag == TEXTURE:
            info = parse_pack(frame, 'pc')
            ids = set(info['records'])
            if texture_ids & ids:
                raise ValueError('Duplicate texture identities across PC roots')
            texture_ids.update(ids)
            texture_roots += 1
        else:
            other_frames += 1
        frames += 1
        offset = end

    if (geometry_roots + texture_roots == 0 or
            (expected_kind == 'geometry' and not geometry_roots) or
            (expected_kind == 'texture' and not texture_roots)):
        raise ValueError('No independently validated native PC resource of requested kind')

    return {
        'scope': 'OFFLINE_CARBON_PC_CHUNK_FRAMING_NOT_LOADER_COMPATIBILITY',
        'complete_top_level_chunk_stream': True,
        'source_total_bytes': len(blob),
        'top_level_frames': frames,
        'top_level_unknown_frames': other_frames,
        'native_pc_geometry_roots': geometry_roots,
        'native_pc_texture_roots': texture_roots,
        'native_pc_distinct_model_records': len(model_ids),
        'native_pc_distinct_texture_records': len(texture_ids),
        'top_level_framing_validated': True,
        'carbon_bun_loader_acceptance_verified': False,
        'carbon_runtime_registration_verified': False,
        'carbon_in_game_rendering_verified': False,
        'private_resource_identifiers_disclosed': False,
    }
