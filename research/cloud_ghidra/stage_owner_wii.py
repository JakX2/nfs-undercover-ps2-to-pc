#!/usr/bin/env python3
"""Fetch SHA-pinned owner Wii images privately via an authenticated Drive service.

This script NEVER accepts anonymous links or exposes the source IDs in logs.
Original binaries are restricted to fresh temporary directories on the runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

EXPECTED = {
    "dol": ("NfsMWRelease.dol", 6_433_280,
            "16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4"),
    "elf": ("NfsMWRelease.elf", 11_151_296,
            "fd9681f2b06e961667bcad2eea6aaf6c762e0f30d666376d1ebb5f2946455ab0"),
}
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{12,128}\Z")
MAX_INPUT_BYTES = 32 * 1024 * 1024


class OriginalImageError(ValueError):
    """Unsafe, unavailable or incorrect owner image."""


def stage_images(service, image_ids: dict[str, str], output: Path,
                 expected: dict[str, tuple[str, int, str]] = EXPECTED) -> dict[str, Path]:
    """Stage verified original images; service can be mocked in synthetic tests."""
    if set(image_ids) != set(expected):
        raise OriginalImageError("original input types are incomplete")
    if len(set(image_ids.values())) != len(image_ids):
        raise OriginalImageError("duplicate original file IDs")
    for file_id in image_ids.values():
        if not isinstance(file_id, str) or not ID_PATTERN.fullmatch(file_id):
            raise OriginalImageError("invalid private Drive file ID")
    if output.exists() or output.is_symlink():
        raise OriginalImageError("private output directory must not already exist")
    output.mkdir(parents=True, mode=0o700)
    output.chmod(0o700)
    created: list[Path] = []
    try:
        for label, (name, size, sha) in expected.items():
            if not 0 < size <= MAX_INPUT_BYTES:
                raise OriginalImageError("configured size violates private safety bound")
            file_id = image_ids[label]
            metadata = service.files().get(fileId=file_id, fields="id,size,mimeType",
                                           supportsAllDrives=True).execute(num_retries=3)
            if str(metadata.get("size")) != str(size):
                raise OriginalImageError("private original file size mismatch")
            if str(metadata.get("mimeType", "")).startswith("application/vnd.google-apps."):
                raise OriginalImageError("Google workspace documents are not executable inputs")
            data = service.files().get_media(fileId=file_id,
                                             supportsAllDrives=True).execute(num_retries=3)
            if not isinstance(data, bytes) or len(data) != size:
                raise OriginalImageError("private original payload size mismatch")
            if hashlib.sha256(data).hexdigest() != sha:
                raise OriginalImageError("private original SHA-256 mismatch")
            dest = output / name
            fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(dest)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        return {label: output / expected[label][0] for label in expected}
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        output.rmdir()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new private temporary directory")
    args = parser.parse_args()
    names = ("WII_GDRIVE_SERVICE_ACCOUNT_JSON", "WII_ORIGINAL_DOL_ID", "WII_ORIGINAL_ELF_ID")
    if any(not os.getenv(name) for name in names):
        parser.error("cloud-only private Drive credentials are not configured")
    # Import only at runtime: synthetic CI needs no Google SDK and no credentials.
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    try:
        account = json.loads(os.environ[names[0]])
        credentials = service_account.Credentials.from_service_account_info(
            account, scopes=["https://www.googleapis.com/auth/drive.readonly"])
        service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        stage_images(service, {"dol": os.environ[names[1]], "elf": os.environ[names[2]]}, args.output)
    except OriginalImageError as exc:
        parser.error(str(exc))
    print("PASS: both owner-private Wii files verified and staged on ephemeral cloud storage")


if __name__ == "__main__":
    main()
