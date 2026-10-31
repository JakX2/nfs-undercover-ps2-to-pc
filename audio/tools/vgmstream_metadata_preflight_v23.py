#!/usr/bin/env python3
"""V23: Metadata-only preflight for original and PC-shaped EA SCHl recordings.

Calls an independently installed vgmstream-cli with -m. No audio is decoded,
written, copied, uploaded, or modified. No assertion of Carbon PC compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

MAX_METADATA_BYTES = 128_000


class ProbeError(Exception):
    """Unsafe input or failed decoder metadata probing."""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_schl(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ProbeError(f"Not a file: {path}")
    if path.stat().st_size < 8:
        raise ProbeError(f"Truncated SCHl input: {path}")
    with path.open("rb") as stream:
        if stream.read(4) != b"SCHl":
            raise ProbeError(f"Not a little-endian SCHl stream: {path}")
    return {"bytes": path.stat().st_size, "sha256": file_sha256(path)}


def parse_metadata(output: str) -> dict[str, Any]:
    """Parse stable vgmstream-cli -m labels. Unknown fields are kept out."""
    fields: dict[str, Any] = {}
    labels = {
        "sample rate": "sample_rate_hz",
        "channels": "channels",
        "stream total samples": "total_samples",
        "encoding": "encoding",
        "layout": "layout",
        "metadata from": "metadata_from",
    }
    for line in output.splitlines():
        if ":" not in line:
            continue
        name, raw = line.strip().split(":", 1)
        key = labels.get(name.strip().lower())
        if key is None:
            continue
        value = raw.strip()
        if key in ("sample_rate_hz", "channels", "total_samples"):
            # "stream total samples: 1234 (0:00.05 seconds)" is legal.
            match = re.match(r"^(\d+)(?:\s|$)", value)
            if not match:
                raise ProbeError(f"Invalid vgmstream metadata field: {key}")
            parsed = int(match.group(1))
            if parsed < 1:
                raise ProbeError(f"Invalid nonpositive metadata field: {key}")
            if key == "channels" and parsed > 8:
                raise ProbeError("Unexpected channel count in metadata")
            if key == "sample_rate_hz" and parsed > 384000:
                raise ProbeError("Unexpected sample rate in metadata")
            fields[key] = parsed
        else:
            fields[key] = value[:256]
    for required in ("sample_rate_hz", "channels", "total_samples", "encoding"):
        if required not in fields:
            raise ProbeError(f"Missing required vgmstream metadata: {required}")
    return fields


def resolve_decoder(executable: str) -> Path:
    found = shutil.which(executable)
    if found is None and Path(executable).is_file():
        found = str(Path(executable).resolve())
    if not found:
        raise ProbeError("vgmstream-cli unavailable; install the official CLI")
    path = Path(found).resolve()
    if not path.is_file():
        raise ProbeError("Decoder is not a regular file")
    return path


def get_metadata(decoder: Path, stream: Path, timeout: int) -> dict[str, Any]:
    if timeout <= 0:
        raise ProbeError("Timeout must be positive")
    try:
        process = subprocess.run(
            [str(decoder), "-m", str(stream.resolve())],
            check=False, capture_output=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(f"Unable to probe vgmstream metadata: {type(exc).__name__}") from exc
    if process.returncode != 0:
        raise ProbeError(f"vgmstream -m exited {process.returncode} (no audio written)")
    output = (process.stdout + b"\n" + process.stderr)[:MAX_METADATA_BYTES]
    return parse_metadata(output.decode("utf-8", errors="replace"))


def probe_pair(original: Path, experimental: Path, decoder: Path, timeout: int) -> dict[str, Any]:
    if original.resolve() == experimental.resolve():
        raise ProbeError("Refusing to compare a file with itself")
    left_source = check_schl(original)
    right_source = check_schl(experimental)
    left = get_metadata(decoder, original, timeout)
    right = get_metadata(decoder, experimental, timeout)
    keys = ("channels", "sample_rate_hz", "total_samples", "encoding")
    equal = {key: left[key] == right[key] for key in keys}
    return {
        "format": "NFS_AUDIO_V23_METADATA_PREFLIGHT",
        "research_only": True,
        "decoder_sha256": file_sha256(decoder),
        "original": {"source": left_source, "metadata": left},
        "experimental": {"source": right_source, "metadata": right},
        "field_matches": equal,
        "metadata_match": all(equal.values()),
        "pcm_checked": False,
        "game_playback_checked": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read vgmstream metadata for original + experimental SCHl streams"
    )
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--experimental", required=True, type=Path)
    parser.add_argument("--decoder", default="vgmstream-cli")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--report", type=Path, help="New output JSON; never overwrite")
    args = parser.parse_args(argv)
    try:
        decoder = resolve_decoder(args.decoder)
        if args.report is not None and args.report.exists():
            raise ProbeError("Report already exists; refusing to overwrite")
        result = probe_pair(args.original, args.experimental, decoder, args.timeout)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.report is not None:
            args.report.open("x", encoding="utf-8").write(payload)
        print(payload, end="")
        return 0 if result["metadata_match"] else 1
    except (ProbeError, OSError) as exc:
        print(f"V23 preflight error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
