#!/usr/bin/env python3
"""Offline EA-MT10 decoder equivalence check for the NFS audio research project.

Compares decoded 16-bit PCM from a native Undercover SCHl stream and an
experimental PC-style SCHl wrapper. Requires an independent vgmstream-cli binary.
No game files are distributed, modified in place, or installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

CHUNK_BYTES = 1024 * 1024


class AudioCheckError(Exception):
    """Invalid input, unsupported WAV, or external decoder failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pcm16_wav(path: Path) -> dict[str, Any]:
    """Hash decoded PCM, not the surrounding WAV/RIFF header."""
    if not path.is_file():
        raise AudioCheckError(f"Missing WAV: {path}")
    digest = hashlib.sha256()
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getcomptype() != "NONE":
                raise AudioCheckError(f"WAV must be uncompressed PCM: {path}")
            channels = wav.getnchannels()
            rate = wav.getframerate()
            width = wav.getsampwidth()
            frames = wav.getnframes()
            if width != 2:
                raise AudioCheckError(
                    f"Expected vgmstream's default 16-bit PCM; got {width * 8}-bit: {path}"
                )
            if channels not in (1, 2) or rate <= 0 or frames <= 0:
                raise AudioCheckError(f"Unsupported or empty WAV format: {path}")
            total_bytes = 0
            while True:
                pcm = wav.readframes(32768)
                if not pcm:
                    break
                digest.update(pcm)
                total_bytes += len(pcm)
    except (EOFError, wave.Error, OSError) as exc:
        raise AudioCheckError(f"Can't inspect WAV {path}: {exc}") from exc
    expected_bytes = frames * channels * width
    if total_bytes != expected_bytes:
        raise AudioCheckError(
            f"Truncated PCM in {path}: {total_bytes} vs {expected_bytes} expected bytes"
        )
    return {
        "channels": channels,
        "sample_rate_hz": rate,
        "sample_width_bits": width * 8,
        "pcm_frames": frames,
        "duration_seconds": frames / rate,
        "pcm_sha256": digest.hexdigest(),
        "pcm_bytes": total_bytes,
    }


def compare_wavs(original: Path, experimental: Path) -> dict[str, Any]:
    left = inspect_pcm16_wav(original)
    right = inspect_pcm16_wav(experimental)
    fields = ("channels", "sample_rate_hz", "sample_width_bits", "pcm_frames")
    metadata_matches = all(left[k] == right[k] for k in fields)
    pcm_hash_matches = left["pcm_sha256"] == right["pcm_sha256"]
    return {
        "format": "NFS_AUDIO_V22_PCM_COMPARISON",
        "original": left,
        "experimental": right,
        "metadata_matches": metadata_matches,
        "pcm_hash_matches": pcm_hash_matches,
        "exact_pcm_match": metadata_matches and pcm_hash_matches,
    }


def assert_schl(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AudioCheckError(f"Missing source recording: {path}")
    with path.open("rb") as source:
        magic = source.read(4)
    if magic != b"SCHl":
        raise AudioCheckError(
            f"Expected an individual little-endian EA SCHl stream: {path}"
        )
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def resolve_decoder(binary: str) -> str:
    found = shutil.which(binary)
    if found is None:
        candidate = Path(binary)
        if candidate.is_file():
            found = str(candidate.resolve())
    if found is None:
        raise AudioCheckError(
            "vgmstream-cli not found. Install the official CLI and provide --decoder "
            "with its executable path; FFmpeg is not an EA-MT10 substitute."
        )
    return found


def decode_one(decoder: str, recording: Path, target: Path, timeout: int) -> None:
    if target.exists():
        raise AudioCheckError(f"Refusing to overwrite: {target}")
    command = [decoder, "-i", "-o", str(target), str(recording.resolve())]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AudioCheckError(f"Decoder did not complete: {exc}") from exc
    if result.returncode != 0 or not target.is_file():
        details = (result.stderr or result.stdout or "").strip()[-1500:]
        raise AudioCheckError(
            f"Decoder failed (exit {result.returncode}) for {recording.name}: {details}"
        )


def save_new_report(path: Path, data: dict[str, Any]) -> None:
    if path.exists():
        raise AudioCheckError(f"Refusing to overwrite existing report: {path}")
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_wav_command(args: argparse.Namespace) -> int:
    result = compare_wavs(args.original, args.experimental)
    if args.report is not None:
        save_new_report(args.report, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["exact_pcm_match"] else 1


def decode_pair_command(args: argparse.Namespace) -> int:
    if args.original.resolve() == args.experimental.resolve():
        raise AudioCheckError("Original and experimental paths cannot be identical")
    source_info = {
        "original": assert_schl(args.original),
        "experimental": assert_schl(args.experimental),
    }
    decoder = resolve_decoder(args.decoder)
    output = args.out_dir.resolve()
    if output.exists():
        raise AudioCheckError(f"Output directory already exists: {output}")
    if args.timeout <= 0:
        raise AudioCheckError("--timeout must be positive")
    output.mkdir(parents=True, exist_ok=False)
    a_wav = output / "original_decoded.wav"
    b_wav = output / "experimental_decoded.wav"
    report: dict[str, Any] = {
        "format": "NFS_AUDIO_V22_DECODER_VALIDATION",
        "research_only": True,
        "source_streams": source_info,
        "decoder_path": decoder,
        "decoder_sha256": sha256_file(Path(decoder)),
        "wav_retained": bool(args.keep_wavs),
    }
    try:
        decode_one(decoder, args.original, a_wav, args.timeout)
        decode_one(decoder, args.experimental, b_wav, args.timeout)
        report["comparison"] = compare_wavs(a_wav, b_wav)
    except AudioCheckError as exc:
        report["error"] = str(exc)
        save_new_report(output / "report.json", report)
        raise
    finally:
        if not args.keep_wavs:
            a_wav.unlink(missing_ok=True)
            b_wav.unlink(missing_ok=True)
    save_new_report(output / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["comparison"]["exact_pcm_match"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="V22: compare EA-MT10 decoded PCM, without touching the game installation"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    wav = sub.add_parser("compare-wavs", help="Compare two already-decoded 16-bit WAVs")
    wav.add_argument("original", type=Path)
    wav.add_argument("experimental", type=Path)
    wav.add_argument("--report", type=Path, help="Optional new JSON report (never overwrite)")
    wav.set_defaults(action=compare_wav_command)
    dec = sub.add_parser("decode-pair", help="Decode and compare two individual SCHl streams")
    dec.add_argument("--original", required=True, type=Path)
    dec.add_argument("--experimental", required=True, type=Path)
    dec.add_argument("--decoder", default="vgmstream-cli")
    dec.add_argument("--out-dir", required=True, type=Path)
    dec.add_argument("--timeout", type=int, default=180)
    dec.add_argument("--keep-wavs", action="store_true", help="Keep decoded copyrighted audio locally")
    dec.set_defaults(action=decode_pair_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.action(args)
    except AudioCheckError as exc:
        print(f"V22 validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
