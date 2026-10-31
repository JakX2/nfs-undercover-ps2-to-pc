#!/usr/bin/env python3
"""V31: select a real mono PS2 EA-MT10 SCHl from a local BIG blob.

Read-only offset scanner for extracted archive files that carry contiguous,
unobfuscated EA SCHl streams. It does NOT parse IDX indexes or split ZIP parts.
Only validated platform 5 / header v3 / mono / codec2=4 recordings are listed.

"scan" reports eligible offsets/sizes without exporting game media.
"verify" reconstructs a single selected SCHl in a PRIVATE temporary folder,
uses V28 for the PC-style header, and REQUIRES the independent vgmstream CLI
to verify exact PCM equality. Temporary WAVs and original excerpts are deleted.

"self-test" generates small, original synthetic EA-MT10 fixtures and exercises
the actual scanner plus the actual CLI. No game recordings are distributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

from undercover_mt10_private_bridge_v28 import (
    BridgeError, MAX_SOURCE_BYTES, parse_header, run_pair, validate_source,
)

SCAN_BLOCK = 1024 * 1024
MAX_HEADER_SIZE = 4096
MAX_TOTAL_BYTES = 16 * 1024 * 1024 * 1024
MAX_RESULTS = 20000
MAGIC = b"SCHl"
TAGS = {b"SCHl", b"SCCl", b"SCDl", b"SCEl", b"SCLl"}


class BIGProbeError(Exception):
    """Unsupported source, invalid offset or unsafe output."""


def read_exact(handle, offset: int, size: int, file_size: int) -> bytes:
    if offset < 0 or size < 0 or size > MAX_SOURCE_BYTES or offset + size > file_size:
        raise BIGProbeError("Read lies outside local BIG or single-SCHl bounds")
    handle.seek(offset)
    value = handle.read(size)
    if len(value) != size:
        raise BIGProbeError("Unexpected end of BIG while probing SCHl")
    return value


def probe_at(handle, start: int, file_size: int) -> dict:
    """Inspect chunk headers only, bounded to an individual possible SCHl."""
    raw_header = read_exact(handle, start, 12, file_size)
    if raw_header[:4] != MAGIC:
        raise BIGProbeError("Offset does not start with SCHl")
    header_length = struct.unpack_from("<I", raw_header, 4)[0]
    if not 24 <= header_length <= MAX_HEADER_SIZE:
        raise BIGProbeError("Invalid or unsupported SCHl header size")
    header = read_exact(handle, start, header_length, file_size)
    try:
        profile = parse_header(header)
    except BridgeError as exc:
        raise BIGProbeError("Unrecognized EA variable header") from exc
    if profile["platform"] != 5 or profile["version"] != 3:
        raise BIGProbeError("Not PS2 version 3")
    if profile["channels"] != 1 or profile["codec2"] != 4:
        raise BIGProbeError("Not mono MT10 codec2=4")
    if not isinstance(profile["sample_count"], int) or profile["sample_count"] <= 0:
        raise BIGProbeError("Missing positive source sample count")
    if not 8000 <= profile["rate"] <= 96000:
        raise BIGProbeError("Invalid original sample rate")

    pos = header_length
    count = None
    blocks = 0
    samples = 0
    saw_end = False
    for _ in range(100_000):
        if pos + 8 > MAX_SOURCE_BYTES:
            raise BIGProbeError("SCHl exceeds maximum individual stream size")
        ch = read_exact(handle, start + pos, 8, file_size)
        tag, chunk_bytes = ch[:4], struct.unpack_from("<I", ch, 4)[0]
        if tag not in TAGS or tag == b"SCHl" or chunk_bytes < 8:
            raise BIGProbeError("Invalid chunk inside SCHl candidate")
        if pos + chunk_bytes > MAX_SOURCE_BYTES or start + pos + chunk_bytes > file_size:
            raise BIGProbeError("Chunk extends beyond SCHl bound")
        if tag == b"SCCl":
            if count is not None or chunk_bytes < 12 or blocks:
                raise BIGProbeError("Unexpected SCCl chunk")
            count = struct.unpack("<I", read_exact(handle, start + pos + 8, 4, file_size))[0]
            if count < 1 or count > 100_000:
                raise BIGProbeError("Invalid declared audio block count")
        elif tag == b"SCDl":
            if count is None or chunk_bytes < 16:
                raise BIGProbeError("SCDl before SCCl or truncated")
            block_samples = struct.unpack(
                "<I", read_exact(handle, start + pos + 8, 4, file_size)
            )[0]
            if block_samples < 1 or block_samples > 10_000_000:
                raise BIGProbeError("Unreasonable SCDl samples")
            blocks += 1
            samples += block_samples
            if blocks > count:
                raise BIGProbeError("More SCDl than declared")
        elif tag == b"SCEl":
            if count != blocks or not blocks or samples != profile["sample_count"]:
                raise BIGProbeError("Block count/sample count mismatch")
            pos += chunk_bytes
            saw_end = True
            break
        pos += chunk_bytes

    if not saw_end:
        raise BIGProbeError("No terminating SCEl chunk")
    return {
        "offset": start,
        "length": pos,
        "platform": profile["platform"],
        "version": profile["version"],
        "codec2": profile["codec2"],
        "channels": profile["channels"],
        "rate_hz": profile["rate"],
        "samples": samples,
        "blocks": blocks,
        "header_bytes": header_length,
    }


def magic_offsets(handle, file_size: int, scan_block: int = SCAN_BLOCK):
    """Stream through a BIG with a 3-byte overlap, even at magic boundaries."""
    if scan_block < 4:
        raise BIGProbeError("scan_block must be at least four bytes")
    carry = b""
    cursor = 0
    while cursor < file_size:
        handle.seek(cursor)
        chunk = handle.read(min(scan_block, file_size - cursor))
        if not chunk:
            raise BIGProbeError("Source size changed while scanning")
        window = carry + chunk
        start_at = cursor - len(carry)
        search_from = 0
        while True:
            found = window.find(MAGIC, search_from)
            if found < 0:
                break
            yield start_at + found
            search_from = found + 1
        carry = window[-3:]
        cursor += len(chunk)


def scan_big(path: Path, *, max_results: int = 250,
             scan_block: int = SCAN_BLOCK) -> list[dict]:
    if not 1 <= max_results <= MAX_RESULTS:
        raise BIGProbeError("Requested candidate limit outside 1..20000")
    if not path.is_file():
        raise BIGProbeError("The local .BIG source file doesn't exist")
    file_size = path.stat().st_size
    if not 8 <= file_size <= MAX_TOTAL_BYTES:
        raise BIGProbeError("BIG size outside supported scan bounds (16 GiB)")
    found = []
    with path.open("rb") as stream:
        for offset in magic_offsets(stream, file_size, scan_block):
            try:
                candidate = probe_at(stream, offset, file_size)
            except (BIGProbeError, OSError, struct.error):
                continue
            found.append(candidate)
            if len(found) >= max_results:
                break
    return found


def extract_at(path: Path, offset: int) -> tuple[bytes, dict]:
    if not path.is_file():
        raise BIGProbeError("The local .BIG source file doesn't exist")
    file_size = path.stat().st_size
    if file_size > MAX_TOTAL_BYTES:
        raise BIGProbeError("BIG exceeds supported 16 GiB maximum")
    with path.open("rb") as stream:
        candidate = probe_at(stream, offset, file_size)
        raw = read_exact(stream, offset, candidate["length"], file_size)
    # Strong independent check: parse and audit ALL original compressed chunks.
    try:
        validate_source(raw)
    except (BridgeError, ValueError) as exc:
        raise BIGProbeError("Candidate rejected by independent V28 SCHl validator") from exc
    return raw, candidate


def verify_at(path: Path, offset: int, decoder: str,
              *, private_dir: Path | None = None, keep_pc: bool = False) -> dict:
    """Decode under both headers. No WAV, source excerpt or wrapper retained by default."""
    if not decoder:
        raise BIGProbeError("Real-clip verification REQUIRES an external decoder")
    original, candidate = extract_at(path, offset)
    with tempfile.TemporaryDirectory(prefix="nfs_v31_private_extract_") as folder:
        temp = Path(folder) / "one_original_schl.asf"
        temp.write_bytes(original)
        retained = None
        if keep_pc:
            if private_dir is None:
                raise BIGProbeError("--keep-pc-shape requires a private output directory")
            retained = private_dir / "experimental_pc_style.asf"
        result = run_pair(temp, decoder, retain=retained)
    if result.get("real_decoder_executed") is not True:
        raise BIGProbeError("Decoder did not execute; not a verified voice experiment")
    if result.get("pcm_equivalent") is not True:
        raise BIGProbeError("Decoder PCM mismatch: real pair cannot be accepted")
    result["format"] = "NFS_AUDIO_V31_PRIVATE_BIG_RECORDING_PCM_GATE"
    result["big_offset"] = candidate["offset"]
    result["big_stream_length"] = candidate["length"]
    result["candidate"] = candidate
    result["actual_undercover_provenance_confirmed"] = False
    result["carbon_pc_runtime_tested"] = False
    return result


def self_test(decoder: str) -> dict:
    """Synthetic BIG with decoys, a multi-frame stream and a three-block stream."""
    from ea_mt10_multiframe_scdl_v30 import make_single_block_stream
    from ea_mt10_multiblock_continuity_v29 import make_ps2_stream
    single = make_single_block_stream()
    multiblock = make_ps2_stream()
    with tempfile.TemporaryDirectory(prefix="nfs_v31_scanner_synthetic_") as folder:
        root = Path(folder)
        big = root / "generated_synthetic.BIG"
        # Scan must discover boundary-crossing magic, skip malformed bytes.
        prefix = b"junk" * 17 + b"SCHl\xFF\xFF\xFF\xFF"
        offset_one = len(prefix) + 31
        offset_two = offset_one + len(single) + 9
        big.write_bytes(prefix + b"x" * 31 + single + b"y" * 9 + multiblock)
        candidates = scan_big(big, scan_block=13)
        if [x["offset"] for x in candidates] != [offset_one, offset_two]:
            raise BIGProbeError("Synthetic BIG scanner missed or misidentified a SCHl")
        reports = [verify_at(big, ofs, decoder) for ofs in (offset_one, offset_two)]
        first_sha = reports[0]["decoded_pcm"]["original"]["pcm_sha256"]
        other_sha = reports[1]["decoded_pcm"]["original"]["pcm_sha256"]
        if first_sha != other_sha:
            raise BIGProbeError("Same generated MicroTalk sequence decoded differently by block packing")
        return {
            "format": "NFS_AUDIO_V31_BIG_SCANNER_REAL_DECODER_SELFTEST",
            "candidate_count": len(candidates),
            "candidate_offsets": [offset_one, offset_two],
            "identical_pcm_across_single_and_multiblock": True,
            "decoded_pcm_sha256": first_sha,
            "game_archive_read": False,
            "carbon_pc_runtime_tested": False,
        }


def new_json(path: Path, obj: dict) -> None:
    with path.open("x", encoding="utf-8") as output:
        json.dump(obj, output, indent=2, sort_keys=True)
        output.write("\n")


def int_offset(value: str) -> int:
    try:
        result = int(value, 0)
        if result < 0:
            raise ValueError()
        return result
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Offset must be nonnegative decimal or 0xhex") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    scan = subs.add_parser("scan", help="Find eligible mono PS2 MT10 SCHl offsets")
    scan.add_argument("--big", type=Path, required=True)
    scan.add_argument("--max-results", type=int, default=250)
    scan.add_argument("--report", type=Path, help="New JSON only; never overwrite")
    verify = subs.add_parser("verify", help="Decode one selected offset privately")
    verify.add_argument("--big", type=Path, required=True)
    verify.add_argument("--offset", type=int_offset, required=True)
    verify.add_argument("--decoder", required=True)
    verify.add_argument("--out-dir", type=Path, required=True)
    verify.add_argument("--keep-pc-shape", action="store_true")
    tst = subs.add_parser("self-test", help="Original synthetic BIG, real decoder")
    tst.add_argument("--decoder", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "self-test":
            result = self_test(args.decoder)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.action == "scan":
            if args.report and args.report.exists():
                raise BIGProbeError("Refusing to overwrite existing JSON report")
            matched = scan_big(args.big, max_results=args.max_results)
            result = {
                "format": "NFS_AUDIO_V31_BIG_SCHL_SCANNER",
                "matching_candidates": len(matched),
                "limit": args.max_results,
                "candidates": matched,
                "bytes_exported": 0,
                "audio_decoded": False,
            }
            if args.report:
                new_json(args.report, result)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        # "verify" is a real decoder gate, never just a structural success.
        if args.out_dir.exists():
            raise BIGProbeError("Refusing to overwrite an existing private output directory")
        args.out_dir.mkdir(parents=True, exist_ok=False)
        result = verify_at(args.big, args.offset, args.decoder,
                           private_dir=args.out_dir, keep_pc=args.keep_pc_shape)
        new_json(args.out_dir / "report.json", result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (BIGProbeError, BridgeError, OSError, ValueError) as exc:
        print(f"V31 BIG scanner/decoder: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
