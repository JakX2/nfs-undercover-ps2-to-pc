#!/usr/bin/env python3
"""Read-only header profile and in-memory, same-size PC DXT1 texture overlay.

This intentionally preserves every uninterpreted source byte. It does NOT
register a texture with Carbon PC, create new identities, or write to disk.
Caller-provided source packs and pixels are never logged or serialized here.
"""
from collections import Counter
import struct

from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import _chunks, aligned_pixel_array
from synthetic_dxt1_texture_writer import encode_dxt1_mips
from pc_dxt_reference_decode import decode_dxt_base

MAX_PROFILE_SECTIONS = 16


def _profile(section):
    parsed = parse_pack(section, 'pc')
    aligned, pad = aligned_pixel_array(section, parsed['records'])
    cid, root_len = struct.unpack_from('<II', section)
    root = _chunks(section, 8, 8 + root_len)
    desc = _chunks(section, root[1][1], root[1][2])
    pix = _chunks(section, root[3][1], root[3][2])
    if [r[0] for r in desc] != [0x33310001, 0x33310002, 0x33310004, 0x33310005]:
        raise ValueError('Unexpected PC descriptor structure')
    header = bytes(section[desc[0][1]:desc[0][2]])
    platform = memoryview(section)[desc[3][1]:desc[3][2]]
    if len(header) != 124 or len(platform) != 24 * len(parsed['records']):
        raise ValueError('Unexpected PC descriptor header/platform length')
    fourcc_only = 0
    for k in range(0, len(platform), 24):
        row = platform[k:k+24]
        if bytes(row[:12]) == bytes(12) and bytes(row[16:]) == bytes(8):
            fourcc_only += 1
    return {'header': header, 'texture_count': len(parsed['records']),
            'dxt1_count': sum(m['codec'] == 34 for m in parsed['records'].values()),
            'fourcc_only': fourcc_only, 'pad': pad,
            'zero_root_framing': (root[0][2]-root[0][1], root[2][2]-root[2][1]),
            'pixel_header_size': pix[0][2]-pix[0][1],
            'pixel_framing_size': pix[1][2]-pix[1][1],
            'aligned_length': len(aligned)}


def profile_pc_texture_headers(sections):
    """Return aggregates only, never source field values, names or hashes.

    Stable offsets do not establish pointers, ABI semantics or loader support.
    """
    if not isinstance(sections, (list, tuple)) or not 1 <= len(sections) <= MAX_PROFILE_SECTIONS:
        raise ValueError('Invalid PC texture section profile count')
    checked = [_profile(section) for section in sections]
    first = checked[0]['header']
    nonzero_words = tuple(i for i in range(0,124,4)
                          if any(int.from_bytes(row['header'][i:i+4], 'little')
                                 for row in checked))
    return {'source_sections': len(checked),
            'total_pc_texture_records': sum(x['texture_count'] for x in checked),
            'total_pc_dxt1_records': sum(x['dxt1_count'] for x in checked),
            'platform_records_fourcc_only': sum(x['fourcc_only'] for x in checked),
            'descriptor_header_size': 124,
            'descriptor_headers_identical': all(x['header'] == first for x in checked),
            'descriptor_headers_all_zero': all(not any(x['header']) for x in checked),
            'descriptor_header_nonzero_u32_offsets': list(nonzero_words),
            'root_framing_sizes': [list(x['zero_root_framing']) for x in checked],
            'pixel_header_sizes': [x['pixel_header_size'] for x in checked],
            'pixel_framing_sizes': [x['pixel_framing_size'] for x in checked],
            'pixel_alignment_padding_sizes': [x['pad'] for x in checked]}


def _source_image_span(section, meta):
    """Locate absolute aligned payload slice; never derive it from a magic 120."""
    _, root_len = struct.unpack_from('<II', section)
    root = _chunks(section, 8, 8 + root_len)
    pixel_children = _chunks(section, root[3][1], root[3][2])
    start = pixel_children[2][1]
    actual_pixel_base = start + (-start % 128)
    a = actual_pixel_base + meta['image_offset']
    b = a + meta['image_bytes']
    if a < actual_pixel_base or b > pixel_children[2][2]:
        raise ValueError('Original PC DXT image span exceeds aligned payload')
    return a, b


def overlay_existing_dxt1(section, identity, opaque_rgba):
    """Change exactly an existing PC DXT1 image span, preserving all other bytes.

    A valid, caller-supplied Carbon-shaped PC section is REQUIRED. A new
    texture hash, dimension, mip count, sampler flag or descriptor is never
    introduced. Returns (modified_section_bytes, aggregate_public_summary).
    No output file is created. This is not a runtime loading claim.
    """
    if not isinstance(section, (bytes, bytearray)):
        raise ValueError('Expected bounded original PC section bytes')
    if type(identity) is not int or not 0 < identity <= 0xffffffff:
        raise ValueError('Invalid existing texture identity')
    parsed = parse_pack(section, 'pc')
    aligned_pixel_array(section, parsed['records'])
    if identity not in parsed['records']:
        raise KeyError('Texture does not exist in this source section')
    meta = parsed['records'][identity]
    if meta['codec'] != 34:
        raise ValueError('Only existing opaque DXT1 entries may be overlaid')
    image, spans = encode_dxt1_mips(opaque_rgba, meta['width'], meta['height'], meta['mip_levels'])
    if len(image) != meta['image_bytes'] or spans[0][3] != meta['base_image_bytes']:
        raise ValueError('Encoded DXT1 mip chain differs from original source byte sizes')
    a, b = _source_image_span(section, meta)
    before = bytes(section)
    result = bytearray(before)
    result[a:b] = image
    if len(result) != len(before) or result[:a] != before[:a] or result[b:] != before[b:]:
        raise ValueError('Overlay wrote outside the existing DXT1 payload')
    rebuilt = bytes(result)
    after_meta = parse_pack(rebuilt, 'pc')['records']
    aligned_pixel_array(rebuilt, after_meta)
    if after_meta != parsed['records']:
        raise ValueError('Overlay modified original texture metadata')
    decoded = decode_dxt_base(image[:spans[0][3]], meta['width'], meta['height'], b'DXT1')
    if len(decoded) != meta['width'] * meta['height'] * 4 or any(decoded[i] != 255 for i in range(3, len(decoded), 4)):
        raise ValueError('Overlay encoded unexpected DXT1 alpha')
    changed = sum(x != y for x,y in zip(before[a:b], image))
    return rebuilt, {'source_texture_count': len(parsed['records']),
                     'overlaid_image_bytes': len(image),
                     'overlaid_mip_levels': meta['mip_levels'],
                     'changed_image_bytes': changed,
                     'unchanged_metadata_and_other_resources': True,
                     'opaque_decoded_base_level': True}
