#!/usr/bin/env python3
"""Source-only V3 byte-lane controls for Carbon PC native 0x372xx post-scene data.

Never rewrites a game file; analyses are aggregate-only. A match to a known
solid/scenery model hash does not establish the function of this chunk, a
serialized pointer, or any relocation rule. Run beside the existing PR #33
world_bridge modules to inspect privately owned original sources.
"""
import argparse
from collections import Counter, defaultdict
import json
import struct

from carbon_pc_postscene_cross_section_gate import (
    SENTINELS, _validate_record, independent_section_specificity,
)

# Deliberately fixed; avoid searching arbitrary bit offsets after seeing results.
LANES = (('little', 0), ('little', 1), ('little', 2),
         ('little', 3), ('big', 0))
KINDS = ('pre', 'data', 'end')


def _classify(value, local, foreign):
    if value == 0:
        return 'zero'
    if value in SENTINELS:
        return 'sentinel'
    if value in local and value in foreign:
        return 'shared'
    if value in local:
        return 'local_only'
    if value in foreign:
        return 'foreign_only'
    return 'unmatched'


def _check_independence(records):
    """Distinct and non-overlapping stream ranges are required for V3 votes."""
    ranges = []
    for record in records:
        _validate_record(record)
        offset, length = record[4], record[5]
        if offset % 2048:
            raise ValueError('Independent section start is not stream-aligned')
        if offset + length > 0xFFFFFFFF:
            raise ValueError('Section stream bound exceeds 32-bit address range')
        ranges.append((offset, offset + length))
    ranges.sort()
    if any(prev_end > cur_start for (_, prev_end), (cur_start, _) in
           zip(ranges, ranges[1:])):
        raise ValueError('Selected section byte ranges overlap or duplicate')


def _lane_words(blob, endian, byte_lane):
    """Candidate 32-bit words at predeclared offsets only."""
    fmt = '<I' if endian == 'little' else '>I'
    for at in range(byte_lane, len(blob) - 3, 4):
        yield struct.unpack_from(fmt, blob, at)[0]


def audit_byte_lanes(records):
    """Compare aligned little-endian ID matches to deliberate negative controls.

    All five tested lanes use exactly the same section-local/foreign model-hash
    inventory. Offset +1/+2/+3 lanes and aligned big-endian are negative
    controls, not alternative ways to interpret chunk contents. Return counts,
    not source values, bytes, hashes, addresses or object names.
    """
    records = list(records)
    if not 1 <= len(records) <= 100:
        raise ValueError('Need 1..100 independent source records')
    _check_independence(records)
    all_hashes = [set(s) | set(g) for _, s, g, _, _, _ in records]
    foreign_sets = [set().union(*(all_hashes[j] for j in range(len(records))
                                   if j != i)) for i in range(len(records))]
    pooled = defaultdict(Counter)
    support = defaultdict(set)
    for i, (parsed, _, _, _, _, _) in enumerate(records):
        for group in parsed['groups']:
            for kind in KINDS:
                for endian, lane in LANES:
                    key = (kind, endian, lane)
                    for value in _lane_words(group[kind], endian, lane):
                        label = _classify(value, all_hashes[i], foreign_sets[i])
                        pooled[key][label] += 1
                        if label == 'local_only':
                            support[key].add(i)
    stats = []
    for kind in KINDS:
        for endian, lane in LANES:
            key = (kind, endian, lane)
            counts = pooled[key]
            stats.append({
                'record': kind, 'byte_order': endian, 'byte_lane': lane,
                'tested_words': sum(counts.values()),
                'zero_words': counts['zero'],
                'sentinel_words': counts['sentinel'],
                'local_only_hash_matches': counts['local_only'],
                'sections_with_local_only_hash_match': len(support[key]),
                'shared_hash_matches': counts['shared'],
                'foreign_only_hash_matches': counts['foreign_only'],
                'unmatched_words': counts['unmatched'],
                'is_predeclared_negative_control': endian != 'little' or lane != 0,
            })
    return {
        'scope': 'READ_ONLY_BYTE_LANE_AND_ENDIAN_NEGATIVE_CONTROLS',
        'independent_nonoverlapping_sections': len(records),
        'predeclared_controls': ['unaligned_little_endian_1_2_3',
                                 'aligned_big_endian'],
        'field_byte_lane_statistics': stats,
        'unverified_register_or_pointer_meaning': True,
        'game_runtime_tested': False,
        'no_game_file_writes': True,
    }


