#!/usr/bin/env python3
"""V27: independently constructed *synthetic* EA-MT10 silence decoder test.

Builds a silence frame with the public EA-MT10/UTK bitstream grammar described
in vgmstream src/coding/libs/utkdec.c, not any copyrighted game sample.

PS2 platform 5/version 3 and PC platform 0/version 2 containers share exactly
the same compressed audio blocks. Uses real upstream vgmstream-cli to decode
both, verifies their PCM hashes and checks 432 zero-valued frames.

This tests vgmstream, NOT the proprietary Carbon PC game audio runtime, and
does not create a general-purpose MT10 encoder or playable game asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import compare_wavs, inspect_pcm16_wav
from ea_schl_platform_pcm_selftest_v26 import ea_chunk, patch
from schl_wrapper_audit_v25 import compare as compare_schl
from vgmstream_metadata_preflight_v23 import get_metadata, resolve_decoder

SAMPLES = 432
RATE = 22050
EA_MT10 = 4


class SyntheticMT10Error(Exception):
    pass


class BitsLSB:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def put(self, value: int, width: int) -> None:
        if not 0 <= value < (1 << width):
            raise ValueError("Bitfield value out of range")
        for i in range(width):
            self.bits.append((value >> i) & 1)

    def finish(self) -> bytes:
        return bytes(
            sum(self.bits[j + i] << i for i in range(min(8, len(self.bits) - j)))
            for j in range(0, len(self.bits), 8)
        )


def compressed_silence_frame(pulse: bool = False) -> bytes:
    """Generate one valid MT10/UTK EA-PCM frame that decodes to 432 zeros.

    In vgmstream's UTK_EA_PCM variant, one leading byte selects optional raw
    PCM overlays; 0x00 means none. Remaining bits use LSB-first ordering.
    Reflection coefficients map to index 32 (0.0), and RELP zero excitation
    keeps all synthesized samples at zero. No actual game audio is used.
    """
    writer = BitsLSB()
    writer.put(1, 1)     # reduced bandwidth: MT10 mode
    writer.put(15, 4)    # base threshold => 17; first rc index 32 uses RELP
    writer.put(0, 4)     # base gain
    writer.put(0, 6)     # gain multiplier
    for _ in range(4):
        writer.put(32, 6)   # rc table index 32 = 0.0
    for _ in range(8):
        writer.put(16, 5)   # rc table index 16+16 = 32 = 0.0
    for subframe in range(4):
        writer.put(0, 8)    # pitch lag
        writer.put(0, 4)    # pitch gain zero
        writer.put(0, 6)    # fixed gain index
        writer.put(0, 1)    # residual alignment
        writer.put(1, 1)    # no interpolation; other half stays zero
        for excitation in range(54):
            if pulse and subframe == 0 and excitation == 0:
                writer.put(3, 2)  # RELP Huffman +2 pulse (LSB pattern 11)
            else:
                writer.put(0, 1)  # RELP Huffman zero excitation
    return b"\x00" + writer.finish()  # no raw PCM override


def make_mt10_header(platform: int, version: int) -> bytes:
    if (platform, version) not in ((5, 3), (0, 2)):
        raise ValueError("Expected PS2 v3 or PC v2 fixture")
    raw = bytearray(b"PT" + struct.pack("<H", platform))
    raw += patch(0x80, version)
    raw += patch(0x82, 1)
    raw += patch(0x84, RATE)
    raw += patch(0x85, SAMPLES)
    raw += patch(0xA0, EA_MT10)
    if platform == 5:
        raw += patch(0x06, 101)  # harmless extra patch (different header length)
    raw += b"\xFF"
    raw += b"\x00" * (-len(raw) % 4)
    return ea_chunk(b"SCHl", raw)


def make_mt10_audio_chunks(pulse: bool = False) -> bytes:
    """Follow vgmstream blocked_ea_schl.c channel offset and flag layout."""
    frame = compressed_silence_frame(pulse=pulse)
    # One SCDl: 432 frame sample count, ch1 relative offset = 0,
    # flag byte 0x01 means compressed data begins, followed by MT10 frame.
    return (
        ea_chunk(b"SCCl", struct.pack("<I", 1)) +
        ea_chunk(b"SCDl", struct.pack("<II", SAMPLES, 0) + b"\x01" + frame) +
        ea_chunk(b"SCEl")
    )


def build_pair(pulse: bool = False) -> tuple[bytes, bytes]:
    body = make_mt10_audio_chunks(pulse=pulse)
    return make_mt10_header(5, 3) + body, make_mt10_header(0, 2) + body


def decode_one(decoder: Path, source: Path, output: Path) -> None:
    result = subprocess.run(
        [str(decoder), "-i", "-o", str(output), str(source)],
        capture_output=True, timeout=40,
    )
    if result.returncode or not output.is_file():
        message = (result.stderr + result.stdout)[-1200:].decode("utf-8", "replace")
        raise SyntheticMT10Error(f"vgmstream MT10 decode failed: {message}")


def run_test(decoder: Path, pulse: bool = False) -> dict:
    ps2_data, pc_data = build_pair(pulse=pulse)
    with tempfile.TemporaryDirectory(prefix="nfs_v27_synthetic_mt10_") as temp:
        root = Path(temp)
        a = root / "ps2_mt10.asf"
        b = root / "pc_mt10.asf"
        a.write_bytes(ps2_data)
        b.write_bytes(pc_data)
        structural = compare_schl(a, b)
        if not structural["structurally_lossless_wrapper"]:
            raise SyntheticMT10Error("Compressed MT10 blocks differ unexpectedly")
        meta_a = get_metadata(decoder, a, 30)
        meta_b = get_metadata(decoder, b, 30)
        for item in (meta_a, meta_b):
            if item["sample_rate_hz"] != RATE or item["total_samples"] != SAMPLES:
                raise SyntheticMT10Error(f"Unexpected sample metadata {item}")
            if item["channels"] != 1:
                raise SyntheticMT10Error("Expected mono for synthetic MT10 frame")
            if not any(label in item["encoding"].lower() for label in ("microtalk", "mt10", "ea mt")):
                raise SyntheticMT10Error(f"Not recognized as EA-MT: {item['encoding']}")
        awav = root / "ps2.wav"
        bwav = root / "pc.wav"
        decode_one(decoder, a, awav)
        decode_one(decoder, b, bwav)
        details_a = inspect_pcm16_wav(awav)
        details_b = inspect_pcm16_wav(bwav)
        exact = compare_wavs(awav, bwav)
        if not exact["exact_pcm_match"]:
            raise SyntheticMT10Error("PCM mismatch between PS2 and PC MT10 wrappers")
        expected = hashlib.sha256(b"\x00\x00" * SAMPLES).hexdigest()
        if pulse:
            if details_a["pcm_sha256"] == expected or details_b["pcm_sha256"] == expected:
                raise SyntheticMT10Error("Encoded pulse did not produce a nonzero PCM signal")
        elif details_a["pcm_sha256"] != expected or details_b["pcm_sha256"] != expected:
            raise SyntheticMT10Error("Synthetic silence did not decode to exact zero PCM")
        return {
            "format": "NFS_AUDIO_V27_SYNTHETIC_EA_MT10_DECODING",
            "source": "original synthetically constructed MT10 bitstream, NOT game audio",
            "codec2": EA_MT10,
            "compressed_frame_bytes": len(compressed_silence_frame(pulse=pulse)),
            "compressed_test_variant": "relp_pulse" if pulse else "silence",
            "ps2_schl_bytes": len(ps2_data),
            "pc_schl_bytes": len(pc_data),
            "audio_samples": SAMPLES,
            "sample_rate_hz": RATE,
            "ps2_metadata": meta_a,
            "pc_metadata": meta_b,
            "pcm_sha256": details_a["pcm_sha256"],
            "pcm_is_exact_silence": not pulse,
            "nonzero_signal_verified": bool(pulse),
            "pc_and_ps2_pcm_identical": True,
            "real_vgmstream_ea_mt_decoder_invoked": True,
            "real_undercover_recording_decoded": False,
            "carbon_pc_runtime_tested": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", default="vgmstream-cli")
    parser.add_argument("--pulse", action="store_true", help="Generate a nonzero synthetic RELP pulse instead of silence")
    args = parser.parse_args(argv)
    try:
        decoder = Path(resolve_decoder(args.decoder))
        print(json.dumps(run_test(decoder, pulse=args.pulse), sort_keys=True, indent=2))
        return 0
    except (SyntheticMT10Error, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("V27 synthetic MT10 decoder test failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
