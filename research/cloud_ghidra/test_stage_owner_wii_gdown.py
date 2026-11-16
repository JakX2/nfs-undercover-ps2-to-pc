#!/usr/bin/env python3
"""Synthetic, original-free tests for the link-based private Wii staging."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from stage_owner_wii import OriginalImageError
from stage_owner_wii_gdown import stage_links


DOL = b"independently-written-synthetic-ppc-dol"
ELF = b"independently-written-synthetic-ppc-elf"
IDS = {"dol": "syntheticDriveId0001", "elf": "syntheticDriveId0002"}
EXPECTED = {
    "dol": ("mock.dol", len(DOL), hashlib.sha256(DOL).hexdigest()),
    "elf": ("mock.elf", len(ELF), hashlib.sha256(ELF).hexdigest()),
}


class Downloader:
    def __init__(self, dol=DOL, elf=ELF, fail=None):
        self.data = {IDS["dol"]: dol, IDS["elf"]: elf}
        self.fail = fail
        self.calls = []

    def __call__(self, *, id, output, quiet):
        self.calls.append((id, quiet))
        if self.fail == "exception":
            raise OSError("deliberately include sensitive-id-in-provider-error")
        if self.fail == "missing":
            return None
        Path(output).write_bytes(self.data[id])
        return output


class TestLinkStaging(unittest.TestCase):
    def test_two_files_staged_with_verified_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            dl = Downloader()
            files = stage_links(dl, IDS, root, EXPECTED)
            self.assertEqual(files["dol"].read_bytes(), DOL)
            self.assertEqual(files["elf"].read_bytes(), ELF)
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            self.assertEqual(files["dol"].stat().st_mode & 0o777, 0o600)
            self.assertTrue(all(quiet for _, quiet in dl.calls))

    def test_bad_content_refused_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "SHA-256"):
                stage_links(Downloader(elf=ELF[::-1]), IDS, root, EXPECTED)
            self.assertFalse(root.exists())

    def test_size_mismatch_refused_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "size mismatch"):
                stage_links(Downloader(dol=b"tiny"), IDS, root, EXPECTED)
            self.assertFalse(root.exists())

    def test_missing_download_refused_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "unavailable"):
                stage_links(Downloader(fail="missing"), IDS, root, EXPECTED)
            self.assertFalse(root.exists())

    def test_exception_strips_private_provider_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            with self.assertRaises(OriginalImageError) as cm:
                stage_links(Downloader(fail="exception"), IDS, root, EXPECTED)
            self.assertNotIn("sensitive-id", str(cm.exception))
            self.assertFalse(root.exists())

    def test_refuses_existing_output_without_modifying(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir()
            sentinel = root / "sentinel"
            sentinel.write_text("don't erase")
            with self.assertRaisesRegex(OriginalImageError, "overwrite"):
                stage_links(Downloader(), IDS, root, EXPECTED)
            self.assertEqual(sentinel.read_text(), "don't erase")

    def test_no_duplicate_or_malformed_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            for ids in (
                {"dol": IDS["dol"]},
                {"dol": IDS["dol"], "elf": IDS["dol"]},
                {"dol": "../unsafe", "elf": IDS["elf"]},
            ):
                with self.assertRaises(OriginalImageError):
                    stage_links(Downloader(), ids, root, EXPECTED)
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
