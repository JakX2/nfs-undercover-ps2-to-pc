#!/usr/bin/env python3
"""Read-only field correlation probe for Carbon PC 0x372xx post-scene frames.

Important: an exact 32-bit match is a *candidate correlation*, not proof of a
pointer, resource registration, relocation rule, or game-loader behavior.
Owner game bytes stay local; JSON contains counts and slot numbers, no raw
model IDs, texture IDs, stream offsets, coordinates, or game assets.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct

HEAD, PRE, DATA, END = 0x37220, 0x37260, 0x37250, 0x37270
MAX_TAIL = 4096
MAX_SECTION = 32 * 1024 * 1024
MAX_SMALL = 8 * 1024 * 1024
MAX_STREAM = 512 * 1024 * 1024


def _frame(raw, offset, tag, payload_bytes):
    if offset < 0 or offset + 8 > len(raw):
        raise ValueError('Truncated post-scene frame')
    actual_tag, n = struct.unpack_from('<II', raw, offset)
    if actual_tag != tag or n != payload_bytes:
        raise ValueError('Unexpected post-scene record tag or length')
    end = offset + 8 + n
    if end > len(raw):
        raise ValueError('Truncated post-scene payload')
    return raw[offset + 8:end], end


def parse_pc_postscene(raw):
    """Independently check exact observed frames, retain opaque payloads in RAM."""
    if not isinstance(raw, bytes) or not 68 <= len(raw) <= MAX_TAIL or raw[:8] != bytes(8):
        raise ValueError('Invalid native post-scene prefix or size')
    head, pos = _frame(raw, 8, HEAD, 24)
    words = struct.unpack('<6I', head)
    count = words[2]
    if (words[:2] != (0x11111111, 0x11111111) or
            not 1 <= count <= 64 or words[3] != count or words[5] != count):
        raise ValueError('Inconsistent native control group count')
    groups = []
    for i in range(count):
        pre, pos = _frame(raw, pos, PRE, 12 if i == 0 else 8)
        data, pos = _frame(raw, pos, DATA, 120)
        end, pos = _frame(raw, pos, END, 8)
        groups.append({'pre': pre, 'data': data, 'end': end})
    if pos != len(raw):
        raise ValueError('Native control has unparsed trailing bytes')
    return {'header': words, 'groups': tuple(groups)}


def _word_samples(parsed, scene_hashes, geometry_hashes, anchor_offsets,
                  disk_offset, section_length):
    """Generate private (slot, value, heuristic flags) tuples without reporting IDs."""
    if not 0 < section_length <= MAX_SECTION or disk_offset < 0:
        raise ValueError('Invalid source section range')
    for group in parsed['groups']:
        for kind in ('pre', 'data', 'end'):
            payload = group[kind]
            for slot, (value,) in enumerate(struct.iter_unpack('<I', payload)):
                # Never turn zero or magic sentinels into misleading pointers.
                sentinel = value in (0, 0x11111111, 0xFFFFFFFF)
                flags = {
                    'zero': value == 0,
                    'scene_hash': not sentinel and value in scene_hashes,
                    'indexed_solid_hash': not sentinel and value in geometry_hashes,
                    'exact_relative_anchor': not sentinel and value in anchor_offsets,
                    'exact_absolute_anchor': not sentinel and value in
                        (disk_offset + anchor for anchor in anchor_offsets),
                    'aligned_in_section_range': not sentinel and
                        0 < value < section_length and value % 4 == 0,
                    'aligned_in_stream_range': not sentinel and
                        disk_offset <= value < disk_offset + section_length and value % 4 == 0,
                }
                yield (kind, slot), value, flags


def analyze_sections(records):
    """Summarize sections without exposing original values or section offsets.

    records: iterable of (parsed, scene_hashes, geometry_hashes,
                          local_anchor_offsets, disk_offset, section_length).
    """
    entries = list(records)
    if not entries or len(entries) > 100:
        raise ValueError('Need between 1 and 100 bounded native sections')
    pooled = defaultdict(list)
    per_section = []
    header_unknown = []
    raw_data_seen = set()
    repeats = 0
    for parsed, scene_ids, solid_ids, anchors, stream_off, length in entries:
        if not parsed['groups'] or len(parsed['groups']) > 64:
            raise ValueError('Empty or oversized native group sequence')
        header_unknown.append(parsed['header'][4])
        per_section.append({'native_control_groups': len(parsed['groups']),
                            'scenery_model_hash_count': len(scene_ids),
                            'indexed_solid_hash_count': len(solid_ids)})
        for group in parsed['groups']:
            if group['data'] in raw_data_seen:
                repeats += 1
            raw_data_seen.add(group['data'])
        for key, value, flags in _word_samples(parsed, scene_ids, solid_ids,
                                                anchors, stream_off, length):
            pooled[key].append((value, flags))
    output = []
    for (kind, slot), sample in sorted(pooled.items()):
        flags = Counter(k for _, ff in sample for k, truth in ff.items() if truth)
        # Nonzero counts avoid accidentally treating all-zero slots as stable IDs.
        nonzero = [v for v,_ in sample if v != 0]
        output.append({'record': kind, 'word_index': slot,
                       'sample_count': len(sample),
                       'zero_count': flags['zero'],
                       'distinct_nonzero_values': len(set(nonzero)),
                       'matching_scene_model_hashes': flags['scene_hash'],
                       'matching_geometry_index_hashes': flags['indexed_solid_hash'],
                       'matching_exact_relative_root_offsets': flags['exact_relative_anchor'],
                       'matching_exact_absolute_root_offsets': flags['exact_absolute_anchor'],
                       'aligned_in_section_range_candidates': flags['aligned_in_section_range'],
                       'aligned_in_stream_range_candidates': flags['aligned_in_stream_range']})
    return {'scope': 'READ_ONLY_CANDIDATE_CORRELATIONS_NOT_PROVEN_REFERENCES',
            'inspected_native_sections': len(entries),
            'inspected_native_groups': sum(x['native_control_groups'] for x in per_section),
            'native_group_count_histogram': dict(sorted(Counter(
                x['native_control_groups'] for x in per_section).items())),
            'duplicate_120_byte_payload_occurrences': repeats,
            'distinct_unknown_header_word4_values': len(set(header_unknown)),
            'per_section_counts': per_section,
            'field_slot_statistics': output,
            'field_semantics': 'UNVERIFIED',
            'pointers_and_relocation': 'UNVERIFIED',
            'runtime_registration': 'UNVERIFIED',
            'no_game_file_writes': True}


def _private_section_record(section, stream_offset):
    """Use the existing strict world-bridge parsers to authenticate source IDs."""
    from carbon_pc_native_postscene_layout_gate import (
        _scan_roots, _children, profile_carbon_section)
    from geometry_hash_control import parse_geometry_root
    if not isinstance(section, bytes) or not 0 < len(section) <= MAX_SECTION:
        raise ValueError('Invalid Carbon PC section')
    profile_carbon_section(section)
    layout = _scan_roots(section, 1)
    parsed = parse_pc_postscene(layout['postscene'])
    geom_start = layout['texture_root_bytes']
    geom_end = geom_start + sum(layout['geometry_root_bytes'])
    index = parse_geometry_root(section[geom_start:geom_end])
    if index['platform'] != 0x00134900:
        raise ValueError('The geometry index is not Carbon PC native')
    scene_at = geom_end + layout['interroot_zero_chunk_bytes']
    scene = layout['scene']
    child = {tag:(a,b) for tag,a,b in _children(scene, 8, len(scene))}
    start, stop = child[0x34102]
    scene_hashes = {struct.unpack_from('<I', scene, pos + 0x18)[0]
                    for pos in range(start, stop, 72)}
    anchors = {geom_start, geom_end, scene_at, layout['scene_end']}
    # The scenery child headers are verified by _children, so they are additional
    # possible exact relative boundaries. They are NOT presumed to be pointers.
    anchors.update(scene_at + a - 8 for _, a, _ in _children(scene, 8, len(scene)))
    return (parsed, scene_hashes, index['hashes'], anchors,
            stream_offset, len(section))


def inspect_original(carbon_bun, carbon_stream, section_ids=(141, 142)):
    """Read private originals directly, emit aggregate data only, never write."""
    paths = (Path(carbon_bun), Path(carbon_stream))
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise ValueError('Only regular original source files are allowed')
    if paths[0].resolve() == paths[1].resolve():
        raise ValueError('Source paths alias')
    if not (0 < paths[0].stat().st_size <= MAX_SMALL and
            0 < paths[1].stat().st_size <= MAX_STREAM):
        raise ValueError('Invalid original source file sizes')
    if not isinstance(section_ids, (list, tuple)) or not 1 <= len(section_ids) <= 100 or \
       any(type(s) is not int for s in section_ids) or len(set(section_ids)) != len(section_ids):
        raise ValueError('Invalid or duplicate requested section IDs')
    from carbon_pc_native_postscene_layout_gate import stream_rows
    rows = stream_rows(paths[0].read_bytes(), paths[1].stat().st_size)
    records = []
    with paths[1].open('rb') as f:
        for sec in section_ids:
            if sec not in rows:
                raise ValueError('Requested section missing from Carbon stream index')
            offset, size = rows[sec]
            if not 0 < size <= MAX_SECTION:
                raise ValueError('Source section exceeds inspection bound')
            f.seek(offset)
            section = f.read(size)
            if len(section) != size:
                raise ValueError('Original stream contains a truncated section')
            records.append(_private_section_record(section, offset))
    return analyze_sections(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-bun', type=Path, required=True)
    parser.add_argument('--carbon-stream', type=Path, required=True)
    parser.add_argument('--sections', nargs='+', type=int, default=(141,142))
    args = parser.parse_args()
    print(json.dumps(inspect_original(args.carbon_bun, args.carbon_stream,
                                      args.sections), indent=2))


if __name__ == '__main__':
    main()
