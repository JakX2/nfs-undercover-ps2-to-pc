#!/usr/bin/env python3
"""Read-only alignment of the *name pools* of indexed GAMEPLAY VPAK records.

Usage: python research/global_vpak/record_alignment.py PC_GLOBAL.zip CARBON_PS2_GLOBAL.zip UNDERCOVER_PS2_GLOBAL.zip
No proprietary strings or binary payloads are printed or written. These are
name-list relationships, not proof that event or attribute payloads are ABI-compatible.
"""

import argparse
import json
import struct
from pathlib import Path

from audit import EDITOR_MARKER, read_selected_members, string_region


def record_names(data):
    """Return entry-local, marker-free ordered string tuples from a gameplay VPAK."""
    if len(data) < 16 or data[:4] != b"VPAK":
        raise ValueError("Missing or truncated gameplay VPAK header")
    count, table_end, _unknown = struct.unpack_from("<III", data, 4)
    if not (0 < count <= 20000 and 16 + count * 20 <= table_end <= len(data)):
        raise ValueError("Invalid gameplay index bounds")
    records = []
    previous_aux = table_end
    for i in range(count):
        _cumulative, first_size, _aux_size, text_offset, aux_offset = struct.unpack_from(
            "<IIIII", data, 16 + 20 * i
        )
        if not (previous_aux <= text_offset <= aux_offset <= len(data)):
            raise ValueError(f"Invalid index offsets at entry {i}")
        if first_size > aux_offset - text_offset:
            raise ValueError(f"Oversized name region at entry {i}")
        block_size, names = string_region(data, text_offset)
        if block_size > first_size:
            raise ValueError(f"Out-of-bounds ErtS at entry {i}")
        records.append(tuple(name for name in names if name != EDITOR_MARKER))
        previous_aux = aux_offset
    return records


def compare_aligned(left, right):
    """Report same-index name-list agreement; no record payload equivalence assumed."""
    common = min(len(left), len(right))
    same_order = 0
    same_set = 0
    changed = []
    for i in range(common):
        a, b = left[i], right[i]
        same_order += a == b
        same_set += set(a) == set(b)
        if set(a) != set(b):
            changed.append(i)
    return {
        "left_entries": len(left),
        "right_entries": len(right),
        "same_index_pairs_checked": common,
        "same_index_identical_ordered_name_lists": same_order,
        "same_index_identical_name_sets": same_set,
        "name_set_difference_count": len(changed),
        "name_set_difference_indices_first_20": changed[:20],
    }


def best_cross_index_match(left, right):
    """Best Jaccard overlap across index pairs, reported only as aggregates.

    A large shared generic-name pool can dominate these scores; the result is
    NOT an event mapping or indication of payload interchangeability.
    """
    if not left or not right:
        raise ValueError("Both source record lists must be nonempty")
    right_sets = [set(names) for names in right]
    best_score = -1.0
    best_intersection = 0
    best_pair = (0, 0)
    runner_up = -1.0
    for i, names in enumerate(left):
        a = set(names)
        for j, b in enumerate(right_sets):
            overlap = len(a & b)
            union = len(a | b)
            score = overlap / union if union else 0.0
            if score > best_score:
                runner_up = best_score
                best_score = score
                best_intersection = overlap
                best_pair = (i, j)
            elif score > runner_up:
                runner_up = score
    return {
        "index_pair_examined": len(left) * len(right),
        "highest_jaccard": round(best_score, 6),
        "highest_overlap_shared_distinct_names": best_intersection,
        "highest_overlap_left_index": best_pair[0],
        "highest_overlap_right_index": best_pair[1],
        "second_highest_jaccard": round(runner_up, 6),
    }


def analyze(pc, carbon_ps2, undercover_ps2):
    pc_files, _ = read_selected_members(pc)
    carbon_files, _ = read_selected_members(carbon_ps2)
    uc_files, _ = read_selected_members(undercover_ps2)
    sources = (
        (pc_files, "GAMEPLAY.BIN", "Carbon PC active"),
        (pc_files, "GAMEPLAY.BAK", "Carbon PC backup"),
        (carbon_files, "GAMEPLAY.BIN", "Carbon PS2"),
        (uc_files, "GAMEPLAY.BIN", "Undercover PS2"),
    )
    records = {}
    for archive, name, label in sources:
        if name not in archive:
            raise ValueError(f"Required source missing: {label}/{name}")
        records[label] = record_names(archive[name])
    return {
        "pc_backup_vs_carbon_ps2": compare_aligned(records["Carbon PC backup"], records["Carbon PS2"]),
        "pc_active_vs_backup": compare_aligned(records["Carbon PC active"], records["Carbon PC backup"]),
        "undercover_vs_carbon_ps2_same_index": compare_aligned(records["Undercover PS2"], records["Carbon PS2"]),
        "undercover_vs_carbon_ps2_best_cross_index": best_cross_index_match(
            records["Undercover PS2"], records["Carbon PS2"]
        ),
        "limits": "Name-pool overlaps only; no payload, event, position, or runtime compatibility inferred.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carbon_pc_zip", type=Path)
    parser.add_argument("carbon_ps2_zip", type=Path)
    parser.add_argument("undercover_ps2_zip", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == "__main__":
    main()
