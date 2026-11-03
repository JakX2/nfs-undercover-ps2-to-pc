#!/usr/bin/env python3
"""Read-only, bounded visibility-edge audit across 5 owner-provided sources.

Two candidate variable-length records in 0x80034150 are tested against all
five platforms and both track regions. Row semantics are not a verified
Carbon PC loader ABI. This script does not produce modified game content.
"""
import argparse
import json
import math
from pathlib import Path
import struct
import zipfile

from scenery_visibility_anchor import (find_unique_chunk, VISIBILITY_ROOT,
                                        VISIBILITY_CHILDREN)
from track_bundle_probe import SplitZip

BOUNDARY_ID = 0x34152
DRIVABLE_ID = 0x34153
MAX_BOUNDARY_POINTS = 16
MAX_VISIBLE_CAPACITY = 128
MAX_BUNDLE_BYTES = 8 * 1024 * 1024


def parse_boundaries(data):
    """Candidate header 48 bytes + NumPoints*8 bytes, with NumPoints at +0x0A."""
    result = {}
    offset = 0
    while offset < len(data):
        if offset + 48 > len(data):
            raise ValueError('Truncated visibility boundary header')
        section, count = struct.unpack_from('<hB', data, offset + 8)
        if not 0 < section < 32768 or not 1 <= count <= MAX_BOUNDARY_POINTS:
            raise ValueError('Invalid visibility boundary section or point count')
        size = 48 + 8 * count
        if offset + size > len(data):
            raise ValueError('Visibility boundary exceeds chunk')
        if section in result:
            raise ValueError('Duplicate visibility boundary section')
        # Finite-float check of *candidate* coordinate words (not an ABI claim).
        numbers = struct.unpack_from('<' + 'f' * (6 + 2 * count), data, offset + 12)
        if not all(math.isfinite(x) for x in numbers):
            raise ValueError('Nonfinite visibility boundary coordinates')
        result[section] = count
        offset += size
    return result


def parse_drivable_sections(data):
    """Candidate row 20 bytes + 2*MaxVisibleSectionCapacity bytes."""
    result = {}
    offset = 0
    while offset < len(data):
        if offset + 20 > len(data):
            raise ValueError('Truncated drivable visibility record')
        section, most, capacity, count = struct.unpack_from('<hBBh', data, offset + 12)
        if (not 0 < section < 32768 or not 0 <= most <= capacity <= MAX_VISIBLE_CAPACITY
                or not 0 <= count <= capacity):
            raise ValueError('Invalid drivable visibility record counts')
        size = 20 + 2 * capacity
        if offset + size > len(data):
            raise ValueError('Drivable visibility record exceeds chunk')
        if section in result:
            raise ValueError('Duplicate drivable visibility section')
        refs = struct.unpack_from('<' + str(count) + 'h', data, offset+18) if count else ()
        if any(n <= 0 for n in refs) or len(set(refs)) != len(refs):
            raise ValueError('Invalid or repeated drivable visibility reference')
        result[section] = {'refs': refs, 'capacity':capacity, 'most':most}
        offset += size
    return result


def visibility_children(bundle):
    root = find_unique_chunk(bundle, VISIBILITY_ROOT)
    root_id, size = struct.unpack_from('<II', root)
    if root_id != VISIBILITY_ROOT or size + 8 != len(root):
        raise ValueError('Malformed visibility manager root')
    cursor, result, order = 8, {}, []
    while cursor < len(root):
        if cursor + 8 > len(root):
            raise ValueError('Truncated visibility child header')
        cid, length = struct.unpack_from('<II', root, cursor)
        end = cursor + 8 + length
        if end > len(root) or cid in result:
            raise ValueError('Out-of-bounds or duplicate visibility child')
        result[cid] = root[cursor+8:end]
        order.append(cid)
        cursor = end
    if tuple(order) != VISIBILITY_CHILDREN:
        raise ValueError('Unexpected visibility child order')
    return result


def summarize(children):
    boundary = parse_boundaries(children[BOUNDARY_ID])
    drivable = parse_drivable_sections(children[DRIVABLE_ID])
    refs = [v for record in drivable.values() for v in record['refs']]
    return {'boundary_sections':len(boundary),
            'drivable_sections':len(drivable),
            'visibility_references':len(refs),
            'distinct_visibility_target_ids':len(set(refs)),
            'largest_visible_capacity':max((r['capacity'] for r in drivable.values()),default=0),
            'boundary_records_have_unique_ids':True,
            'drivable_records_have_unique_ids':True,
            'all_visibility_links_positive_and_unique_per_row':True}


def analyze(pc_volumes, carbon_ps2, carbon_wii_volumes, uc_ps2, uc_wii):
    archives = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(uc_ps2), 'L2'),
        'undercover_wii': (Path(uc_wii), 'L2'),
    }
    raw = {}
    stats = {}
    for label,(archive,stem) in archives.items():
        for region in ('RA','RB'):
            member = f'TRACKS/{stem}{region}.BUN'
            if isinstance(archive, SplitZip):
                payload = archive.read(member, limit=MAX_BUNDLE_BYTES)
            else:
                with zipfile.ZipFile(archive) as z:
                    if z.getinfo(member).file_size > MAX_BUNDLE_BYTES:
                        raise ValueError('Small visibility bundle too large')
                    payload = z.read(member)
            key = label+'_'+region
            raw[key] = visibility_children(payload)
            stats[key] = summarize(raw[key])
    comparisons = {}
    for a,b in (('carbon_pc','carbon_ps2'),('carbon_pc','carbon_wii'),
                ('carbon_ps2','carbon_wii'),('undercover_ps2','undercover_wii')):
        for region in ('RA','RB'):
            left,right = raw[a+'_'+region], raw[b+'_'+region]
            comparisons[a+'_vs_'+b+'_'+region] = {
                'identical_child_payloads':sum(left[cid] == right[cid] for cid in VISIBILITY_CHILDREN),
                'total_children':len(VISIBILITY_CHILDREN),
                'boundary_payload_byte_equal':left[BOUNDARY_ID] == right[BOUNDARY_ID],
                'drivable_payload_byte_equal':left[DRIVABLE_ID] == right[DRIVABLE_ID],
            }
    return {'sources':stats,'comparisons':comparisons,
            'limits':('This checks complete visibility frames, candidate variable-size '
                      'records, signed section numbers and in-row reference uniqueness '
                      'only. References may legitimately point outside the current '
                      'RA/RB streaming table (LOD or other file classes). The loader '
                      'ABI, cross-game section relocation, runtime rendering and '
                      'collision remain unverified.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--carbon-wii-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-wii-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.carbon_wii_volumes,
                             a.undercover_ps2_zip,a.undercover_wii_zip),indent=2))

if __name__=='__main__':main()
