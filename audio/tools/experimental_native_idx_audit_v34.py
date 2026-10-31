#!/usr/bin/env python3
"""V34 experimental Black Box IDX offset-table auditor, read-only.

Public evidence (ResHax 2023, Carbon original Xbox) describes an IDX header
with a uint32 count at 0x54 and entries of FOUR uint32 values:
  raw_id, unknown_1, unknown_2, big_offset.
That is an EXPERIMENTAL PROFILE, not a verified Undercover PS2 binary format.

Parse both candidate byte orders, accept exactly one plausible interpretation,
and test every offset against an actual SCHl boundary in the accompanying BIG.
Do NOT equate raw_id or unknown fields with CSI/EVT group IDs.

No original audio is exported. All reports contain only numeric metadata.
A self-test builds original synthetic MT10 streams and can invoke the actual
upstream vgmstream decoder to validate the indexed byte ranges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from undercover_big_voice_scan_v31 import BIGProbeError, probe_at, verify_at

COUNT_OFFSET = 0x54
ENTRY_OFFSET = 0x58
ENTRY_SIZE = 16
MAX_RECORDS = 100_000
MAX_IDX_BYTES = 16 * 1024 * 1024
MAX_BIG_BYTES = 16 * 1024 * 1024 * 1024
PROFILE = "experimental_blackbox_idx_count_0x54_records_16"


class NativeIDXError(Exception):
    """Unsupported candidate index or unsafe operation."""


def parse_table(data: bytes, big_size: int, endian: str) -> dict:
    if endian not in ("little", "big"):
        raise NativeIDXError("Byte order must be little or big")
    if len(data) < ENTRY_OFFSET or len(data) > MAX_IDX_BYTES:
        raise NativeIDXError("IDX size outside experimental profile bounds")
    if not 16 <= big_size <= MAX_BIG_BYTES:
        raise NativeIDXError("BIG size outside supported bounds")
    fmt = "<" if endian == "little" else ">"
    count = struct.unpack_from(fmt + "I", data, COUNT_OFFSET)[0]
    if not 1 <= count <= MAX_RECORDS:
        raise NativeIDXError("Unreasonable IDX entry count")
    end = ENTRY_OFFSET + count * ENTRY_SIZE
    if end > len(data):
        raise NativeIDXError("IDX table truncated")
    records = []
    previous_offset = -1
    for index in range(count):
        raw_id, unknown1, unknown2, offset = struct.unpack_from(
            fmt + "IIII", data, ENTRY_OFFSET + index * ENTRY_SIZE
        )
        if offset <= previous_offset or offset >= big_size:
            raise NativeIDXError("IDX BIG offsets are not strictly increasing/in bounds")
        records.append({
            "ordinal": index,
            "raw_id": raw_id,
            "unknown_1": unknown1,
            "unknown_2": unknown2,
            "big_offset": offset,
        })
        previous_offset = offset
    for i, record in enumerate(records):
        end_offset = (records[i + 1]["big_offset"]
                      if i + 1 < count else big_size)
        span = end_offset - record["big_offset"]
        if span <= 0:
            raise NativeIDXError("Non-positive indexed BIG span")
        record["big_span_bytes"] = span
    return {
        "profile": PROFILE,
        "source_profile_proven_for_undercover_ps2": False,
        "endian": endian,
        "declared_records": count,
        "trailing_idx_bytes": len(data) - end,
        "records": records,
    }


def detect_table(data: bytes, big_size: int, mode: str = "auto") -> dict:
    if mode in ("little", "big"):
        return parse_table(data, big_size, mode)
    if mode != "auto":
        raise NativeIDXError("Invalid byte order mode")
    matches = []
    for endian in ("little", "big"):
        try:
            matches.append(parse_table(data, big_size, endian))
        except NativeIDXError:
            pass
    if len(matches) != 1:
        raise NativeIDXError("No unique plausible byte order; specify --endian explicitly")
    return matches[0]


def audit(idx: Path, big: Path, endian: str = "auto",
          *, probe_limit: int = MAX_RECORDS) -> dict:
    if not 1 <= probe_limit <= MAX_RECORDS:
        raise NativeIDXError("Invalid --probe-limit")
    if not idx.is_file() or idx.stat().st_size > MAX_IDX_BYTES:
        raise NativeIDXError("Missing/oversized IDX")
    if not big.is_file() or big.stat().st_size > MAX_BIG_BYTES:
        raise NativeIDXError("Missing/oversized BIG")
    idx_data = idx.read_bytes()
    big_size = big.stat().st_size
    table = detect_table(idx_data, big_size, endian)
    for record in table["records"]:
        record["schl_status"] = "not_probed"
        record["schl_length_bytes"] = None
        record["schl_samples"] = None
        record["schl_blocks"] = None
    valid = 0
    padded = 0
    invalid = 0
    with big.open("rb") as stream:
        for record in table["records"][:probe_limit]:
            try:
                source = probe_at(stream, record["big_offset"], big_size)
                if source["length"] > record["big_span_bytes"]:
                    record["schl_status"] = "schl_extends_beyond_index_span"
                    invalid += 1
                    continue
                record["schl_length_bytes"] = source["length"]
                record["schl_samples"] = source["samples"]
                record["schl_blocks"] = source["blocks"]
                record["schl_status"] = ("exact_schl_span" if
                    source["length"] == record["big_span_bytes"]
                    else "schl_within_padded_idx_span")
                if record["schl_status"] == "exact_schl_span":
                    valid += 1
                else:
                    padded += 1
            except (BIGProbeError, OSError, struct.error):
                record["schl_status"] = "not_supported_mono_ps2_v3_mt10_schl"
                invalid += 1
    # A count of matched offsets only supports the profile's offset hypothesis.
    # Unknown dwords are opaque, not group IDs, even if they appear familiar.
    table.update({
        "format": "NFS_AUDIO_V34_EXPERIMENTAL_NATIVE_IDX_AUDIT",
        "read_only": True,
        "big_bytes": big_size,
        "idx_bytes": len(idx_data),
        "idx_sha256": hashlib.sha256(idx_data).hexdigest(),
        "schl_probe_limit": probe_limit,
        "probed_records": min(probe_limit, table["declared_records"]),
        "exact_schl_spans": valid,
        "schl_inside_index_span": padded,
        "invalid_or_other_streams": invalid,
        "no_audio_bytes_exported": True,
        "raw_id_semantics_known": False,
        "group_or_police_event_identity_confirmed": False,
        "real_decoder_executed": False,
        "game_runtime_tested": False,
    })
    return table


def make_synthetic_idx(big_size: int, offsets: list[int],
                       endian: str = "little") -> bytes:
    fmt = "<" if endian == "little" else ">"
    b = bytearray(ENTRY_OFFSET)
    # Original research fixture: unknown initial header bytes are zero.
    struct.pack_into(fmt + "I", b, COUNT_OFFSET, len(offsets))
    for ordinal, offset in enumerate(offsets):
        b.extend(struct.pack(fmt + "IIII", 900 + ordinal, 7, 8, offset))
    return bytes(b)


def self_test(decoder: str) -> dict:
    from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
    from ea_mt10_multiblock_continuity_v29 import make_ps2_stream
    a = make_single_block_stream()
    b = make_ps2_stream()
    with tempfile.TemporaryDirectory(prefix="nfs_v34_idx_synthetic_") as tmp:
        home = Path(tmp)
        original_big = home / "original_generated.BIG"
        prefix = b"\x00" * 32
        pad = b"\x00" * 19
        offset1 = len(prefix)
        offset2 = offset1 + len(a) + len(pad)
        original_big.write_bytes(prefix + a + pad + b)
        original_idx = home / "original_generated.IDX"
        original_idx.write_bytes(
            make_synthetic_idx(original_big.stat().st_size, [offset1, offset2])
        )
        report = audit(original_idx, original_big)
        if (report["declared_records"] != 2 or
            report["exact_schl_spans"] != 1 or
            report["schl_inside_index_span"] != 1):
            raise NativeIDXError("Synthetic IDX/BIG boundaries not verified")
        outcomes = [
            verify_at(original_big, offset1, decoder),
            verify_at(original_big, offset2, decoder),
        ]
        a_sha = outcomes[0]["decoded_pcm"]["original"]["pcm_sha256"]
        b_sha = outcomes[1]["decoded_pcm"]["original"]["pcm_sha256"]
        if a_sha != b_sha:
            raise NativeIDXError("Same MT10 audio decoded differently across layout")
        return {
            "format": "NFS_AUDIO_V34_IDX_OFFSETS_REAL_DECODER_SELFTEST",
            "idx_offset_profile_tested": PROFILE,
            "idx_records": 2,
            "exact_schl_spans": report["exact_schl_spans"],
            "schl_inside_padded_spans": report["schl_inside_index_span"],
            "independent_pcm_pairs_verified": 2,
            "same_decoded_audio_hash": a_sha,
            "game_audio_used": False,
            "undercover_ps2_idx_profile_confirmed": False,
            "carbon_pc_runtime_verified": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("audit", help="Test Xbox-documented candidate IDX layout")
    run.add_argument("--idx", type=Path, required=True)
    run.add_argument("--big", type=Path, required=True)
    run.add_argument("--endian", choices=("auto", "little", "big"), default="auto")
    run.add_argument("--probe-limit", type=int, default=MAX_RECORDS)
    run.add_argument("--report", type=Path, required=True)
    test = sub.add_parser("self-test", help="Synthetic IDX + BIG, real MT10 decoder")
    test.add_argument("--decoder", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "self-test":
            print(json.dumps(self_test(args.decoder), sort_keys=True, indent=2))
            return 0
        if args.report.exists() or args.report.resolve() in (
            args.idx.resolve(), args.big.resolve()
        ):
            raise NativeIDXError("Refusing to overwrite an existing input/output")
        result = audit(args.idx, args.big, args.endian, probe_limit=args.probe_limit)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(result, output, sort_keys=True, indent=2)
            output.write("\n")
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (NativeIDXError, OSError, ValueError) as exc:
        print(f"V34 experimental IDX probe failed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
