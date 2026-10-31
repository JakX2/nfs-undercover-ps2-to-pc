#!/usr/bin/env python3
"""V29: genuine multi-block synthetic EA-MT10 decoder continuity experiment.

Build a PS2/v3 EA SCHl with three independently encoded EA MicroTalk frames
in three separate SCDl blocks (silence, nonzero pulse, silence). The MT10
initialization header exists ONLY in the first frame: the MicroTalk decoder
must preserve its codec state across later block boundaries.

Pass the original PS2 stream through V28's actual private rewrapper and verify
that upstream vgmstream-cli decodes the PS2 and PC/v2 streams to identical PCM.
Also verify that removing the middle pulse changes decoded audio.

All data is originally generated here, not copied from any EA game. This is
a decoder/container integration test, not Carbon PC runtime compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
import wave
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import (
    AudioCheckError, compare_wavs, decode_one, inspect_pcm16_wav,
    resolve_decoder,
)
from ea_mt10_synthetic_silence_v27 import BitsLSB
from ea_schl_platform_pcm_selftest_v26 import ea_chunk, patch
from schl_wrapper_audit_v25 import compare as audit_pair
from undercover_mt10_private_bridge_v28 import convert
from vgmstream_metadata_preflight_v23 import get_metadata

RATE = 22050
FRAME_SAMPLES = 432
FRAME_PATTERN = (False, True, False)  # original; only the middle has a pulse
EA_MT10 = 4


class MultiBlockError(Exception):
    pass


def synth_frame(*, first: bool, pulse: bool) -> bytes:
    """Generate a valid EA_PCM MicroTalk frame, header only in the first."""
    bits = BitsLSB()
    if first:
        bits.put(1, 1)   # reduced-bandwidth MT10
        bits.put(15, 4)  # multipulse cutoff
        bits.put(0, 4)   # base gain
        bits.put(0, 6)   # gain multiplier
    for _ in range(4):
        bits.put(32, 6)  # zero reflection coefficient
    for _ in range(8):
        bits.put(16, 5)  # zero reflection coefficient
    for subframe in range(4):
        bits.put(0, 8)  # pitch lag
        bits.put(0, 4)  # pitch gain
        bits.put(0, 6)  # fixed gain index
        bits.put(0, 1)  # alignment
        bits.put(1, 1)  # zero alternate excitation positions
        for excitation in range(54):
            if pulse and subframe == 0 and excitation == 0:
                bits.put(3, 2)  # +2 RELP excitation
            else:
                bits.put(0, 1)  # zero excitation
    return b"\x00" + bits.finish()  # no optional PCM overlay


def make_ps2_stream(pattern: tuple[bool, ...] = FRAME_PATTERN) -> bytes:
    """Each block has an independent SCDl header, not a new codec header."""
    if not 2 <= len(pattern) <= 8:
        raise MultiBlockError("Synthetic fixture supports 2-8 blocks")
    sample_count = FRAME_SAMPLES * len(pattern)
    raw = bytearray(b"PT\x05\x00")
    for tag, value in (
        (0x80, 3), (0x82, 1), (0x84, RATE),
        (0x85, sample_count), (0xA0, EA_MT10), (0x06, 101),
    ):
        raw += patch(tag, value)
    raw += b"\xFF"
    raw += b"\x00" * (-len(raw) % 4)
    stream = bytearray(ea_chunk(b"SCHl", bytes(raw)))
    stream += ea_chunk(b"SCCl", struct.pack("<I", len(pattern)))
    for i, pulse in enumerate(pattern):
        packet = synth_frame(first=i == 0, pulse=pulse)
        # SCDl: sample count, mono data offset, "data begins" flag, packet
        stream += ea_chunk(
            b"SCDl", struct.pack("<II", FRAME_SAMPLES, 0) + b"\x01" + packet
        )
    stream += ea_chunk(b"SCEl")
    return bytes(stream)


def decode_and_read(decoder: str, source: Path, wav: Path) -> tuple[dict, bytes]:
    decode_one(decoder, source, wav, timeout=40)
    metrics = inspect_pcm16_wav(wav)
    with wave.open(str(wav), "rb") as reader:
        audio = reader.readframes(reader.getnframes())
    return metrics, audio


def real_decoder_test(decoder: str) -> dict:
    binary = resolve_decoder(decoder)
    original = make_ps2_stream()
    experimental, conversion = convert(original)
    mutated = make_ps2_stream((False, False, False))
    sample_count = len(FRAME_PATTERN) * FRAME_SAMPLES

    with tempfile.TemporaryDirectory(prefix="nfs_v29_original_synthetic_mt10_") as tmp:
        directory = Path(tmp)
        ps2 = directory / "original_ps2.asf"
        pc = directory / "experimental_pc.asf"
        control = directory / "negative_control_no_pulse.asf"
        ps2.write_bytes(original)
        pc.write_bytes(experimental)
        control.write_bytes(mutated)

        structural = audit_pair(ps2, pc)
        if not structural["structurally_lossless_wrapper"]:
            raise MultiBlockError("Rewrapping changed original compressed blocks")
        if structural["original"]["audio_block_count"] != len(FRAME_PATTERN):
            raise MultiBlockError("Expected three independently structured SCDl blocks")
        if structural["original"]["total_scdl_samples"] != sample_count:
            raise MultiBlockError("SCDl sample count totals don't match expected frames")
        negative_structural = audit_pair(ps2, control)
        if negative_structural["structurally_lossless_wrapper"]:
            raise MultiBlockError("Structural test didn't detect a changed middle block")

        metadata = {}
        for name, file in (("ps2", ps2), ("pc", pc)):
            info = get_metadata(Path(binary), file, timeout=30)
            if (info["sample_rate_hz"] != RATE or info["channels"] != 1 or
                info["total_samples"] != sample_count or
                "microtalk" not in info["encoding"].lower()):
                raise MultiBlockError(f"Decoder metadata incorrect for {name}: {info}")
            metadata[name] = info

        ps2wav = directory / "ps2.wav"
        pcwav = directory / "pc.wav"
        negwav = directory / "no_pulse.wav"
        a, a_pcm = decode_and_read(binary, ps2, ps2wav)
        b, b_pcm = decode_and_read(binary, pc, pcwav)
        c, c_pcm = decode_and_read(binary, control, negwav)
        if a["pcm_frames"] != sample_count or b["pcm_frames"] != sample_count:
            raise MultiBlockError("Decoded WAV frame count mismatch")
        if a_pcm != b_pcm or not compare_wavs(ps2wav, pcwav)["exact_pcm_match"]:
            raise MultiBlockError("Rewrapped multi-block EA-MT10 decoded PCM differs")
        if a_pcm == c_pcm:
            raise MultiBlockError("Negative-control pulse removal didn't change PCM")
        # Slices correspond exactly to the separate decoded blocks.
        block0 = a_pcm[:FRAME_SAMPLES * 2]
        block1 = a_pcm[FRAME_SAMPLES * 2:FRAME_SAMPLES * 4]
        if any(block0):
            raise MultiBlockError("Original silence block did not decode to silence")
        if not any(block1):
            raise MultiBlockError("Second compressed block's pulse disappeared")
        return {
            "format": "NFS_AUDIO_V29_MULTIBLOCK_EA_MT10",
            "fixture": "original copyright-free generated MicroTalk, not game speech",
            "blocks": len(FRAME_PATTERN),
            "sample_count": sample_count,
            "sample_rate_hz": RATE,
            "ps2_header_bytes": conversion["source_header"]["header_size"],
            "pc_header_bytes": conversion["target_header"]["header_size"],
            "original_compressed_body_sha256": conversion["compressed_body_sha256"],
            "decoder_metadata": metadata,
            "ps2_decoded_pcm_sha256": a["pcm_sha256"],
            "pc_decoded_pcm_sha256": b["pcm_sha256"],
            "negative_control_decoded_pcm_sha256": c["pcm_sha256"],
            "both_platform_pcm_exact_match": True,
            "middle_block_nonzero_verified": True,
            "negative_control_differs": True,
            "real_mt10_multiblock_decoder_checked": True,
            "real_undercover_voice_decoded": False,
            "carbon_pc_runtime_checked": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", default="vgmstream-cli")
    args = parser.parse_args(argv)
    try:
        report = real_decoder_test(args.decoder)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (AudioCheckError, MultiBlockError, OSError, ValueError) as exc:
        print(f"V29 multi-block decoder experiment failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
