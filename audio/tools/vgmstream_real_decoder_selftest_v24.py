#!/usr/bin/env python3
"""V24: deterministic *real vgmstream CLI* self-test using synthetic PCM16LE.

This is a non-game audio decoder integration test based on vgmstream's TXTH
format; it does NOT exercise EA-MT10 or prove game compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import AudioCheckError, inspect_pcm16_wav
from vgmstream_metadata_preflight_v23 import (
    ProbeError, get_metadata, resolve_decoder,
)

FRAMES = 4096
RATE = 22050
TXTH = (
    "codec = PCM16LE\n"
    "channels = 1\n"
    f"sample_rate = {RATE}\n"
    f"num_samples = {FRAMES}\n"
    "start_offset = 0\n"
)


def raw_samples(changed: bool = False) -> bytes:
    """Own-generated test tone: deterministic samples, no game recordings."""
    output = bytearray()
    for n in range(FRAMES):
        value = int(11000 * math.sin(2 * math.pi * (280 * n / RATE)))
        if changed and n == FRAMES // 2:
            value ^= 1
        output += value.to_bytes(2, "little", signed=True)
    return bytes(output)


def decode(decoder: Path, original: Path, output: Path) -> None:
    cmd = [str(decoder), "-i", "-o", str(output), str(original)]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0 or not output.is_file():
        errors = (result.stdout + result.stderr)[-1800:].decode(
            "utf-8", errors="replace"
        )
        raise ProbeError(f"Real vgmstream decode failed: {errors}")


def selftest(decoder: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="nfs_v24_generated_pcm_") as directory:
        home = Path(directory)
        descriptor = home / ".pcm.txth"
        descriptor.write_text(TXTH, encoding="utf-8")
        normal = home / "original.pcm"
        altered = home / "one_bit_changed.pcm"
        normal_data = raw_samples()
        altered_data = raw_samples(changed=True)
        normal.write_bytes(normal_data)
        altered.write_bytes(altered_data)
        original_wav = home / "original.wav"
        altered_wav = home / "altered.wav"
        original_metadata = get_metadata(decoder, normal, timeout=30)
        changed_metadata = get_metadata(decoder, altered, timeout=30)
        for meta in (original_metadata, changed_metadata):
            if meta["channels"] != 1:
                raise ProbeError(f"Unexpected channels: {meta}")
            if meta["sample_rate_hz"] != RATE:
                raise ProbeError(f"Unexpected sample rate: {meta}")
            if meta["total_samples"] != FRAMES:
                raise ProbeError(f"Unexpected sample count: {meta}")
        decode(decoder, normal, original_wav)
        decode(decoder, altered, altered_wav)
        original_result = inspect_pcm16_wav(original_wav)
        changed_result = inspect_pcm16_wav(altered_wav)
        native_sha = hashlib.sha256(normal_data).hexdigest()
        altered_sha = hashlib.sha256(altered_data).hexdigest()
        if original_result["pcm_sha256"] != native_sha:
            raise ProbeError("vgmstream WAV PCM is not byte-identical to generated original")
        if changed_result["pcm_sha256"] != altered_sha:
            raise ProbeError("vgmstream WAV PCM is not byte-identical to generated changed PCM")
        if original_result["pcm_sha256"] == changed_result["pcm_sha256"]:
            raise ProbeError("Decoder did not preserve the intentional one-bit difference")
        return {
            "format": "NFS_AUDIO_V24_VGMSTREAM_SYNTHETIC_INTEGRATION",
            "source_data": "deterministically generated PCM16LE; not game audio",
            "input": {"codec": "PCM16LE", "channels": 1,
                      "sample_rate_hz": RATE, "frames": FRAMES},
            "decoder_metadata_original": original_metadata,
            "decoder_metadata_changed": changed_metadata,
            "original_pcm_sha256": native_sha,
            "altered_pcm_sha256": altered_sha,
            "pcm_roundtrip_identical": True,
            "single_bit_mutation_detected": True,
            "actual_ea_mt10_decoded": False,
            "carbon_pc_runtime_tested": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", default="vgmstream-cli")
    args = parser.parse_args(argv)
    try:
        decoder = resolve_decoder(args.decoder)
        print(json.dumps(selftest(decoder), indent=2, sort_keys=True))
        return 0
    except (ProbeError, AudioCheckError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"V24 decoder synthetic integration failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
