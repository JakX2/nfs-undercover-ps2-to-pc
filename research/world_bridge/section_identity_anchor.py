#!/usr/bin/env python3
"""Read-only world-section identity and spatial invariants across five sources.

No original game bytes, names, or per-section fields are emitted. Markers and
field names are research hypotheses supported by the Most Wanted reconstruction,
not proof of a Carbon PC loader ABI or an installable conversion.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import zipfile

from track_bundle_probe import SplitZip
from track_stream_section_probe import find_chunk

ROW_SIZE = 92
MIB = 1024 * 1024
MAX_PREFIX_MIB = 64
MAX_BUNDLE = 8 * MIB
RESOURCE_IDS = {
    0x80134000: 'geometry_pack',
    0x80034100: 'scenery_section',
    0xB3300000: 'texture_pack',
    0x0003B802: 'collision_grid_island_data',
    0x0003BC00: 'emitter_system',
}


def parse_rows(payload, stream_size):
    """Check 92-byte rows against bounded stream sizes and preserve field bytes."""
    if not payload or len(payload) % ROW_SIZE:
        raise ValueError('Not a nonempty series of 92-byte rows')
    if type(stream_size) is not int or stream_size < 1:
        raise ValueError('Invalid stream file size')
    records = {}
    previous_end = 0
    for i in range(0, len(payload), ROW_SIZE):
        row = payload[i:i + ROW_SIZE]
        raw_name = row[:8].split(b'\0', 1)[0]
        if not raw_name or any(x < 32 or x > 126 for x in raw_name):
            raise ValueError('Bad section name')
        section = struct.unpack_from('<h', row, 8)[0]
        offset, size, compressed = struct.unpack_from('<3I', row, 0x14)
        cx, cy, radius = struct.unpack_from('<3f', row, 0x28)
        if section in records:
            raise ValueError('Duplicate section number')
        if not all(math.isfinite(x) for x in (cx, cy, radius)) or radius < 0:
            raise ValueError('Nonfinite coordinates or negative radius')
        if not size or not compressed or offset + max(size, compressed) > stream_size:
            raise ValueError('Empty or out-of-bounds section')
        if offset < previous_end:
            raise ValueError('Overlapping or unordered stream section ranges')
        previous_end = offset + max(size, compressed)
        records[section] = row
    return records


def summarize(rows):
    return {
        'rows': len(rows),
        'rows_with_zero_spatial_triplet': sum(r[0x28:0x34] == bytes(12) for r in rows.values()),
        'filetype_one': sum(struct.unpack_from('<I', r, 0x10)[0] == 1 for r in rows.values()),
        'status_zero': sum(struct.unpack_from('<I', r, 0x0c)[0] == 0 for r in rows.values()),
        'sizes_equal_compressed': sum(r[0x18:0x1c] == r[0x1c:0x20] for r in rows.values()),
        'offsets_aligned_2048': sum(struct.unpack_from('<I', r, 0x14)[0] % 2048 == 0 for r in rows.values()),
    }


def compare_rows(left, right):
    shared = left.keys() & right.keys()
    same_spatial = {k for k in shared if left[k][0x28:0x34] == right[k][0x28:0x34]}
    same_zero = sum(left[k][0x28:0x34] == bytes(12) for k in same_spatial)
    return {
        'shared_section_numbers': len(shared),
        'only_left': len(left) - len(shared),
        'only_right': len(right) - len(shared),
        'matching_names': sum(left[k][:8] == right[k][:8] for k in shared),
        'matching_section_priorities': sum(left[k][0x24:0x28] == right[k][0x24:0x28] for k in shared),
        'matching_exact_spatial_triplets': len(same_spatial),
        'matching_both_zero_spatial_triplets': same_zero,
        'matching_nonzero_spatial_triplets': len(same_spatial) - same_zero,
        'different_spatial_triplets': len(shared) - len(same_spatial),
        'matching_section_checksum_field': sum(left[k][0x34:0x38] == right[k][0x34:0x38] for k in shared),
        'matching_stream_offsets': sum(left[k][0x14:0x18] == right[k][0x14:0x18] for k in shared),
        'matching_serialized_sizes': sum(left[k][0x18:0x1c] == right[k][0x18:0x1c] for k in shared),
    }


def classify_marker(prefix, offset):
    """Classify a candidate chunk marker at a section start, without decoding it."""
    if offset < 0 or offset + 8 > len(prefix):
        return None
    (identifier,) = struct.unpack_from('<I', prefix, offset)
    if identifier in RESOURCE_IDS:
        return RESOURCE_IDS[identifier]
    if identifier == 0:
        # Some platforms add framing before the first geometry pack.
        end = min(len(prefix), offset + 128)
        at = prefix.find(struct.pack('<I', 0x80134000), offset + 8, end)
        if at >= 0:
            return 'geometry_pack_after_initial_framing'
    return 'other_or_unresolved'


def sample_markers(rows, prefix):
    counts = Counter()
    for row in rows.values():
        offset = struct.unpack_from('<I', row, 0x14)[0]
        marker = classify_marker(prefix, offset)
        if marker is not None:
            counts[marker] += 1
    return {'sampled_section_starts': sum(counts.values()),
            'resource_header_categories': dict(sorted(counts.items()))}


def read_bun_and_prefix(source, stem, sector, prefix_bytes):
    small = f'TRACKS/{stem}{sector}.BUN'
    stream = f'TRACKS/STREAM{stem}{sector}.BUN'
    if isinstance(source, SplitZip):
        raw = source.read(small, limit=MAX_BUNDLE)
        stream_size = source.entries[stream][4]
        prefix = source.read(stream, limit=min(prefix_bytes, stream_size), prefix=True)
    else:
        with zipfile.ZipFile(source) as z:
            if z.getinfo(small).file_size > MAX_BUNDLE:
                raise ValueError('Small bundle exceeds safety limit')
            raw = z.read(small)
            stream_size = z.getinfo(stream).file_size
            with z.open(stream) as handle:
                prefix = handle.read(min(prefix_bytes, stream_size))
    return raw, prefix, stream_size


def analyze(pc_volumes, carbon_ps2_zip, carbon_wii_volumes,
            undercover_ps2_zip, undercover_wii_zip, prefix_mib=32):
    if type(prefix_mib) is not int or not 1 <= prefix_mib <= MAX_PREFIX_MIB:
        raise ValueError('Invalid prefix sampling bound')
    sources = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2_zip), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(undercover_ps2_zip), 'L2'),
        'undercover_wii': (Path(undercover_wii_zip), 'L2'),
    }
    rows, summaries = {}, {}
    for label, (archive, stem) in sources.items():
        for sector in ('RA', 'RB'):
            resource = label + '_' + sector
            bundle, prefix, stream_size = read_bun_and_prefix(archive, stem, sector, prefix_mib * MIB)
            rows[resource] = parse_rows(find_chunk(bundle), stream_size)
            summaries[resource] = {**summarize(rows[resource]),
                                   **sample_markers(rows[resource], prefix),
                                   'stream_size_bytes': stream_size}
    pairs = (
        ('carbon_pc', 'carbon_ps2'),
        ('carbon_pc', 'carbon_wii'),
        ('carbon_wii', 'carbon_ps2'),
        ('undercover_wii', 'undercover_ps2'),
        ('undercover_ps2', 'carbon_ps2'),
    )
    comparisons = {}
    for a, b in pairs:
        for sector in ('RA', 'RB'):
            comparisons[f'{a}_vs_{b}_{sector}'] = compare_rows(rows[a + '_' + sector], rows[b + '_' + sector])
    return {
        'sample_prefix_mib_per_stream': prefix_mib,
        'sources': summaries,
        'comparisons': comparisons,
        'limits': ('Field names derive from reconstructed Most Wanted, NOT a Carbon loader ABI. '
                   'Classification samples only section offsets within the bounded stream prefix. '
                   'Spatial values are exact serialized bytes. Matching section IDs between '
                   'different games do not establish matching world locations.'),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', nargs='+', type=Path, required=True)
    p.add_argument('--carbon-ps2-zip', type=Path, required=True)
    p.add_argument('--carbon-wii-volumes', nargs='+', type=Path, required=True)
    p.add_argument('--undercover-ps2-zip', type=Path, required=True)
    p.add_argument('--undercover-wii-zip', type=Path, required=True)
    p.add_argument('--sample-prefix-mib', type=int, default=32)
    a = p.parse_args()
    print(json.dumps(analyze(a.pc_volumes, a.carbon_ps2_zip, a.carbon_wii_volumes,
                             a.undercover_ps2_zip, a.undercover_wii_zip,
                             a.sample_prefix_mib), indent=2))


if __name__ == '__main__':
    main()
