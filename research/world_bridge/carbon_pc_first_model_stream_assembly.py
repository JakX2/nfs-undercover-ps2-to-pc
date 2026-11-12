#!/usr/bin/env python3
"""Offline assembly gate for ONE Undercover model + its PC DXT material set.

The existing original-free converters independently generate a complete
indexed PC eSolid root and an indexed PC DXT5 texture root in memory.
This module creates a single bounded top-level chunk stream, reparses
the COMPLETE stream with the independent Carbon PC resource readers,
and checks local material/texture closure. It never installs, writes,
injects, exports or registers the bytes.

A valid stream is only PC-parser-shaped, not proved compatible with
Carbon's CreateResourceFile/BeginLoading ABI or original .BUN format.
"""
import struct

from carbon_pc_bun_chunk_stream_gate import (
    MAX_BUN_BYTES, inspect_carbon_pc_chunk_stream,
)
from carbon_pc_resource_namespace_gate import (
    _model_and_materials, _texture_ids,
)
from geometry_hash_control import GEOM
from texture_metadata_pixel_bridge import ROOT as TEXTURE, parse_pack


def build_private_pc_first_model_stream(geometry_root, texture_root,
                                         require_dxt5=True):
    """Return (private combined bytes, redacted audit report), never write.

    Input must be exactly one indexed Carbon-PC-shaped geometry root and
    one PC-format texture root. Every texture-table entry must have a
    corresponding candidate image and no extra image identities are
    allowed for this first-model experiment. A second, independently
    implemented scanner reparses the whole assembled file.
    """
    if (type(geometry_root) is not bytes or type(texture_root) is not bytes or
            type(require_dxt5) is not bool):
        raise ValueError('Expected immutable PC geometry/texture input roots')
    if (len(geometry_root) < 40 or len(texture_root) < 40 or
            len(geometry_root) + len(texture_root) > MAX_BUN_BYTES):
        raise ValueError('Candidate PC chunk stream exceeds bounded format')
    for blob, kind in ((geometry_root, GEOM), (texture_root, TEXTURE)):
        tag, size = struct.unpack_from('<II', blob)
        if tag != kind or size != len(blob) - 8:
            raise ValueError('PC root must have one exact top-level chunk frame')

    models, materials = _model_and_materials(geometry_root)
    images = _texture_ids(texture_root)
    if len(models) != 1 or not materials:
        raise ValueError('Only one complete indexed model is supported')
    if materials != images:
        raise ValueError('Candidate image identities must exactly match full material table')

    records = parse_pack(texture_root, 'pc')['records']
    if require_dxt5 and any(record['codec'] != 38 for record in records.values()):
        raise ValueError('Expected DXT5-only Undercover conversion candidate')

    # Carbon PC top-level chunk framing is little-endian; this does not
    # manufacture any unknown stream index, loader header or scene metadata.
    stream = geometry_root + texture_root
    check = inspect_carbon_pc_chunk_stream(stream, 'either')
    if (check['source_total_bytes'] != len(stream) or
            check['top_level_frames'] != 2 or
            check['native_pc_geometry_roots'] != 1 or
            check['native_pc_texture_roots'] != 1 or
            check['top_level_unknown_frames'] != 0 or
            check['native_pc_distinct_model_records'] != 1 or
            check['native_pc_distinct_texture_records'] != len(images)):
        raise ValueError('Combined original-free PC resource stream readback disagrees')

    # Two checks are independent: the earlier component-local index and
    # material parser, and the full concatenated stream inventory.
    return stream, {
        'scope': 'PRIVATE_OFFLINE_ONE_MODEL_PC_CHUNK_STREAM_NOT_LOADABLE_PROOF',
        'pc_candidate_chunk_stream_bytes_in_memory': len(stream),
        'pc_geometry_root_bytes': len(geometry_root),
        'pc_texture_root_bytes': len(texture_root),
        'top_level_frames': check['top_level_frames'],
        'native_pc_geometry_roots': 1,
        'native_pc_texture_roots': 1,
        'pc_candidate_model_records': len(models),
        'pc_candidate_texture_records': len(images),
        'full_material_table_identities_backed': True,
        'no_unreferenced_candidate_texture_identities': True,
        'pc_dxt5_only': all(r['codec'] == 38 for r in records.values()),
        'complete_pc_chunk_framing_reparsed': True,
        'retail_carbon_bun_container_abi_verified': False,
        'retail_carbon_runtime_registration_verified': False,
        'pc_loader_accepted_candidate_verified': False,
        'undercover_model_rendered_in_game': False,
        'installed_or_exported_candidate': False,
        'private_model_texture_ids_and_pixels_disclosed': False,
        'limitations': ('The two original-free PC roots form a complete '
                        'synthetic chunk stream; missing original Carbon '
                        'stream registry, resource init stage, binary ABI, '
                        'world placement, collider and renderer behavior '
                        'have not been reconstructed. No installation '
                        'or in-game rendering is performed.'),
    }