def strict_slot_screen(records):
    """Require ≥3 distinct source sections and EVERY observed informative word.

    This is intentionally stricter than V2's exploratory two-section filter;
    zero/sentinels are excluded from the informative denominator. A slot is
    not endorsed if just two values match and dozens don't.
    """
    records = list(records)
    if not 1 <= len(records) <= 100:
        raise ValueError('Need 1..100 independent source records')
    _check_independence(records)
    v2 = independent_section_specificity(records)
    candidates = []
    per_slot = []
    for item in v2['field_slot_statistics']:
        hits = item['local_only_occurrences']
        informative = item['nonzero_non_sentinel_occurrences']
        local_support = item['independent_source_sections_with_local_only_match']
        qualifies = bool(len(records) >= 3 and local_support >= 3 and
                         informative >= 3 and hits == informative and
                         item['foreign_only_occurrences'] == 0 and
                         item['ambiguous_shared_control_occurrences'] == 0 and
                         item['unmatched_occurrences'] == 0)
        row = {'record': item['record'], 'word_index': item['word_index'],
               'local_only_hits': hits, 'informative_words': informative,
               'independent_sections_with_local_only_match': local_support,
               'all_informative_words_local_only': bool(informative and hits == informative),
               'passes_strict_three_section_screen': qualifies}
        per_slot.append(row)
        if qualifies:
            candidates.append({'record': row['record'], 'word_index': row['word_index']})
    return {
        'scope': 'STRICT_HYPOTHESIS_TRIAGE_NOT_SEMANTIC_PROOF',
        'independent_sections': len(records),
        'minimum_independent_sections_for_pass': 3,
        'insufficient_independent_sections_for_pass': len(records) < 3,
        'field_slot_statistics': per_slot,
        'strict_screen_candidates': candidates,
        'unverified_register_or_pointer_meaning': True,
        'no_game_file_writes': True,
    }


def inspect_private_sources(carbon_bun, carbon_stream, section_ids=(141, 142)):
    """Reuse authenticated PC source reader, one pass, no write operations."""
    from pathlib import Path
    ids = tuple(section_ids)
    if not 1 <= len(ids) <= 100 or any(type(v) is not int for v in ids) or \
       len(set(ids)) != len(ids):
        raise ValueError('Invalid or duplicate independent section IDs')
    from carbon_pc_postscene_dependency_probe import MAX_SMALL, MAX_STREAM, MAX_SECTION
    bun, stream = Path(carbon_bun), Path(carbon_stream)
    if not bun.is_file() or not stream.is_file() or bun.is_symlink() or stream.is_symlink():
        raise ValueError('Source paths must be regular files')
    if bun.resolve() == stream.resolve():
        raise ValueError('Source paths alias')
    if not 0 < bun.stat().st_size <= MAX_SMALL or not 0 < stream.stat().st_size <= MAX_STREAM:
        raise ValueError('Source dimensions exceed private audit limits')
    from carbon_pc_native_postscene_layout_gate import stream_rows
    from carbon_pc_postscene_dependency_probe import _private_section_record
    index = stream_rows(bun.read_bytes(), stream.stat().st_size)
    records = []
    with stream.open('rb') as fp:
        for sec in ids:
            if sec not in index:
                raise ValueError('Requested Carbon section is absent')
            off, count = index[sec]
            if not 0 < count <= MAX_SECTION:
                raise ValueError('Selected section size exceeds audit limit')
            fp.seek(off)
            raw = fp.read(count)
            if len(raw) != count:
                raise ValueError('Truncated original Carbon streaming section')
            records.append(_private_section_record(raw, off))
    return {'v2_specificity': independent_section_specificity(records),
            'v3_lane_controls': audit_byte_lanes(records),
            'v3_strict_screen': strict_slot_screen(records),
            'original_files_written': False,
            'runtime_claim': 'NONE'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--carbon-bun', required=True)
    p.add_argument('--carbon-stream', required=True)
    p.add_argument('--sections', nargs='+', type=int, default=[141, 142])
    a = p.parse_args()
    print(json.dumps(inspect_private_sources(a.carbon_bun, a.carbon_stream,
                                             a.sections), indent=2))


if __name__ == '__main__':
    main()
