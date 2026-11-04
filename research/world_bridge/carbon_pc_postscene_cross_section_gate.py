#!/usr/bin/env python3
"""Read-only, independent-section specificity controls for Carbon PC 0x372xx.

This is a follow-up to carbon_pc_postscene_dependency_probe.py. No source
asset bytes, model hashes, file offsets, identities or raw field values are
emitted. Correlations are NOT proof of any pointer/registration semantics.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct

from carbon_pc_postscene_dependency_probe import (
    MAX_SECTION, MAX_SMALL, MAX_STREAM, analyze_sections as analyze_v1,
    _private_section_record,
)

SENTINELS = frozenset((0, 0x11111111, 0xFFFFFFFF))
ROLES = ('scene_only', 'solid_only', 'scene_and_solid', 'either')


def _validate_record(record):
    """Validate enough of the supplied in-memory synthetic/source record to fail closed."""
    if not isinstance(record, tuple) or len(record) != 6:
        raise ValueError('Invalid source record tuple')
    parsed, scene, solid, anchors, offset, length = record
    if (not isinstance(parsed, dict) or not isinstance(parsed.get('groups'), tuple)
            or not 1 <= len(parsed['groups']) <= 64
            or not isinstance(scene, (set, frozenset))
            or not isinstance(solid, (set, frozenset))
            or not isinstance(anchors, (set, frozenset))
            or not all(type(v) is int and 0 <= v <= 0xFFFFFFFF for v in scene | solid)
            or not all(type(v) is int and 0 <= v <= MAX_SECTION for v in anchors)
            or type(offset) is not int or offset < 0
            or type(length) is not int or not 0 < length <= MAX_SECTION):
        raise ValueError('Invalid Carbon PC source record dimensions')
    for i, group in enumerate(parsed['groups']):
        if not isinstance(group, dict) or any(not isinstance(group.get(k), bytes)
                                              or len(group[k]) != n for k, n in
                                              (('pre', 12 if i == 0 else 8),
                                               ('data', 120), ('end', 8))):
            raise ValueError('Invalid 0x372xx opaque control payloads')
    header = parsed.get('header')
    n = len(parsed['groups'])
    if (not isinstance(header, tuple) or len(header) != 6
            or header[:2] != (0x11111111, 0x11111111)
            or not (header[2] == header[3] == header[5] == n)):
        raise ValueError('Inconsistent native post-scene header')


def _iter_words(parsed):
    for group in parsed['groups']:
        for kind in ('pre', 'data', 'end'):
            for slot, (value,) in enumerate(struct.iter_unpack('<I', group[kind])):
                yield (kind, slot), value


def _role(value, scene_hashes, solid_hashes):
    in_scene, in_solid = value in scene_hashes, value in solid_hashes
    if in_scene and in_solid:
        return 'scene_and_solid'
    if in_scene:
        return 'scene_only'
    if in_solid:
        return 'solid_only'
    return None


def independent_section_specificity(records):
    """Compare each opaque word with OWN verified IDs vs OTHER section IDs.

    Leave-one-section-out negatives are only informative when source sets vary;
    overlap is explicitly classified as ambiguous. Multiple groups in one
    section never count as multiple independent sections. All values remain RAM.
    """
    entries = list(records)
    if not 1 <= len(entries) <= 100:
        raise ValueError('Need 1..100 independent source sections')
    for entry in entries:
        _validate_record(entry)
    hashes = [set(a) | set(b) for _, a, b, _, _, _ in entries]
    local_scene_solid_overlap = [len(set(s) & set(g))
                                 for _, s, g, _, _, _ in entries]
    foreign = [set().union(*(h for j, h in enumerate(hashes) if j != i))
               for i in range(len(entries))]
    rows = defaultdict(lambda: {
        'nonzero_non_sentinel_occurrences': 0,
        'local_only_occurrences': 0,
        'foreign_only_occurrences': 0,
        'ambiguous_shared_control_occurrences': 0,
        'unmatched_occurrences': 0,
        'zero_occurrences': 0,
        'sentinel_occurrences': 0,
        'local_section_support': set(),
        'foreign_section_support': set(),
        'local_scene_only_occurrences': 0,
        'local_solid_only_occurrences': 0,
        'local_scene_and_solid_occurrences': 0,
    })
    for i, (parsed, scene, solid, _, _, _) in enumerate(entries):
        own = hashes[i]
        other = foreign[i]
        for key, value in _iter_words(parsed):
            row = rows[key]
            if value == 0:
                row['zero_occurrences'] += 1
                continue
            if value in SENTINELS:
                row['sentinel_occurrences'] += 1
                continue
            row['nonzero_non_sentinel_occurrences'] += 1
            is_local, is_foreign = value in own, value in other
            if is_local and is_foreign:
                row['ambiguous_shared_control_occurrences'] += 1
            elif is_local:
                row['local_only_occurrences'] += 1
                row['local_section_support'].add(i)
                role = _role(value, scene, solid)
                row['local_' + role + '_occurrences'] += 1
            elif is_foreign:
                row['foreign_only_occurrences'] += 1
                row['foreign_section_support'].add(i)
            else:
                row['unmatched_occurrences'] += 1
    slots = []
    followups = []
    for (kind, slot), row in sorted(rows.items()):
        support = len(row['local_section_support'])
        foreign_support = len(row['foreign_section_support'])
        flagged = (support >= 2 and row['foreign_only_occurrences'] == 0 and
                   row['ambiguous_shared_control_occurrences'] == 0)
        item = {
            'record': kind,
            'word_index': slot,
            'independent_source_sections_with_local_only_match': support,
            'independent_source_sections_with_foreign_only_match': foreign_support,
            'local_only_occurrences': row['local_only_occurrences'],
            'foreign_only_occurrences': row['foreign_only_occurrences'],
            'ambiguous_shared_control_occurrences': row['ambiguous_shared_control_occurrences'],
            'unmatched_occurrences': row['unmatched_occurrences'],
            'zero_occurrences': row['zero_occurrences'],
            'sentinel_occurrences': row['sentinel_occurrences'],
            'nonzero_non_sentinel_occurrences': row['nonzero_non_sentinel_occurrences'],
            'local_scene_only_occurrences': row['local_scene_only_occurrences'],
            'local_solid_only_occurrences': row['local_solid_only_occurrences'],
            'local_scene_and_solid_occurrences': row['local_scene_and_solid_occurrences'],
            'passes_cross_section_followup_filter': flagged,
        }
        slots.append(item)
        if flagged:
            followups.append({'record': kind, 'word_index': slot})
    return {
        'scope': 'READ_ONLY_LEAVE_ONE_SECTION_OUT_NEGATIVE_CONTROL',
        'inspected_independent_sections': len(entries),
        'native_group_counts': dict(sorted(Counter(
            len(rec[0]['groups']) for rec in entries).items())),
        'own_scene_and_solid_hash_set_overlap_counts': local_scene_solid_overlap,
        'sections_with_any_shared_model_hash_in_other_section': sum(
            bool(hashes[i] & foreign[i]) for i in range(len(entries))),
        'field_slot_statistics': slots,
        'slots_passing_followup_filter': followups,
        'candidate_reference_semantics': 'UNVERIFIED',
        'cross_section_followup_filter_is_not_loader_proof': True,
        'no_game_file_writes': True,
    }


def inspect_private_sources(carbon_bun, carbon_stream, section_ids=(141,142)):
    """One private read pass, two independent analyses; never write the originals."""
    p_bun, p_stream = Path(carbon_bun), Path(carbon_stream)
    if any(not p.is_file() or p.is_symlink() for p in (p_bun, p_stream)):
        raise ValueError('Source inputs must be regular files, not symlinks')
    if p_bun.resolve() == p_stream.resolve():
        raise ValueError('Original inputs alias')
    if not (0 < p_bun.stat().st_size <= MAX_SMALL and
            0 < p_stream.stat().st_size <= MAX_STREAM):
        raise ValueError('Invalid private source file sizes')
    if (not isinstance(section_ids, (tuple, list)) or
            not 1 <= len(section_ids) <= 100 or
            any(type(k) is not int for k in section_ids) or
            len(set(section_ids)) != len(section_ids)):
        raise ValueError('Invalid or duplicate requested section IDs')
    from carbon_pc_native_postscene_layout_gate import stream_rows
    rows = stream_rows(p_bun.read_bytes(), p_stream.stat().st_size)
    records = []
    with p_stream.open('rb') as fp:
        for number in section_ids:
            if number not in rows:
                raise ValueError('Section missing from the native Carbon index')
            offset, length = rows[number]
            if not 0 < length <= MAX_SECTION:
                raise ValueError('Original section exceeds read-only inspection bound')
            fp.seek(offset)
            section = fp.read(length)
            if len(section) != length:
                raise ValueError('Short original Carbon section')
            records.append(_private_section_record(section, offset))
    return {'v1_field_correlations': analyze_v1(records),
            'v2_section_specificity': independent_section_specificity(records),
            'original_retained_in_place': True,
            'runtime_tested': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--carbon-bun', type=Path, required=True)
    p.add_argument('--carbon-stream', type=Path, required=True)
    p.add_argument('--sections', nargs='+', type=int, default=[141,142])
    args = p.parse_args()
    print(json.dumps(inspect_private_sources(args.carbon_bun, args.carbon_stream,
                                             args.sections), indent=2))


if __name__ == '__main__':
    main()
