#!/usr/bin/env python3
"""V4: blind, read-only Carbon PC RB candidate census for post-scene controls.

The source owner keeps all original game bytes private. A candidate is counted
only after the known native PC scene/geometry/post-scene profile validates;
rejection means 'outside the CURRENT parser profile', not 'no control records'.
No stream or game file is ever written. Neither matching bytes nor a strict
screen establishes pointer, registration or relocation semantics.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from carbon_pc_postscene_dependency_probe import (
    MAX_SMALL, MAX_STREAM, MAX_SECTION, _private_section_record,
)
from carbon_pc_postscene_cross_section_gate import independent_section_specificity
from carbon_pc_postscene_lane_controls import (
    _check_independence, audit_byte_lanes, strict_slot_screen,
)

PC_TEXTURE_TAG = 0xB3300000
MAX_AUTHENTICATED_SECTIONS = 100
MAX_INDEX_ROWS = 16384


def _check_inputs(bun, stream, baseline_ids):
    """Check untrusted file paths, sizes and baseline section selections."""
    paths = (Path(bun), Path(stream))
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise ValueError('Original inputs must be regular files, not symlinks')
    if paths[0].resolve() == paths[1].resolve():
        raise ValueError('Original files alias')
    if not (0 < paths[0].stat().st_size <= MAX_SMALL and
            0 < paths[1].stat().st_size <= MAX_STREAM):
        raise ValueError('Original source dimensions exceed inspection bounds')
    if (not isinstance(baseline_ids, (tuple, list)) or not baseline_ids or
            len(baseline_ids) > MAX_AUTHENTICATED_SECTIONS or
            any(type(k) is not int or not -32768 <= k <= 32767 for k in baseline_ids) or
            len(set(baseline_ids)) != len(baseline_ids)):
        raise ValueError('Invalid baseline section identifiers')
    return paths


def _suffix_fingerprint(parsed):
    """RAM-only fingerprint for suppressing byte-identical candidate suffixes."""
    digest = hashlib.sha256()
    digest.update(struct.pack('<6I', *parsed['header']))
    for g in parsed['groups']:
        for part in ('pre', 'data', 'end'):
            digest.update(g[part])
    return digest.digest()


def inspect_originals(carbon_bun, carbon_stream, baseline_ids=(141, 142)):
    """Census EVERY indexed section; never pick a third ID by looking at matches.

    Only exact controls fitting the strict 141/142 framing enter the analysis.
    Equivalent opaque native suffixes count once, even at disjoint offsets.
    All rejection categories are coarse aggregate counts, never raw bytes.
    """
    bun, stream = _check_inputs(carbon_bun, carbon_stream, baseline_ids)
    from carbon_pc_native_postscene_layout_gate import stream_rows
    index = stream_rows(bun.read_bytes(), stream.stat().st_size)
    if len(index) > MAX_INDEX_ROWS:
        raise ValueError('Original source index has too many candidate rows')
    if any(k not in index for k in baseline_ids):
        raise ValueError('Known Carbon baseline is missing from source index')

    stats = Counter()
    accepted = {}
    fingerprints = {}
    with stream.open('rb') as handle:
        for section_id in sorted(index):
            stats['indexed_rows'] += 1
            offset, size = index[section_id]
            if not size:
                stats['empty_rows'] += 1
                continue
            if size > MAX_SECTION:
                stats['oversize_rows'] += 1
                continue
            stats['bounded_nonempty_rows'] += 1
            handle.seek(offset)
            section = handle.read(size)
            if len(section) != size:
                raise ValueError('Original indexed stream section was truncated')
            if len(section) < 8 or struct.unpack_from('<I', section)[0] != PC_TEXTURE_TAG:
                stats['outside_texture_root_prefix'] += 1
                continue
            stats['texture_prefixed_rows'] += 1
            try:
                record = _private_section_record(section, offset)
            except ValueError:
                stats['unsupported_by_current_strict_profile'] += 1
                continue
            # Successful verification includes genuine scene-index, embedded-solid
            # index and the exact native PC 0x372xx post-scene envelope.
            accepted[section_id] = record
            stats['strictly_authenticated_rows'] += 1
            fp = _suffix_fingerprint(record[0])
            fingerprints.setdefault(fp, []).append(section_id)

    for section_id in baseline_ids:
        if section_id not in accepted:
            raise ValueError('Known Carbon baseline failed strict authentication')
    if len(accepted) > MAX_AUTHENTICATED_SECTIONS:
        raise ValueError('More authenticated sections than bounded analysis limit')
    all_records = [accepted[k] for k in sorted(accepted)]
    _check_independence(all_records)

    # The first section in each identical-suffix equivalence class wins, with
    # a baseline preferred if present. This is deterministic and predeclared.
    candidates = []
    duplicate_count = 0
    for same_suffix_ids in fingerprints.values():
        if len(same_suffix_ids) > 1:
            duplicate_count += len(same_suffix_ids) - 1
        preferred = sorted(same_suffix_ids, key=lambda s: (s not in baseline_ids, s))[0]
        candidates.append(preferred)
    chosen_ids = sorted(candidates)
    records = [accepted[k] for k in chosen_ids]
    _check_independence(records)
    sufficient = len(records) >= 3
    v2 = independent_section_specificity(records)
    lanes = audit_byte_lanes(records)
    strict = strict_slot_screen(records)

    return {
        'scope': 'READ_ONLY_BLIND_STRICT_PROFILE_CENSUS_NOT_RUNTIME_PROOF',
        'indexed_row_census': dict(sorted(stats.items())),
        'strictly_authenticated_section_ids': sorted(accepted),
        'independent_distinct_suffix_section_ids': chosen_ids,
        'byte_identical_postscene_suffix_extra_occurrences': duplicate_count,
        'known_baselines_authenticated': all(k in accepted for k in baseline_ids),
        'independent_three_section_gate': 'EVALUABLE' if sufficient else 'INSUFFICIENT_CONTROLS',
        'first_additional_control_beyond_baselines': next((k for k in chosen_ids if k not in baseline_ids), None),
        'v2_specificity': v2,
        'v3_byte_lane_negatives': lanes,
        'v3_strict_screen': strict,
        'interpretation': ('All accepted IDs satisfy the current 141/142 structural profile. '
                           'A rejected section may be valid under a different native layout. '
                           'No resource-control field, address or relocation semantics proven.'),
        'retail_game_execution_tested': False,
        'game_file_write_performed': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-bun', type=Path, required=True)
    parser.add_argument('--carbon-stream', type=Path, required=True)
    parser.add_argument('--baseline-ids', type=int, nargs='+', default=[141, 142])
    args = parser.parse_args()
    print(json.dumps(inspect_originals(args.carbon_bun, args.carbon_stream,
                                       tuple(args.baseline_ids)), indent=2))


if __name__ == '__main__':
    main()
