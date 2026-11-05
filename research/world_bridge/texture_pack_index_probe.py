"""Bounded, source-independent streamed texture-index inspection.

This is a read-only index/coverage probe, not a texture decoder or writer.
Original texture hashes and serialized resource data are never emitted.
"""
from collections import Counter
import struct

TEXTURE_ROOT = 0xB3300000
DESCRIPTOR_ROOT = 0xB3310000
PIXEL_ROOT = 0xB3320000
HASH_TABLE = 0x33310002
MAX_SECTION_BYTES = 32 * 1024 * 1024
MAX_TEXTURES = 32768


def children(blob):
    """Bounded immediate chunk reader, rejecting truncated child frames."""
    out = []
    pos = 0
    while pos < len(blob):
        if pos + 8 > len(blob):
            raise ValueError('Truncated child chunk')
        tag, length = struct.unpack_from('<II', blob, pos)
        end = pos + 8 + length
        if end > len(blob):
            raise ValueError('Child chunk exceeds parent bounds')
        out.append((tag, blob[pos + 8:end]))
        pos = end
    return out


def parse_section_index(section):
    """Read a B3300000 root anchored at a stream section's first byte.

    Returns an in-memory frozen set of texture hashes. Caller must not publish
    that set: only aggregate statistics are appropriate for shared reports.
    """
    if not 24 <= len(section) <= MAX_SECTION_BYTES:
        raise ValueError('Texture section exceeds safety bound')
    tag, size = struct.unpack_from('<II', section)
    if tag != TEXTURE_ROOT or size < 32 or size + 8 > len(section):
        raise ValueError('Missing complete section-start texture root')
    root = children(section[8:8 + size])
    if [k for k, _ in root] != [0, DESCRIPTOR_ROOT, 0, PIXEL_ROOT]:
        raise ValueError('Unexpected texture root child order')
    if not root[3][1]:
        raise ValueError('Empty serialized texture-pixel resource')
    desc = children(root[1][1])
    if [k for k, _ in desc] != [0x33310001, HASH_TABLE, 0x33310004, 0x33310005]:
        raise ValueError('Unexpected descriptor child order')
    if any(not desc[i][1] for i in (0, 2, 3)):
        raise ValueError('Empty required texture descriptor field')
    data = desc[1][1]
    if not data or len(data) % 8 or len(data) // 8 > MAX_TEXTURES:
        raise ValueError('Malformed 8-byte texture index table')
    rows = tuple(struct.iter_unpack('<II', data))
    if any(pointer for _, pointer in rows):
        raise ValueError('Nonzero serialized texture index pointer')
    hashes = tuple(h for h, _ in rows)
    if not all(hashes) or hashes != tuple(sorted(set(hashes))):
        raise ValueError('Texture index has zero, duplicate or unordered hash')
    return frozenset(hashes)


def summarize_index(index, solid_texture_tables):
    """Aggregate source solid hash references without exporting actual hashes."""
    tables = tuple(solid_texture_tables)
    if not tables:
        raise ValueError('Missing verified solid texture tables')
    references = []
    for table in tables:
        if not table or any(type(h) is not int or not 0 < h <= 0xffffffff for h in table):
            raise ValueError('Invalid local eSolid texture table')
        references.extend(table)
    referenced = frozenset(references)
    return {'solid_occurrences': len(tables),
            'solid_texture_reference_occurrences': len(references),
            'distinct_solid_texture_hashes': len(referenced),
            'indexed_texture_hashes': len(index),
            'referenced_in_local_index': len(referenced & index),
            'referenced_outside_local_index': len(referenced - index),
            'indexed_but_not_referenced_by_local_solids': len(index - referenced)}


def compare_platform_indexes(pc_index, ps2_index, pc_solid_tables, ps2_solid_tables):
    """Check same-source texture references before comparing platform indexes."""
    a = tuple(pc_solid_tables)
    b = tuple(ps2_solid_tables)
    if not a or a != b:
        raise ValueError('PC and PS2 solid texture tables are not identical')
    return {'solid_tables_identical': True,
            'common_index_hashes': len(pc_index & ps2_index),
            'pc_only_index_hashes': len(pc_index - ps2_index),
            'ps2_only_index_hashes': len(ps2_index - pc_index),
            'ps2_index_is_subset_of_pc': ps2_index <= pc_index}
