#!/usr/bin/env python3
"""V30: decode MULTIPLE generated EA-MT10 frames inside one EA SCDl block.

Unlike V29's one-frame-per-SCDl fixture, V30 places three consecutive MT10
frames in ONE SCDl, then independently decodes it with upstream vgmstream-cli
under PS2/v3 and V28-generated PC/v2 SCHl headers.

The middle frame has a nonzero RELP excitation pulse. An all-silent variant
provides a negative control. Both variants are original generated compressed
data, not Undercover game recordings. Carbon PC runtime remains untested.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import tempfile
from pathlib import Path

from ea_mt10_multiblock_continuity_v29 import (
    FRAME_PATTERN, FRAME_SAMPLES, RATE, MultiBlockError,
    decode_and_read, make_ps2_stream, synth_frame,
)
from ea_mt10_pcm_equivalence_v22 import AudioCheckError, compare_wavs, resolve_decoder
from ea_schl_platform_pcm_selftest_v26 import ea_chunk
from schl_wrapper_audit_v25 import compare as compare_schl, parse_stream
from undercover_mt10_private_bridge_v28 import convert
from vgmstream_metadata_preflight_v23 import get_metadata


def make_single_block_stream(pattern: tuple[bool, ...] = FRAME_PATTERN) -> bytes:
    """Pack 2-8 complete byte-aligned compressed frames into one SCDl chunk."""
    if not 2 <= len(pattern) <= 8:
        raise MultiBlockError("V30 synthetic fixture supports 2-8 MT10 frames")
    # The header is built with V29's independent synthetic EA platform5/v3
    # fixture, but data blocks are built differently in this experiment.
    baseline = make_ps2_stream(pattern)
    header_length = struct.unpack_from("<I", baseline, 4)[0]
    header = baseline[:header_length]
    compressed = b"".join(
        synth_frame(first=(i == 0), pulse=active)
        for i, active in enumerate(pattern)
    )
    sample_count = FRAME_SAMPLES * len(pattern)
    body = (
        ea_chunk(b"SCCl", struct.pack("<I", 1))
        + ea_chunk(
            b"SCDl",
            struct.pack("<II", sample_count, 0) + b"\x01" + compressed
        )
        + ea_chunk(b"SCEl")
    )
    return header + body


def verify_real_decoder(decoder: str) -> dict:
    """Use the ACTUAL external MicroTalk decoder for both wrapped variants."""
    binary = resolve_decoder(decoder)
    original = make_single_block_stream()
    pc_stream, conversion = convert(original)
    all_silent = make_single_block_stream((False, False, False))
    expected_frames = FRAME_SAMPLES * len(FRAME_PATTERN)

    with tempfile.TemporaryDirectory(prefix="nfs_v30_original_synthetic_") as temporary:
        home = Path(temporary)
        source = home / "original_ps2.asf"
        wrapped = home / "experimental_pc.asf"
        control = home / "negative_control.asf"
        separate_blocks = home / "three_separate_scdl.asf"
        source.write_bytes(original)
        wrapped.write_bytes(pc_stream)
        control.write_bytes(all_silent)
        separate_blocks.write_bytes(make_ps2_stream())

        audit = compare_schl(source, wrapped)
        if not audit["structurally_lossless_wrapper"]:
            raise MultiBlockError("V30 compressed bytes changed during PC rewrapping")
        if audit["original"]["audio_block_count"] != 1:
            raise MultiBlockError("Expected exactly one SCDl block for all three frames")
        if audit["original"]["total_scdl_samples"] != expected_frames:
            raise MultiBlockError("Unexpected total samples in single SCDl")
        if compare_schl(source, control)["structurally_lossless_wrapper"]:
            raise MultiBlockError("V30 negative-control compressed bytes did not differ")

        metadata = {}
        for name, file in (("ps2", source), ("pc", wrapped)):
            m = get_metadata(Path(binary), file, timeout=30)
            if (
                m["total_samples"] != expected_frames
                or m["channels"] != 1
                or m["sample_rate_hz"] != RATE
                or "microtalk" not in m["encoding"].lower()
            ):
                raise MultiBlockError(f"Invalid upstream EA-MT10 metadata for {name}: {m}")
            metadata[name] = m

        a_wav = home / "ps2.wav"
        b_wav = home / "pc.wav"
        control_wav = home / "no_pulse.wav"
        three_blocks_wav = home / "three_blocks.wav"
        a, a_pcm = decode_and_read(binary, source, a_wav)
        b, b_pcm = decode_and_read(binary, wrapped, b_wav)
        c, c_pcm = decode_and_read(binary, control, control_wav)
        d, d_pcm = decode_and_read(binary, separate_blocks, three_blocks_wav)
        if a["pcm_frames"] != expected_frames or b["pcm_frames"] != expected_frames:
            raise MultiBlockError("Decoder returned unexpected PCM sample count")
        if a_pcm != b_pcm or not compare_wavs(a_wav, b_wav)["exact_pcm_match"]:
            raise MultiBlockError("PC and PS2 decoded PCM differ for single-block frames")
        if a_pcm != d_pcm or not compare_wavs(a_wav, three_blocks_wav)["exact_pcm_match"]:
            raise MultiBlockError("Same MT10 frames decoded differently as one vs three SCDl blocks")
        if a_pcm == c_pcm:
            raise MultiBlockError("Middle-pulse negative control did not change PCM")
        if any(a_pcm[:FRAME_SAMPLES * 2]):
            raise MultiBlockError("First compressed silence frame produced nonzero PCM")
        if not any(a_pcm[FRAME_SAMPLES * 2:FRAME_SAMPLES * 4]):
            raise MultiBlockError("Nonzero compressed middle frame was lost")

        return {
            "format": "NFS_AUDIO_V30_MULTIFRAME_SINGLE_SCDL",
            "input_provenance": "synthetic MT10 bitstream, no commercial game audio",
            "codec": "Electronic Arts MicroTalk (codec2=4)",
            "frame_count": len(FRAME_PATTERN),
            "scdl_block_count": audit["original"]["audio_block_count"],
            "samples_per_frame": FRAME_SAMPLES,
            "total_decoded_samples": expected_frames,
            "sample_rate_hz": RATE,
            "ps2_header_bytes": conversion["source_header"]["header_size"],
            "pc_header_bytes": conversion["target_header"]["header_size"],
            "preserved_audio_body_sha256": conversion["compressed_body_sha256"],
            "ps2_decoded_pcm_sha256": a["pcm_sha256"],
            "pc_decoded_pcm_sha256": b["pcm_sha256"],
            "negative_control_pcm_sha256": c["pcm_sha256"],
            "three_scdl_reference_pcm_sha256": d["pcm_sha256"],
            "independent_decoder_metadata": metadata,
            "ps2_pc_pcm_exact_match": True,
            "one_block_vs_three_blocks_pcm_exact_match": True,
            "middle_frame_nonzero": True,
            "negative_control_differs": True,
            "actual_undercover_voice_tested": False,
            "carbon_pc_runtime_tested": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoder", default="vgmstream-cli")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_real_decoder(args.decoder), sort_keys=True, indent=2))
        return 0
    except (AudioCheckError, MultiBlockError, OSError, ValueError) as exc:
        print(f"V30 synthetic MT10 multi-frame test failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
