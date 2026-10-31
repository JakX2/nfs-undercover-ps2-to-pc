#!/usr/bin/env python3
"""V36: discover candidate IDX record layouts from independently scanned SCHl offsets.

Do NOT trust a platform-specific IDX schema by default. Given an original IDX
and a V31 scan JSON for the SAME user-owned BIG, test bounded combinations of
integer count/header positions, table starts, row widths, offset columns and
byte orders. Rank only layouts whose sampled offset columns match independently
validated original SCHl start offsets.

This is a heuristic DISCOVERY tool, not a complete native IDX parser. All raw
index fields remain opaque. In particular, IDX IDs are not police event IDs.
Never infer a valid game identity from a layout score or CSV export.

No BIG data or copyrighted audio is read by this script; only numeric scan
metadata and the local IDX bytes. Both inputs are read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from idx_evt_csi_evidence_join_v33 import AttributionError, load_scan

MAX_IDX_BYTES = 16 * 1024 * 1024
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_COUNT = 100_000
MAX_LAYOUTS = 20
COUNT_POSITIONS = tuple(range(0, 0x84, 4))
TABLE_GAPS = (4, 8, 12, 16, 20, 24, 32, 48, 64)
ROW_WIDTHS = (8, 12, 16, 20, 24, 32)
SAMPLE_SIZE = 96
MIN_MATCHES = 3
MIN_SAMPLE_MATCH_RATIO = 0.75
FORMAT = "NFS_AUDIO_V36_IDX_LAYOUT_DISCOVERY"


class LayoutError(Exception):
    """Invalid original metadata or unsupported/ambiguous layout."""


def read_idx(path: Path) -> bytes:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_IDX_BYTES:
        raise LayoutError("IDX absent or larger than bounded read")
    return path.read_bytes()


def read_scan(path: Path) -> set[int]:
    if not path.is_file() or path.stat().st_size > MAX_REPORT_BYTES:
        raise LayoutError("Missing/oversized V31 JSON")
    return {item["offset"] for item in load_scan(path)}


def sampled_indices(count: int) -> tuple[int, ...]:
    """Uniformly probe table start, middle and end before considering a layout."""
    if count < 1:
        raise LayoutError("Non-positive candidate count")
    if count <= SAMPLE_SIZE:
        return tuple(range(count))
    return tuple(sorted(set(
        (i * (count - 1)) // (SAMPLE_SIZE - 1)
        for i in range(SAMPLE_SIZE)
    )))


def score_profile(data: bytes, starts: set[int], *, endian: str,
                  count_pos: int, table_start: int, stride: int,
                  offset_in_row: int) -> dict | None:
    if endian not in ("little", "big") or stride not in ROW_WIDTHS:
        return None
    if count_pos < 0 or count_pos + 4 > len(data):
        return None
    if table_start < count_pos + 4 or table_start % 4 or count_pos % 4:
        return None
    if offset_in_row < 0 or offset_in_row + 4 > stride or offset_in_row % 4:
        return None
    fmt = "<I" if endian == "little" else ">I"
    count = struct.unpack_from(fmt, data, count_pos)[0]
    if count < MIN_MATCHES or count > MAX_COUNT:
        return None
    table_end = table_start + count * stride
    if table_end > len(data):
        return None
    indices = sampled_indices(count)
    hits = []
    misses = []
    offsets = []
    for row in indices:
        position = table_start + row * stride + offset_in_row
        offset = struct.unpack_from(fmt, data, position)[0]
        offsets.append(offset)
        if offset in starts:
            hits.append(row)
        else:
            misses.append(row)
    ratio = len(hits) / len(indices)
    if len(hits) < MIN_MATCHES or ratio < MIN_SAMPLE_MATCH_RATIO:
        return None
    # Opaque rows can be aliased or unsorted. Record both, never discard
    # plausible non-monotonic candidates just to force Xbox assumptions.
    distinct_hits = len(set(offsets[row_to_index] for row_to_index, row
                            in enumerate(indices) if row in hits))
    if distinct_hits < MIN_MATCHES:
        return None
    monotonic = all(a < b for a, b in zip(offsets, offsets[1:]))
    return {
        "endian": endian,
        "count_field_position": count_pos,
        "record_table_start": table_start,
        "record_stride": stride,
        "offset_field_position_in_record": offset_in_row,
        "record_count": count,
        "sampled_rows": len(indices),
        "matching_sampled_rows": len(hits),
        "unique_matching_offsets": distinct_hits,
        "sample_match_ratio": round(ratio, 6),
        "sampled_offsets_strictly_increasing": monotonic,
        "trailing_idx_bytes": len(data) - table_end,
        "raw_id_and_group_semantics_known": False,
        "undercover_ps2_format_confirmed": False,
    }


def discover(data: bytes, offsets: set[int], *, top: int = 10,
             maximum_count: int = MAX_COUNT) -> dict:
    if not 1 <= top <= MAX_LAYOUTS:
        raise LayoutError("Top layout count must be 1..20")
    if not 3 <= maximum_count <= MAX_COUNT:
        raise LayoutError("Maximum IDX entry count must be 3..100000")
    if len(data) < 16 or len(data) > MAX_IDX_BYTES:
        raise LayoutError("IDX length outside safe analysis range")
    if not offsets:
        raise LayoutError("V31 scan has no validated SCHl offsets")
    results = []
    tested = 0
    for endian in ("little", "big"):
        for count_pos in COUNT_POSITIONS:
            if count_pos + 4 > len(data):
                break
            count = struct.unpack_from(
                "<I" if endian == "little" else ">I", data, count_pos
            )[0]
            if not MIN_MATCHES <= count <= maximum_count:
                continue
            for gap in TABLE_GAPS:
                start = count_pos + gap
                if start % 4:
                    continue
                for stride in ROW_WIDTHS:
                    if start + count * stride > len(data):
                        continue
                    for position in range(0, stride, 4):
                        tested += 1
                        item = score_profile(
                            data, offsets, endian=endian, count_pos=count_pos,
                            table_start=start, stride=stride,
                            offset_in_row=position
                        )
                        if item is not None:
                            results.append(item)
    # Ranking is an investigative aid, NOT a probability or verified schema.
    # Prefer high coverage, distinct offsets, fewer dangling IDX bytes, then
    # smaller table gaps. Return all ties, but cap output at 20 candidates.
    results.sort(key=lambda p: (
        -p["sample_match_ratio"],
        -p["unique_matching_offsets"],
        p["trailing_idx_bytes"],
        p["record_table_start"] - p["count_field_position"],
        p["record_stride"],
        p["offset_field_position_in_record"],
    ))
    all_matches = len(results)
    selected = results[:top]
    return {
        "format": FORMAT,
        "read_only": True,
        "candidate_schema_tests_run": tested,
        "validated_schl_offsets_supplied": len(offsets),
        "qualifying_layouts_total": all_matches,
        "displayed_layouts": selected,
        "layouts_truncated": all_matches > len(selected),
        "layout_is_not_proof_of_native_undercover_format": True,
        "unknown_idx_words_not_mapped_to_group_or_event": True,
        "real_game_audio_decoded": False,
        "carbon_runtime_tested": False,
    }


def investigate(idx: Path, scan: Path, top: int = 10) -> dict:
    data = read_idx(idx)
    offsets = read_scan(scan)
    report = discover(data, offsets, top=top)
    report["idx_sha256"] = hashlib.sha256(data).hexdigest()
    report["v31_scan_json_sha256"] = hashlib.sha256(scan.read_bytes()).hexdigest()
    report["idx_bytes"] = len(data)
    return report


def fake_idx(offsets: list[int], count_pos: int, gap: int,
             stride: int, offset_column: int, endian: str) -> bytes:
    """Synthetic non-proprietary IDX layout, NOT an EA native encoder."""
    fmt = "<I" if endian == "little" else ">I"
    if offset_column + 4 > stride:
        raise LayoutError("Invalid synthetic IDX column")
    data = bytearray(count_pos + gap + len(offsets) * stride)
    struct.pack_into(fmt, data, count_pos, len(offsets))
    for ordinal, offset in enumerate(offsets):
        record_at = count_pos + gap + ordinal * stride
        struct.pack_into(fmt, data, record_at + offset_column, offset)
    return bytes(data)


def self_test() -> dict:
    """Two distinct original synthetic IDX schemas both found from scan data."""
    starts = [64, 160, 300, 512, 900]
    expected = [
        ("little", 0x54, 4, 16, 12),
        ("big", 0x10, 8, 12, 4),
    ]
    matched = []
    for endian, count_pos, gap, stride, field in expected:
        data = fake_idx(starts, count_pos, gap, stride, field, endian)
        report = discover(data, set(starts))
        if not any(
            x["endian"] == endian and x["count_field_position"] == count_pos
            and x["record_table_start"] == count_pos + gap
            and x["record_stride"] == stride
            and x["offset_field_position_in_record"] == field
            and x["matching_sampled_rows"] == len(starts)
            for x in report["displayed_layouts"]
        ):
            raise LayoutError("Synthetic native-table hypothesis was not discovered")
        matched.append({"endian": endian, "stride": stride, "offset_column": field})
    # Also prove the same discovery works from actual V31 SCHl scan output,
    # not just a hand-authored set of integer offsets.
    from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
    from ea_mt10_multiblock_continuity_v29 import make_ps2_stream
    from undercover_big_voice_scan_v31 import scan_big
    with tempfile.TemporaryDirectory(prefix="nfs_v36_layout_synthetic_") as folder:
        root = Path(folder)
        big = root / "synthetic.BIG"
        chunks = [make_single_block_stream(), make_ps2_stream()] * 2
        buf = bytearray(b"Z" * 64)
        discovered_starts = []
        for chunk in chunks:
            discovered_starts.append(len(buf))
            buf.extend(chunk)
            buf.extend(b"pad_9byte")
        big.write_bytes(buf)
        valid = scan_big(big, scan_block=11)
        if [r["offset"] for r in valid] != discovered_starts:
            raise LayoutError("Real SCHl scanner did not match synthetic IDX offsets")
        scan_json = root / "scan.json"
        scan_json.write_text(json.dumps({
            "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER",
            "candidates": valid,
        }))
        idx = root / "synthetic.IDX"
        idx.write_bytes(fake_idx(discovered_starts, 0x54, 4, 16, 12, "little"))
        integrated = investigate(idx, scan_json)
        if not integrated["displayed_layouts"]:
            raise LayoutError("IDX layout could not be recovered from real SCHl scanner")
    return {
        "format": "NFS_AUDIO_V36_SYNTHETIC_LAYOUT_DISCOVERY_SELFTEST",
        "distinct_synthetic_layouts_found": len(matched),
        "layouts": matched,
        "real_schl_scanner_integrated": True,
        "game_data_used": False,
        "undercover_native_idx_format_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("discover", help="Rank offset column hypotheses from V31 scan")
    run.add_argument("--idx", required=True, type=Path)
    run.add_argument("--scan", required=True, type=Path)
    run.add_argument("--top", type=int, default=10)
    run.add_argument("--report", required=True, type=Path)
    sub.add_parser("self-test")
    args = p.parse_args(argv)
    try:
        if args.mode == "self-test":
            report = self_test()
        else:
            if args.report.exists() or args.report.resolve() in (
                args.idx.resolve(), args.scan.resolve()
            ):
                raise LayoutError("Refusing to overwrite existing source/report")
            report = investigate(args.idx, args.scan, top=args.top)
            with args.report.open("x", encoding="utf-8") as output:
                json.dump(report, output, indent=2, sort_keys=True)
                output.write("\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (LayoutError, AttributionError, OSError, ValueError) as exc:
        print(f"V36 IDX layout discovery: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
