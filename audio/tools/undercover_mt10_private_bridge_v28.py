#!/usr/bin/env python3
"""V28: one-command PRIVATE PS2-MT10 to PC-style SCHl wrapper experiment.

Accepts one individually extracted Undercover PS2 SCHl *mono* stream.
Reads its EA variable header, builds a minimal PC platform=0/version=2 header,
preserves every original byte after the SCHl header, then optionally checks
exact PCM with a locally installed, independent vgmstream-cli.

Default result: metadata-only JSON in a NEW output folder; temporary converted
SCHl/WAV deleted. --keep-pc-shape retains a proprietary ASF locally only.
No Carbon runtime loading, 24 kHz resampling, transcoding, or gameplay patch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from ea_mt10_pcm_equivalence_v22 import (
    AudioCheckError, compare_wavs, decode_one, resolve_decoder, sha256_file,
)
from schl_wrapper_audit_v25 import SCHlAuditError, compare, parse_stream

# Strictly recognize ordinary numeric EA variable-header patch tags.
# Based on vgmstream src/meta/ea_schl.c, parse_variable_header.
PATCH_VALUES = {
    0x00,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,
    0x0E,0x0F,0x10,0x11,0x12,0x13,0x14,0x15,0x19,0x1B,0x1C,0x1D,
    0x1E,0x1F,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,
    0x2A,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8A,
    0x8B,0x8C,0x8D,0x8E,0x8F,0x90,0x91,0x92,0x93,0x94,0x95,0x98,
    0x99,0x9C,0x9D,0x9E,0x9F,0xA0,0xA1,0xA2,0xA3,0xA6,0xA7,0xAB,
    0xAC,0xAD
}
MARKERS = {0xFC, 0xFD}
IMPLICIT_PS2_RATE = 22050
MT10_CODEC2 = 4
MAX_SOURCE_BYTES = 64 * 1024 * 1024


class BridgeError(Exception):
    """Invalid or unsupported source for *this* experimental bridge."""


def ea_patch(tag: int, value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise BridgeError("EA patch numeric value outside uint32")
    count = max(1, (value.bit_length() + 7) // 8)
    return bytes((tag, count)) + value.to_bytes(count, "big")


def parse_header(raw: bytes) -> dict:
    """Read normal PT5-v3 variable patch headers, rejecting ambiguous profiles."""
    if raw[:4] != b"SCHl" or len(raw) < 24:
        raise BridgeError("Expected an individual little-endian SCHl stream")
    size = struct.unpack_from("<I", raw, 4)[0]
    if not 12 <= size <= len(raw) or raw[8:10] != b"PT":
        raise BridgeError("Unexpected SCHl header/EA platform marker")
    platform = struct.unpack_from("<H", raw, 10)[0]
    patches: dict[int, int] = {}
    p = 12
    ended = False
    while p < size:
        tag = raw[p]
        p += 1
        if tag == 0xFF:
            ended = True
            break
        if tag in MARKERS:
            continue
        if tag not in PATCH_VALUES:
            raise BridgeError(f"Unsupported EA patch 0x{tag:02X}")
        if p >= size:
            raise BridgeError("Truncated EA patch size")
        width = raw[p]
        p += 1
        if width > 4:
            # Nested or >32-bit opaque patches cannot be safely reconstructed.
            raise BridgeError("Opaque EA variable patch unsupported")
        if p + width > size:
            raise BridgeError("Truncated EA patch value")
        value = int.from_bytes(raw[p:p+width], "big")
        p += width
        if tag in (0x80,0x82,0x84,0x85,0xA0) and tag in patches:
            raise BridgeError("Duplicate essential EA header patch")
        patches[tag] = value
    if not ended or any(raw[p:size]):
        raise BridgeError("Missing EA terminator or nonzero header padding")
    return {"platform":platform, "version":patches.get(0x80),
            "codec2":patches.get(0xA0), "channels":patches.get(0x82, 1),
            "rate":patches.get(0x84, IMPLICIT_PS2_RATE),
            "sample_count":patches.get(0x85),
            "header_size":size}


def validate_source(raw: bytes) -> tuple[dict,dict]:
    header = parse_header(raw)
    if header["platform"] != 5 or header["version"] != 3:
        raise BridgeError("Expected an original PS2 platform 5, header version 3")
    if header["codec2"] != MT10_CODEC2:
        raise BridgeError("Requires EA MicroTalk codec2=4 (MT10), not PCM")
    if header["channels"] != 1:
        raise BridgeError("V28 only supports mono; stereo block semantics need separate tests")
    if not 8000 <= header["rate"] <= 96000:
        raise BridgeError("Unreasonable source sample rate")
    if not isinstance(header["sample_count"],int) or header["sample_count"] < 1:
        raise BridgeError("Missing positive source sample count")
    structure = parse_stream(raw)
    if structure["total_scdl_samples"] != header["sample_count"]:
        raise BridgeError("EA sample count does not equal sum of SCDl sample counts")
    return header, structure


def convert(raw: bytes) -> tuple[bytes,dict]:
    """Keep original compressed audio blocks byte-for-byte; change header only."""
    source, original_structure = validate_source(raw)
    fields = bytearray(b"PT\x00\x00")
    for tag, value in (
        (0x80,2), (0x82,source["channels"]), (0x84,source["rate"]),
        (0x85,source["sample_count"]), (0xA0,MT10_CODEC2),
        (0x05,80), (0x06,101)
    ):
        fields += ea_patch(tag,value)
    fields += b"\xFF"
    fields += b"\x00" * (-len(fields) % 4)
    header = b"SCHl" + struct.pack("<I",len(fields)+8) + bytes(fields)
    result = header + raw[source["header_size"]:]
    result_structure = parse_stream(result)
    if result_structure["post_header_sha256"] != original_structure["post_header_sha256"]:
        raise BridgeError("Rewrap unexpectedly changed original audio body")
    if result_structure["total_scdl_samples"] != source["sample_count"]:
        raise BridgeError("PC-shaped output has inconsistent sample count")
    target = parse_header(result)
    if (target["platform"], target["version"], target["codec2"],
        target["rate"], target["channels"], target["sample_count"]) != (
        0, 2, 4, source["rate"], 1, source["sample_count"]
    ):
        raise BridgeError("New PC-style header did not parse correctly")
    return result, {"source_header":source, "target_header":target,
                    "compressed_body_sha256":original_structure["post_header_sha256"],
                    "scdl_blocks":original_structure["audio_block_count"]}


def run_pair(original: Path, decoder: str | None = None,
             *, retain: Path | None = None, timeout: int = 120) -> dict:
    if not original.is_file() or original.stat().st_size > MAX_SOURCE_BYTES:
        raise BridgeError("Source is missing or exceeds 64 MiB")
    raw = original.read_bytes()
    converted, details = convert(raw)
    report = {
        "format":"NFS_AUDIO_V28_PRIVATE_MONO_MT10_REWRAP",
        "research_only":True,
        "source_bytes":len(raw),
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "converted_bytes":len(converted),
        "converted_sha256":hashlib.sha256(converted).hexdigest(),
        **details,
        "body_byte_identical":True,
        "real_decoder_executed":False,
        "real_undercover_confirmed":False,
        "carbon_pc_runtime_verified":False,
        "pcm_equivalent":None,
    }
    with tempfile.TemporaryDirectory(prefix="nfs_audio_v28_private_") as folder:
        other = Path(folder) / "pc_style.asf"
        other.write_bytes(converted)
        structure = compare(original, other)
        if not structure["structurally_lossless_wrapper"]:
            raise BridgeError("Independent V25 block auditor rejected wrapper")
        if decoder is not None:
            if timeout <= 0:
                raise BridgeError("Timeout must be positive")
            executable = resolve_decoder(decoder)
            wav_a = Path(folder) / "ps2.wav"
            wav_b = Path(folder) / "pc.wav"
            decode_one(executable, original, wav_a, timeout)
            decode_one(executable, other, wav_b, timeout)
            cmp = compare_wavs(wav_a, wav_b)
            report["decoder_sha256"] = sha256_file(Path(executable))
            report["real_decoder_executed"] = True
            report["decoded_pcm"] = cmp
            report["pcm_equivalent"] = cmp["exact_pcm_match"]
        if retain is not None:
            # Caller must supply a new, outside-the-repository private file path.
            with retain.open("xb") as fh:
                fh.write(converted)
            report["pc_shape_retained_locally"] = True
        else:
            report["pc_shape_retained_locally"] = False
    return report


def self_test(decoder: str) -> dict:
    """Run our new conversion code against BOTH genuine synthetic MT10 cases."""
    from ea_mt10_synthetic_silence_v27 import build_pair
    outputs = []
    for pulse in (False,True):
        source, _unused_reference = build_pair(pulse=pulse)
        with tempfile.TemporaryDirectory(prefix="nfs_audio_v28_ci_") as folder:
            file = Path(folder) / "source.asf"
            file.write_bytes(source)
            report = run_pair(file, decoder)
            if report["pcm_equivalent"] is not True:
                raise BridgeError("V28 synthetic MT10 PCM differed after new rewrap")
            outputs.append({"type":"pulse" if pulse else "silence",
                            "decoded_pcm_sha256":report["decoded_pcm"]["original"]["pcm_sha256"],
                            "scdl_blocks":report["scdl_blocks"],
                            "equal":True})
    return {"format":"NFS_AUDIO_V28_REAL_DECODER_SYNTHETIC_GATE",
            "all_synthetic_pcm_checks_passed":True,
            "experiments":outputs,"real_undercover_recording_tested":False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original",type=Path,help="Privately extracted original PS2 mono SCHl")
    p.add_argument("--decoder",help="vgmstream-cli executable path; required for PCM verification")
    p.add_argument("--out-dir",type=Path,help="NEW private directory for JSON report only")
    p.add_argument("--keep-pc-shape",action="store_true",
                   help="Opt-in: retain experimental proprietary PC-shaped ASF locally")
    p.add_argument("--self-test",action="store_true",
                   help="Use two original synthetic MT10 fixtures, no copyrighted audio")
    p.add_argument("--timeout",type=int,default=120)
    args=p.parse_args(argv)
    try:
        if args.self_test:
            if not args.decoder:
                raise BridgeError("--self-test requires --decoder")
            print(json.dumps(self_test(args.decoder),indent=2,sort_keys=True))
            return 0
        if not args.original or not args.out_dir:
            raise BridgeError("--original and --out-dir required for private conversion")
        if args.out_dir.exists():
            raise BridgeError("Output folder exists: refusing to overwrite")
        if args.original.resolve() == args.out_dir.resolve():
            raise BridgeError("Input and output directory cannot be identical")
        # Out folder is reserved before writing private output or running decoder.
        args.out_dir.mkdir(parents=True,exist_ok=False)
        retained = args.out_dir / "experimental_pc_style.asf" if args.keep_pc_shape else None
        report=run_pair(args.original,args.decoder,retain=retained,timeout=args.timeout)
        (args.out_dir/"report.json").open("x",encoding="utf-8").write(
            json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0 if report["pcm_equivalent"] is not False else 1
    except (BridgeError,SCHlAuditError,AudioCheckError,OSError) as exc:
        print(f"V28 failed: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
