#!/usr/bin/env python3
"""V26: real EA SCHl parser test using ORIGINAL synthetic PCM audio.

Construct two little-endian EA SCHl streams using the SAME SCCl/SCDl/SCEl
blocks and different original-style variable headers: PS2 version 3 and PC
version 2. Check the actual official vgmstream-cli decode on both.

THIS IS NOT EA-MT10: codec2 0 is uncompressed 16-bit PCM. The test addresses
the EA SCHl header/blocked-layout path, not the MicroTalk codec.
No copyrighted audio, original game files, or runtime patches are involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import compare_wavs, inspect_pcm16_wav
from schl_wrapper_audit_v25 import compare as compare_schl
from vgmstream_metadata_preflight_v23 import get_metadata, resolve_decoder

RATE = 22050
FRAMES = 4096
BLOCK_FRAMES = 2048
CODEC2_S16LE_INT = 0
PLATFORM_PS2 = 5
PLATFORM_PC = 0


class SyntheticEAError(Exception):
    pass


def patch(tag: int, value: int) -> bytes:
    """Variable EA header numeric patch; value uses big-endian-sized integer."""
    if not 0 <= tag <= 0xFF or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("EA patch value out of range")
    width = max(1, (value.bit_length() + 7) // 8)
    return bytes((tag, width)) + value.to_bytes(width, "big")


def ea_chunk(tag: bytes, data: bytes = b"") -> bytes:
    if len(tag) != 4:
        raise ValueError("EA chunk type must have exactly 4 bytes")
    return tag + struct.pack("<I", len(data) + 8) + data


def make_pcm() -> bytes:
    audio = bytearray()
    for i in range(FRAMES):
        sample = round(10000 * math.sin(2 * math.pi * 330 * i / RATE))
        audio += struct.pack("<h", sample)
    return bytes(audio)


def make_header(platform: int, version: int, *, priority_patch: bool) -> bytes:
    if (platform, version) not in ((PLATFORM_PS2, 3), (PLATFORM_PC, 2)):
        raise ValueError("Only the chosen synthetic PS2 v3 and PC v2 cases exist")
    # "PT" + 16-bit LE platform, as read by vgmstream ea_schl.c.
    header = bytearray(b"PT" + struct.pack("<H", platform))
    header += patch(0x80, version)  # version
    header += patch(0x82, 1)  # channels
    header += patch(0x84, RATE)  # sample rate
    header += patch(0x85, FRAMES)  # total PCM frames
    header += patch(0xA0, CODEC2_S16LE_INT)  # codec2 = PCM16 interleaved
    if priority_patch:
        header += patch(0x06, 101)  # harmless priority value
    header += b"\xFF"
    # Variable header alignment, *after* its end patch.
    header += b"\x00" * (-len(header) % 4)
    return ea_chunk(b"SCHl", bytes(header))


def make_blocks(pcm: bytes) -> bytes:
    if len(pcm) != FRAMES * 2:
        raise ValueError("Unexpected synthetic PCM length")
    output = bytearray()
    output += ea_chunk(b"SCCl", struct.pack("<I", FRAMES // BLOCK_FRAMES))
    for start in range(0, FRAMES, BLOCK_FRAMES):
        frame_bytes = pcm[start * 2 : (start + BLOCK_FRAMES) * 2]
        # offset 0 points to the first byte after the channel-offset table.
        output += ea_chunk(
            b"SCDl", struct.pack("<II", BLOCK_FRAMES, 0) + frame_bytes
        )
    output += ea_chunk(b"SCEl")
    return bytes(output)


def build_pair(pcm: bytes) -> tuple[bytes, bytes]:
    blocks = make_blocks(pcm)
    ps2 = make_header(PLATFORM_PS2, 3, priority_patch=True) + blocks
    pc = make_header(PLATFORM_PC, 2, priority_patch=False) + blocks
    return ps2, pc


def decode_one(decoder: Path, source: Path, wav: Path) -> None:
    result = subprocess.run(
        [str(decoder), "-i", "-o", str(wav), str(source)],
        capture_output=True, timeout=45
    )
    if result.returncode != 0 or not wav.is_file():
        msg = (result.stdout + result.stderr)[-1500:].decode("utf-8", "replace")
        raise SyntheticEAError("vgmstream could not decode synthetic EA SCHl: " + msg)


def run_test(decoder: Path) -> dict:
    pcm = make_pcm()
    ps2_stream, pc_stream = build_pair(pcm)
    with tempfile.TemporaryDirectory(prefix="nfs_v26_synthetic_ea_schl_") as folder:
        root = Path(folder)
        ps2 = root / "ps2_v3.asf"
        pc = root / "pc_v2.asf"
        ps2.write_bytes(ps2_stream)
        pc.write_bytes(pc_stream)
        block_report = compare_schl(ps2, pc)
        if not block_report["structurally_lossless_wrapper"]:
            raise SyntheticEAError("PC-style header unexpectedly changed audio blocks")
        ps2_metadata = get_metadata(decoder, ps2, 30)
        pc_metadata = get_metadata(decoder, pc, 30)
        for item in (ps2_metadata, pc_metadata):
            if item["sample_rate_hz"] != RATE or item["channels"] != 1:
                raise SyntheticEAError("Unexpected metadata: " + str(item))
            if item["total_samples"] != FRAMES:
                raise SyntheticEAError("Unexpected stream sample count: " + str(item))
            if "PCM" not in item["encoding"].upper():
                raise SyntheticEAError("This fixture should decode as uncompressed PCM")
        ps2_wav = root / "ps2.wav"
        pc_wav = root / "pc.wav"
        decode_one(decoder, ps2, ps2_wav)
        decode_one(decoder, pc, pc_wav)
        ps2_details = inspect_pcm16_wav(ps2_wav)
        pc_details = inspect_pcm16_wav(pc_wav)
        native_hash = hashlib.sha256(pcm).hexdigest()
        if ps2_details["pcm_sha256"] != native_hash:
            raise SyntheticEAError("PS2-version EA SCHl PCM differs from generated PCM")
        if pc_details["pcm_sha256"] != native_hash:
            raise SyntheticEAError("PC-version EA SCHl PCM differs from generated PCM")
        comparison = compare_wavs(ps2_wav, pc_wav)
        if not comparison["exact_pcm_match"]:
            raise SyntheticEAError("PS2/PC version headers produced different decoded PCM")
        return {
            "format": "NFS_AUDIO_V26_EA_SCHL_SYNTHETIC",
            "original_source": "generated uncompressed PCM16LE",
            "sample_rate_hz": RATE,
            "sample_frames": FRAMES,
            "pcm_sha256": native_hash,
            "ps2_platform": PLATFORM_PS2,
            "ps2_header_version": 3,
            "pc_platform": PLATFORM_PC,
            "pc_header_version": 2,
            "ea_codec2": CODEC2_S16LE_INT,
            "ps2_header_bytes": block_report["original"]["header_size"],
            "pc_header_bytes": block_report["experimental"]["header_size"],
            "block_count": block_report["original"]["audio_block_count"],
            "blocks_identical": True,
            "ps2_decoder_metadata": ps2_metadata,
            "pc_decoder_metadata": pc_metadata,
            "real_vgmstream_pcm_identical": True,
            "real_ea_schl_parser_tested": True,
            "real_ea_mt10_tested": False,
            "carbon_runtime_tested": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", default="vgmstream-cli")
    args = parser.parse_args(argv)
    try:
        decoder = Path(resolve_decoder(args.decoder))
        print(json.dumps(run_test(decoder), indent=2, sort_keys=True))
        return 0
    except (SyntheticEAError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("V26 synthetic EA SCHl failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
