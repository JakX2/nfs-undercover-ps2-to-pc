#!/usr/bin/env python3
"""Read-only pairing of Z0 scene/visibility root framing across source platforms.

Checks complete nested frame boundaries for original L5/L2 RA/RB bundles.
Does not decode scene node payloads, visibility section references, collision
or the Carbon PC loader ABI. Never writes extracted game data.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip
from section_identity_anchor import MAX_BUNDLE, parse_rows

SCENE_ROOT = 0x80034100
VISIBILITY_ROOT = 0x80034150
STREAM_INDEX = 0x00034110
SCENE_CHILDREN = (0x34101, 0x34103, 0x34102, 0x3410D, 0x34105, 0x34107)
VISIBILITY_CHILDREN = (0x34151, 0x34152, 0x34156, 0x34155, 0x34153)
Z0_SECTION_NUMBER = 2600
MAX_ROOT_FRAME = 64 * 1024


def frame_children(blob, expected_id, expected_children):
    """Require a complete nested frame; return aggregate child lengths only."""
    if len(blob) < 8:
        raise ValueError('Truncated root header')
    root_id, size = struct.unpack_from('<II', blob)
    if root_id != expected_id or size + 8 > len(blob):
        raise ValueError('Missing or out-of-bounds expected root')
    end, cursor, children = size + 8, 8, []
    while cursor < end:
        if cursor + 8 > end:
            raise ValueError('Incomplete child header')
        cid, n = struct.unpack_from('<II', blob, cursor)
        if cursor + 8 + n > end:
            raise ValueError('Child frame overruns parent')
        children.append((cid, n))
        cursor += 8 + n
    if cursor != end or tuple(cid for cid, n in children) != tuple(expected_children):
        raise ValueError('Unexpected child framing/order')
    return {'frame_payload_bytes': size,
            'child_payload_bytes': {f'0x{cid:08x}': n for cid, n in children},
            'complete': True}


def find_unique_chunk(bundle, needle):
    pos, matches = 0, []
    while pos < len(bundle):
        if pos + 8 > len(bundle):
            raise ValueError('Truncated small bundle chunk header')
        cid, size = struct.unpack_from('<II', bundle, pos)
        end = pos + 8 + size
        if end > len(bundle):
            raise ValueError('Small bundle chunk out of bounds')
        if cid == needle:
            matches.append(bundle[pos:end])
        pos = end
    if len(matches) != 1:
        raise ValueError('Expected exactly one designated chunk in small bundle')
    return matches[0]


def locate_z0_row(index_chunk, stream_size):
    rows = parse_rows(index_chunk[8:], stream_size)
    if Z0_SECTION_NUMBER not in rows:
        raise ValueError('Missing Z0 section number')
    row = rows[Z0_SECTION_NUMBER]
    if row[:8].split(b'\0', 1)[0] != b'Z0':
        raise ValueError('Unexpected section name at Z0 number')
    return struct.unpack_from('<II', row, 0x14)


def inspect_one(bundle, stream_prefix, stream_size):
    index = find_unique_chunk(bundle, STREAM_INDEX)
    offset, section_size = locate_z0_row(index, stream_size)
    vis = frame_children(find_unique_chunk(bundle, VISIBILITY_ROOT),
                         VISIBILITY_ROOT, VISIBILITY_CHILDREN)
    if offset + 8 > len(stream_prefix):
        raise ValueError('Unreachable Z0 stream root in supplied prefix')
    if struct.unpack_from('<I', stream_prefix, offset)[0] != SCENE_ROOT:
        raise ValueError('Z0 does not start with scenery root')
    scene = frame_children(stream_prefix[offset:], SCENE_ROOT, SCENE_CHILDREN)
    if scene['frame_payload_bytes'] + 8 > section_size:
        raise ValueError('Scene root overflows declared Z0 stream section')
    return {'z0_scene_root': scene, 'small_bundle_visibility_root': vis,
            'z0_scene_frame_within_section': True}


def read_one(source, stem, sector):
    small = f'TRACKS/{stem}{sector}.BUN'
    stream = f'TRACKS/STREAM{stem}{sector}.BUN'
    if isinstance(source, SplitZip):
        bundle = source.read(small, limit=MAX_BUNDLE)
        stream_size = source.entries[stream][4]
        index = find_unique_chunk(bundle, STREAM_INDEX)
        offset, _ = locate_z0_row(index, stream_size)
        if offset + MAX_ROOT_FRAME > stream_size:
            raise ValueError('Insufficient bytes to inspect complete Z0 frame')
        prefix = source.read(stream, limit=offset + MAX_ROOT_FRAME, prefix=True)
    else:
        with zipfile.ZipFile(source) as z:
            if z.getinfo(small).file_size > MAX_BUNDLE:
                raise ValueError('Small bundle exceeds input safety bound')
            bundle = z.read(small)
            stream_size = z.getinfo(stream).file_size
            index = find_unique_chunk(bundle, STREAM_INDEX)
            offset, _ = locate_z0_row(index, stream_size)
            if offset + MAX_ROOT_FRAME > stream_size:
                raise ValueError('Insufficient bytes to inspect complete Z0 frame')
            with z.open(stream) as reader:
                prefix = reader.read(offset + MAX_ROOT_FRAME)
    return inspect_one(bundle, prefix, stream_size)


def analyze(pc_volumes, carbon_ps2_zip, carbon_wii_volumes,
            undercover_ps2_zip, undercover_wii_zip):
    sources = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2_zip), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(undercover_ps2_zip), 'L2'),
        'undercover_wii': (Path(undercover_wii_zip), 'L2'),
    }
    roots = {}
    for name, (source, stem) in sources.items():
        for sector in ('RA', 'RB'):
            roots[name + '_' + sector] = read_one(source, stem, sector)
    return {'validated_source_bundle_pairs': len(roots),
            'roots': roots,
            'limits': ('Valid nested root framing and 0x34110-to-Z0 source offset '
                       'only; no 0x34150 section-reference decoding, geometry '
                       'payload semantics, collision proof, writer or runtime test.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pc-volumes', nargs='+', type=Path, required=True)
    parser.add_argument('--carbon-ps2-zip', type=Path, required=True)
    parser.add_argument('--carbon-wii-volumes', nargs='+', type=Path, required=True)
    parser.add_argument('--undercover-ps2-zip', type=Path, required=True)
    parser.add_argument('--undercover-wii-zip', type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(analyze(a.pc_volumes, a.carbon_ps2_zip, a.carbon_wii_volumes,
                             a.undercover_ps2_zip, a.undercover_wii_zip), indent=2))


if __name__ == '__main__':
    main()
