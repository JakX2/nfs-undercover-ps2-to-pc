#!/usr/bin/env python3
"""Read-only six-chunk GAMEPLAY VPAK structure audit (no asset export).

Usage: python research/global_vpak/chunk_layout.py PC_GLOBAL.zip CARBON_PS2_GLOBAL.zip UC_PS2_GLOBAL.zip

The byte comparisons are evidence of shared serialized data, not proof of
runtime loading, semantic compatibility, or a completed gameplay port.
"""
import argparse
import json
import struct
from pathlib import Path

from audit import read_selected_members, string_region

CHUNK_ORDER = (b"sreV", b"NpeD", b"NrtS", b"NtaD", b"NpxE", b"NrtP")


def parse_chunks(data):
    """Validate index, ErtS, six chunk headers and exact per-record chunk coverage.

    Returns record-local source bytes solely for in-memory equality comparisons.
    It never interprets or rewrites unknown gameplay fields.
    """
    if len(data) < 16 or data[:4] != b"VPAK":
        raise ValueError("Missing or truncated VPAK header")
    count, index_end, _unknown = struct.unpack_from("<III", data, 4)
    if not (0 < count <= 20000 and 16 + count * 20 <= index_end <= len(data)):
        raise ValueError("Invalid gameplay index bounds")

    entries = [struct.unpack_from("<5I", data, 16 + i * 20) for i in range(count)]
    records = []
    previous_end = index_end
    for i, (_cumulative, text_size, aux_size, text_offset, aux_offset) in enumerate(entries):
        next_offset = entries[i + 1][3] if i + 1 < count else len(data)
        if not (previous_end <= text_offset <= aux_offset <= next_offset <= len(data)):
            raise ValueError(f"Overlapping or out-of-bounds record {i}")
        if not (8 <= text_size <= aux_offset - text_offset):
            raise ValueError(f"Invalid string-region size in record {i}")
        if not (sum((16, 48, 16, 16, 16, 16)) <= aux_size <= next_offset - aux_offset):
            raise ValueError(f"Invalid auxiliary size in record {i}")
        block_size, _names = string_region(data, text_offset)
        if block_size > text_size:
            raise ValueError(f"ErtS block overruns declared string region in record {i}")

        cursor = aux_offset
        end = aux_offset + aux_size
        chunks = {}
        for expected_tag in CHUNK_ORDER:
            if cursor + 8 > end:
                raise ValueError(f"Truncated chunk header in record {i}")
            tag, size = struct.unpack_from("<4sI", data, cursor)
            if tag != expected_tag:
                raise ValueError(f"Unexpected chunk tag in record {i}: {tag!r}")
            if size < 16 or size % 16 or cursor + size > end:
                raise ValueError(f"Invalid chunk size in record {i}: {tag!r}")
            chunk = data[cursor:cursor + size]
            if tag == b"sreV" and size != 16:
                raise ValueError(f"Unexpected version-chunk size in record {i}")
            if tag == b"NrtS" and size != 16:
                raise ValueError(f"Unexpected NrtS size in record {i}")
            if tag == b"NpxE":
                (export_count,) = struct.unpack_from("<I", chunk, 8)
                if size != 16 + 16 * export_count:
                    raise ValueError(f"NpxE count/size mismatch in record {i}")
            chunks[tag.decode("ascii")] = chunk
            cursor += size
        if cursor != end:
            raise ValueError(f"Unparsed bytes inside declared chunks in record {i}")
        records.append({"text": data[text_offset:aux_offset], "chunks": chunks})
        previous_end = end
    return records


def compare_chunks(left, right):
    """Compare same-index serialized chunks, never claiming semantic equivalence."""
    checked = min(len(left), len(right))
    counts = {tag.decode("ascii"): 0 for tag in CHUNK_ORDER}
    differences = {tag.decode("ascii"): [] for tag in CHUNK_ORDER}
    identical_text_regions = 0
    identical_except_version = 0
    for i in range(checked):
        a, b = left[i], right[i]
        identical_text_regions += a["text"] == b["text"]
        identical_except_version += all(
            a["chunks"][tag.decode("ascii")] == b["chunks"][tag.decode("ascii")]
            for tag in CHUNK_ORDER[1:]
        )
        for tag in CHUNK_ORDER:
            name = tag.decode("ascii")
            if a["chunks"][name] == b["chunks"][name]:
                counts[name] += 1
            else:
                differences[name].append(i)
    return {
        "same_index_records_checked": checked,
        "identical_string_regions": identical_text_regions,
        "identical_chunks_except_version": identical_except_version,
        "identical_chunk_counts": counts,
        "different_indices": differences,
    }


def analyze(pc_zip, carbon_ps2_zip, undercover_ps2_zip):
    pc, _ = read_selected_members(pc_zip)
    carbon, _ = read_selected_members(carbon_ps2_zip)
    uc, _ = read_selected_members(undercover_ps2_zip)
    needed = (
        (pc, "GAMEPLAY.BIN", "carbon_pc_active"),
        (pc, "GAMEPLAY.BAK", "carbon_pc_backup"),
        (carbon, "GAMEPLAY.BIN", "carbon_ps2"),
        (uc, "GAMEPLAY.BIN", "undercover_ps2"),
    )
    records = {}
    for files, name, label in needed:
        if name not in files:
            raise ValueError(f"Missing {label}/{name}")
        records[label] = parse_chunks(files[name])
    return {
        "validated_records": {label: len(value) for label, value in records.items()},
        "six_chunk_order": [tag.decode("ascii") for tag in CHUNK_ORDER],
        "carbon_pc_backup_vs_ps2": compare_chunks(records["carbon_pc_backup"], records["carbon_ps2"]),
        "carbon_pc_active_vs_backup": compare_chunks(records["carbon_pc_active"], records["carbon_pc_backup"]),
        "undercover_ps2_vs_carbon_ps2_same_index": compare_chunks(records["undercover_ps2"], records["carbon_ps2"]),
        "limitations": "Exact chunk bytes only; not a payload decoder, event mapper, or PC runtime test.",
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
