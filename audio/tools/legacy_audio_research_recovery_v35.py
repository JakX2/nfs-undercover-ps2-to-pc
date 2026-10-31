#!/usr/bin/env python3
"""V35: safely recover SOURCE-ONLY research from a private V1-V21 ZIP.

The earlier private V21 archive contains original IDX/EVT/CSI reverse-
engineering research that has NOT been migrated to the V22+ GitHub branch.
This tool locates Python/BMS/text research files without ever executing code,
extracting proprietary sounds, or uploading the archive.

inspect: print bounded JSON manifest (paths, byte sizes, SHA-256, keyword flags).
recover: write only audited source/text files to a NEW private output directory.

The tool does NOT validate authentic Undercover IDX formats or audio playback;
it allows the prior source parsers to be reviewed locally before import.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_ZIP_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 4000
MAX_MEMBER_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 48 * 1024 * 1024
MAX_RATIO = 300
ALLOWED = frozenset({".py", ".bms", ".md", ".rst", ".txt"})
KEYWORDS = ("IDX", "CSI", "EVT", "SCHL", "MICROTALK", "MT10", "SCDL", "SCCl",
            "SPEECH", "GROUP", "POLICE")
FORMAT = "NFS_AUDIO_V35_LEGACY_RESEARCH_SOURCE_RECOVERY"


class RecoveryError(Exception):
    """Invalid research ZIP or unsafe extraction target."""


def safe_path(name: str) -> PurePosixPath:
    if (
        not name or name.startswith("/") or "\\" in name
        or ":" in name or "\x00" in name
        or any(ord(x) < 32 for x in name)
    ):
        raise RecoveryError("Unsafe ZIP member path")
    path = PurePosixPath(name)
    if any(part in ("", ".", "..") for part in name.split("/")):
        raise RecoveryError("ZIP traversal or noncanonical path")
    if path.is_absolute() or len(path.parts) > 20:
        raise RecoveryError("Unsafe ZIP member nesting")
    return path


def has_unsafe_member_type(info: zipfile.ZipInfo) -> bool:
    # UNIX-made ZIPs can contain symlinks and special files. Never follow them.
    mode = (info.external_attr >> 16) & 0xFFFF
    if info.create_system == 3 and mode:
        category = stat.S_IFMT(mode)
        return category not in (0, stat.S_IFREG, stat.S_IFDIR)
    return False


def selected_files(archive: Path) -> tuple[list[dict], dict[str, bytes]]:
    """Validate ALL ZIP member paths, collect only bounded plain research text."""
    if not archive.is_file():
        raise RecoveryError("Research archive not found")
    if archive.stat().st_size > MAX_ZIP_BYTES:
        raise RecoveryError("ZIP archive exceeds source-recovery size limit")
    collected: list[dict] = []
    contents: dict[str, bytes] = {}
    seen: set[str] = set()
    total_bytes = 0
    skipped = 0
    try:
        with zipfile.ZipFile(archive, "r") as z:
            infos = z.infolist()
            if len(infos) > MAX_MEMBERS:
                raise RecoveryError("ZIP exceeds member count limit")
            for member in infos:
                path = safe_path(member.filename.rstrip("/") if member.is_dir()
                                 else member.filename)
                normalized = path.as_posix().casefold()
                if normalized in seen:
                    raise RecoveryError("Duplicate ZIP member path (case-insensitive)")
                seen.add(normalized)
                if has_unsafe_member_type(member):
                    raise RecoveryError("Special file or symlink in archive")
                if member.flag_bits & 0x1:
                    raise RecoveryError("Encrypted member unsupported")
                if member.is_dir():
                    continue
                if member.file_size > MAX_MEMBER_BYTES:
                    if path.suffix.lower() in ALLOWED:
                        raise RecoveryError("Oversized research source member")
                    skipped += 1
                    continue
                if member.file_size and (
                    member.compress_size == 0
                    or member.file_size > MAX_RATIO * max(1, member.compress_size)
                ):
                    raise RecoveryError("ZIP member compression ratio unsafe")
                if path.suffix.lower() not in ALLOWED:
                    skipped += 1
                    continue
                total_bytes += member.file_size
                if total_bytes > MAX_TOTAL_BYTES:
                    raise RecoveryError("Selected research source total too large")
                with z.open(member, "r") as reader:
                    data = reader.read(MAX_MEMBER_BYTES + 1)
                if len(data) != member.file_size:
                    raise RecoveryError("ZIP member length mismatch")
                if b"\x00" in data:
                    skipped += 1  # disguised binary is not source text
                    continue
                try:
                    as_text = data.decode("utf-8-sig")
                except UnicodeError:
                    skipped += 1
                    continue
                upper = as_text.upper()
                matches = [
                    tag for tag in KEYWORDS
                    if re.search(r"(?<![A-Z0-9])" + re.escape(tag.upper()) +
                                 r"(?![A-Z0-9])", upper)
                ]
                collected.append({
                    "path": path.as_posix(),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "topic_flags": sorted(set(matches)),
                })
                contents[path.as_posix()] = data
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as exc:
        raise RecoveryError("Corrupt or unreadable source ZIP") from exc
    return collected, contents


def manifest(archive: Path) -> tuple[dict, dict[str, bytes]]:
    files, contents = selected_files(archive)
    digest = hashlib.sha256()
    with archive.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    flagged = sorted(
        (x for x in files if x["topic_flags"]),
        key=lambda x: (-len(x["topic_flags"]), x["path"].casefold())
    )
    return {
        "format": FORMAT,
        "archive_sha256": digest.hexdigest(),
        "archive_size_bytes": archive.stat().st_size,
        "selected_source_files": len(files),
        "files_with_audio_format_keywords": len(flagged),
        "source_files": files,
        "likely_relevant_source_paths": [x["path"] for x in flagged],
        "no_source_code_executed": True,
        "no_commercial_audio_exported": True,
        "authentic_idx_schema_confirmed": False,
        "original_undercover_voice_decoded": False,
        "carbon_pc_runtime_tested": False,
    }, contents


def recover(archive: Path, new_folder: Path) -> dict:
    if new_folder.exists():
        raise RecoveryError("Output directory already exists; refusing overwrite")
    report, contents = manifest(archive)
    new_folder.mkdir(parents=True, exist_ok=False)
    # Archive member paths were validated before creating any output.
    for rel_name, raw in contents.items():
        target = new_folder / "research_sources" / rel_name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as out:
            out.write(raw)
    with (new_folder / "manifest.json").open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2, sort_keys=True)
        out.write("\n")
    return report


def self_test() -> dict:
    """Proof of source-only recovery, with a generated, game-free ZIP."""
    with tempfile.TemporaryDirectory(prefix="nfs_v35_source_recovery_") as tmp:
        root = Path(tmp)
        source = root / "synthetic_history.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("legacy/v21/idx_parser.py",
                       "# IDX record format, BIG offset\n"
                       "def parse_idx(data):\n    return data[:4]\n")
            z.writestr("legacy/v21/events.md",
                       "CSI and EVT research is not yet verified on game bytes.\n")
            z.writestr("legacy/v21/speech.asf", b"SCHl" + b"\0" * 100)
        inspected, _ = manifest(source)
        target = root / "safe_recovery"
        restored = recover(source, target)
        if (inspected["selected_source_files"] != 2
            or restored["selected_source_files"] != 2
            or (target / "research_sources/legacy/v21/speech.asf").exists()
            or not (target / "research_sources/legacy/v21/idx_parser.py").exists()):
            raise RecoveryError("Synthetic source-only recovery did not pass")
        return {
            "format": "NFS_AUDIO_V35_SOURCE_RECOVERY_SYNTHETIC_SELFTEST",
            "selected_source_files": 2,
            "audio_files_excluded": True,
            "private_zip_executed": False,
            "real_v21_zip_inspected": False,
            "original_game_audio_used": False,
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    for name in ("inspect", "recover"):
        command = sub.add_parser(name)
        command.add_argument("--archive", type=Path, required=True)
        if name == "recover":
            command.add_argument("--out-dir", type=Path, required=True)
    sub.add_parser("self-test")
    args = p.parse_args(argv)
    try:
        if args.action == "self-test":
            result = self_test()
        elif args.action == "inspect":
            result, _ = manifest(args.archive)
        else:
            result = recover(args.archive, args.out_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (RecoveryError, OSError, ValueError) as exc:
        print(f"V35 research source recovery: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
