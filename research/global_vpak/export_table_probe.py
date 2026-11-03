#!/usr/bin/env python3
"""Read-only structural probe for 16-byte NpxE entries in GAMEPLAY VPAKs.

Four u32 fields are intentionally named word0, length_candidate, offset_candidate,
marker_candidate until independently verified against the game engine.
"""
import argparse
import json
import struct
from pathlib import Path

from audit import read_selected_members
from chunk_layout import parse_chunks


def align8(value):
    return (value + 7) & ~7


def inspect_export_entries(records):
    """Check the observed offset/length chain without decoding payload semantics."""
    summary = {
        "records": len(records),
        "entries": 0,
        "consecutive_offset_transitions": 0,
        "terminal_zero_markers": 0,
        "first_word_values": set(),
        "nonterminal_offset_outside_data": 0,
        "nonterminal_length_past_data": 0,
        "nonterminal_length_past_data_indices": [],
    }
    for i, record in enumerate(records):
        chunks = record["chunks"]
        export = chunks["NpxE"]
        data_length = len(chunks["NtaD"])
        count = struct.unpack_from("<I", export, 8)[0]
        if not count or len(export) != 16 + 16 * count:
            raise ValueError(f"Invalid NpxE entry count in record {i}")
        entries = list(struct.iter_unpack("<4I", export[16:]))
        if len(entries) != count:
            raise ValueError(f"Truncated NpxE entry array in record {i}")
        if entries[-1][3] != 0 or any(e[3] == 0 for e in entries[:-1]):
            raise ValueError(f"Missing or misplaced final zero marker in record {i}")
        summary["terminal_zero_markers"] += 1
        summary["entries"] += count
        for j, (word0, length, offset, marker) in enumerate(entries):
            summary["first_word_values"].add(word0)
            if length % 4 or offset % 8:
                raise ValueError(f"Unexpected entry alignment at record {i}, entry {j}")
            if j + 1 < count:
                if entries[j + 1][2] != align8(offset + length):
                    raise ValueError(f"Broken consecutive offset chain at record {i}, entry {j}")
                summary["consecutive_offset_transitions"] += 1
                if offset >= data_length:
                    summary["nonterminal_offset_outside_data"] += 1
                if offset + length > data_length:
                    summary["nonterminal_length_past_data"] += 1
                    summary["nonterminal_length_past_data_indices"].append(i)
    summary["distinct_first_word_values"] = len(summary.pop("first_word_values"))
    summary["nonterminal_length_past_data_indices"] = sorted(set(summary["nonterminal_length_past_data_indices"]))
    return summary


def analyze(pc_zip, carbon_ps2_zip, undercover_ps2_zip):
    pc, _ = read_selected_members(pc_zip)
    carbon, _ = read_selected_members(carbon_ps2_zip)
    uc, _ = read_selected_members(undercover_ps2_zip)
    inputs = (
        (pc, "GAMEPLAY.BIN", "carbon_pc_active"),
        (pc, "GAMEPLAY.BAK", "carbon_pc_backup"),
        (carbon, "GAMEPLAY.BIN", "carbon_ps2"),
        (uc, "GAMEPLAY.BIN", "undercover_ps2"),
    )
    result = {}
    for files, name, label in inputs:
        if name not in files:
            raise ValueError(f"Missing {label}/{name}")
        result[label] = inspect_export_entries(parse_chunks(files[name]))
    result["limitations"] = (
        "Observed length/offset chain only; no decoded object type, field meaning, "
        "or runtime compatibility claim. A final marker entry is not a data object."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carbon_pc_zip", type=Path)
    parser.add_argument("carbon_ps2_zip", type=Path)
    parser.add_argument("undercover_ps2_zip", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == "__main__":
    main()
