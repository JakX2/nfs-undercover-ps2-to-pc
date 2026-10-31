#!/usr/bin/env python3
"""V25: verify an Undercover SCHl stream and a PC-shaped copy block-by-block.

The experiment preserves all bytes after the SCHl header; this tool checks
that claim on *individual* user-supplied recordings. An optional independent
vgmstream decode verifies actual PCM equality. Nothing modifies game assets.
The default structural audit never decodes or writes audio.

All chunk sizes here are for little-endian EA SCHl. This deliberately does
not accept whole IDX/BIG banks, localized video blocks, or big-endian streams.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ea_mt10_pcm_equivalence_v22 import (
    AudioCheckError, compare_wavs, decode_one, resolve_decoder, sha256_file,
)

MAX_STREAM_SIZE = 64 * 1024 * 1024
MAX_CHUNKS = 100_000
KNOWN_TAGS = {b"SCHl", b"SCCl", b"SCDl", b"SCEl", b"SCLl"}


class SCHlAuditError(Exception):
    """Unsupported or corrupted input, or unsafe output."""


@dataclass(frozen=True)
class Chunk:
    tag: bytes
    offset: int
    size: int


def parse_stream(data: bytes) -> dict[str, Any]:
    """Walk a standalone little-endian EA stream with strict boundaries."""
    if not (16 <= len(data) <= MAX_STREAM_SIZE):
        raise SCHlAuditError("Stream size outside supported bounds")
    chunks: list[Chunk] = []
    pos = 0
    end = None
    while pos < len(data):
        if len(chunks) >= MAX_CHUNKS:
            raise SCHlAuditError("Too many SCHl chunks")
        if len(data) - pos < 8:
            raise SCHlAuditError("Truncated chunk header")
        tag = data[pos:pos+4]
        if tag not in KNOWN_TAGS:
            raise SCHlAuditError(f"Unsupported EA chunk {tag!r} at {pos}")
        size = struct.unpack_from("<I", data, pos + 4)[0]
        if size < 8 or size > len(data) - pos:
            raise SCHlAuditError(f"Invalid {tag!r} chunk size at {pos}")
        if not chunks and tag != b"SCHl":
            raise SCHlAuditError("First chunk must be SCHl")
        if chunks and tag == b"SCHl":
            raise SCHlAuditError("Unexpected second SCHl header")
        if tag == b"SCCl" and size < 12:
            raise SCHlAuditError("Truncated SCCl count chunk")
        if tag == b"SCDl" and size < 16:
            raise SCHlAuditError("Truncated SCDl block")
        chunks.append(Chunk(tag, pos, size))
        pos += size
        if tag == b"SCEl":
            end = pos
            break
    if end is None:
        raise SCHlAuditError("Missing SCEl terminator")
    if any(data[end:]):
        raise SCHlAuditError("Unexpected nonzero bytes after SCEl")
    # A short all-zero alignment tail is harmless; do not compare it with audio.
    if len(data) - end > 255:
        raise SCHlAuditError("Unexpectedly long post-stream padding")

    header = chunks[0]
    count_chunks = [c for c in chunks[1:] if c.tag == b"SCCl"]
    audio = [c for c in chunks[1:] if c.tag == b"SCDl"]
    if len(count_chunks) != 1:
        raise SCHlAuditError("Expected exactly one SCCl count chunk")
    if not audio:
        raise SCHlAuditError("No SCDl audio blocks")
    if any(c.tag == b"SCCl" for c in chunks[chunks.index(audio[0])+1:]):
        raise SCHlAuditError("SCCl count must precede all SCDl blocks")
    if chunks[-1].tag != b"SCEl":
        raise SCHlAuditError("SCEl must terminate the chunk list")
    declared_blocks = struct.unpack_from("<I", data, count_chunks[0].offset + 8)[0]
    if declared_blocks != len(audio):
        raise SCHlAuditError(
            f"SCCl declared {declared_blocks} SCDl blocks, found {len(audio)}"
        )

    block_samples = [
        struct.unpack_from("<I", data, chunk.offset + 8)[0] for chunk in audio
    ]
    if any(s <= 0 or s > 10_000_000 for s in block_samples):
        raise SCHlAuditError("Invalid SCDl block sample count")
    total_samples = sum(block_samples)

    def sha256(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    return {
        "header_size": header.size,
        "header_sha256": sha256(data[:header.size]),
        "post_header_bytes": end - header.size,
        "post_header_sha256": sha256(data[header.size:end]),
        "chunk_tags": [chunk.tag.decode("ascii") for chunk in chunks],
        "chunk_count": len(chunks),
        "audio_block_count": len(audio),
        "declared_block_count": declared_blocks,
        "total_scdl_samples": total_samples,
        "scdl_samples_sha256": sha256(
            b"".join(struct.pack("<I", n) for n in block_samples)
        ),
        "scdl_chunk_sha256": [
            sha256(data[c.offset:c.offset+c.size]) for c in audio
        ],
        "audio_block_bytes_total": sum(c.size for c in audio),
        "trailing_zero_pad_bytes": len(data) - end,
    }


def inspect_one(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SCHlAuditError(f"No input stream: {path}")
    if path.stat().st_size > MAX_STREAM_SIZE:
        raise SCHlAuditError("Input exceeds the maximum single-stream size")
    raw = path.read_bytes()
    result = parse_stream(raw)
    result["file_size"] = len(raw)
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def compare(original: Path, experimental: Path) -> dict[str, Any]:
    if original.resolve() == experimental.resolve():
        raise SCHlAuditError("Cannot compare the same source path")
    a = inspect_one(original)
    b = inspect_one(experimental)
    post_header_equal = (
        a["post_header_bytes"] == b["post_header_bytes"] and
        a["post_header_sha256"] == b["post_header_sha256"]
    )
    equal_blocks = a["scdl_chunk_sha256"] == b["scdl_chunk_sha256"]
    checks = {
        "unchanged_post_header_bytes": post_header_equal,
        "identical_audio_blocks": equal_blocks,
        "unchanged_chunk_order": a["chunk_tags"] == b["chunk_tags"],
        "unchanged_block_sample_counts":
            a["scdl_samples_sha256"] == b["scdl_samples_sha256"],
    }
    return {
        "format": "NFS_AUDIO_V25_SCHL_WRAPPER_AUDIT",
        "source": "individual EA SCHl files, not full banks",
        "original": a,
        "experimental": b,
        "checks": checks,
        "structurally_lossless_wrapper": all(checks.values()),
        "decoder_executed": False,
        "ea_mt10_encoding_verified": False,
        "carbon_pc_playback_verified": False,
    }


def decode_pair(
    decoder: str, original: Path, experimental: Path, timeout: int
) -> dict[str, Any]:
    if timeout <= 0:
        raise SCHlAuditError("Timeout must be positive")
    decoder_path = resolve_decoder(decoder)
    with tempfile.TemporaryDirectory(prefix="nfs_v25_private_pcm_") as tmp:
        original_wav = Path(tmp) / "original.wav"
        experimental_wav = Path(tmp) / "experimental.wav"
        decode_one(decoder_path, original, original_wav, timeout)
        decode_one(decoder_path, experimental, experimental_wav, timeout)
        comparison = compare_wavs(original_wav, experimental_wav)
    return {
        "decoder_sha256": sha256_file(Path(decoder_path)),
        "decoded_pcm_comparison": comparison,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--experimental", type=Path, required=True)
    parser.add_argument("--decoder",
                        help="Optional vgmstream-cli path for real PCM comparison")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--report", type=Path, help="New JSON report, never overwrite")
    args = parser.parse_args(argv)
    try:
        if args.report and args.report.exists():
            raise SCHlAuditError("Report already exists; refusing to overwrite")
        result = compare(args.original, args.experimental)
        if args.decoder is not None:
            result["decoder_executed"] = True
            result["real_decoder"] = decode_pair(
                args.decoder, args.original, args.experimental, args.timeout
            )
        pcm_ok = (
            not args.decoder or
            result["real_decoder"]["decoded_pcm_comparison"]["exact_pcm_match"]
        )
        passed = result["structurally_lossless_wrapper"] and pcm_ok
        result["passed"] = bool(passed)
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.report:
            with args.report.open("x", encoding="utf-8") as output:
                output.write(serialized)
        print(serialized, end="")
        return 0 if passed else 1
    except (SCHlAuditError, AudioCheckError, OSError) as exc:
        print(f"V25 wrapper validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
