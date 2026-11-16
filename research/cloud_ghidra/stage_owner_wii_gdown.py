#!/usr/bin/env python3
"""Stage owner Wii files from existing link-readable Google Drive IDs.

Link IDs are read only from GitHub Actions secrets. Verify whole-file SHA-256
and exact size before admitting either downloaded file for native analysis.
No owner binaries, URLs, IDs, or downloads are printed or uploaded.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import os
from pathlib import Path
import shutil

from stage_owner_wii import EXPECTED, ID_PATTERN, MAX_INPUT_BYTES, OriginalImageError


def stage_links(download, ids: dict[str, str], destination: Path,
                expected: dict[str, tuple[str, int, str]] = EXPECTED) -> dict[str, Path]:
    """Stage verified images. Inject downloader for deterministic, original-free tests."""
    if set(ids) != set(expected):
        raise OriginalImageError("missing expected Wii input IDs")
    if len(set(ids.values())) != len(ids):
        raise OriginalImageError("Wii input IDs cannot be duplicated")
    if any(not isinstance(v, str) or not ID_PATTERN.fullmatch(v) for v in ids.values()):
        raise OriginalImageError("malformed Wii input ID")
    if destination.exists() or destination.is_symlink():
        raise OriginalImageError("refusing to overwrite private input directory")
    destination.mkdir(mode=0o700, parents=True)
    destination.chmod(0o700)
    try:
        paths = {}
        for kind, (name, size, sha256) in expected.items():
            if (not 0 < size <= MAX_INPUT_BYTES or Path(name).name != name
                    or not name or "/" in name or "\\" in name):
                raise OriginalImageError("unsafe expected Wii file geometry")
            target = destination / name
            # Suppress provider messages that could print a private Drive ID/link.
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    result = download(id=ids[kind], output=str(target), quiet=True)
            except Exception:
                raise OriginalImageError("Drive download failed; check Viewer link access") from None
            if not result or not target.is_file() or target.is_symlink():
                raise OriginalImageError("Drive download unavailable")
            if target.stat().st_size != size:
                raise OriginalImageError("owner Wii file size mismatch")
            digest = hashlib.sha256()
            with target.open("rb") as src:
                for block in iter(lambda: src.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != sha256:
                raise OriginalImageError("owner Wii SHA-256 mismatch")
            target.chmod(0o600)
            paths[kind] = target
        return paths
    except BaseException:
        # Only files made in a fresh private directory. Never touch a prior run.
        shutil.rmtree(destination)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="new ephemeral private directory")
    args = parser.parse_args()
    names = ("WII_ORIGINAL_DOL_ID", "WII_ORIGINAL_ELF_ID")
    if any(not os.getenv(key) for key in names):
        parser.error("the two Wii Drive IDs must be configured as Actions secrets")
    try:
        import gdown
        stage_links(gdown.download,
                    {"dol": os.environ[names[0]], "elf": os.environ[names[1]]},
                    args.destination)
    except OriginalImageError as exc:
        parser.error(str(exc))
    print("PASS: original Wii DOL and ELF staged and SHA-256 verified privately")


if __name__ == "__main__":
    main()
