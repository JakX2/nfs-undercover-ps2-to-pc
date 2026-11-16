#!/usr/bin/env python3
"""Original-free staging regressions; all image payloads are fake synthetic bytes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from stage_owner_wii import OriginalImageError, stage_images

FIRST_ID = "syntheticDriveId0001"
SECOND_ID = "syntheticDriveId0002"
INPUTS = {"dol": FIRST_ID, "elf": SECOND_ID}
FILES = {FIRST_ID: b"fake-independently-written-DOL", SECOND_ID: b"fake-independently-written-ELF"}
EXPECTED = {
    "dol": ("Synthetic.dol", len(FILES[FIRST_ID]), hashlib.sha256(FILES[FIRST_ID]).hexdigest()),
    "elf": ("Synthetic.elf", len(FILES[SECOND_ID]), hashlib.sha256(FILES[SECOND_ID]).hexdigest()),
}


class MockRequest:
    def __init__(self, response):
        self.response = response

    def execute(self, **kwargs):
        return self.response


class MockDrive:
    def __init__(self, contents):
        self.contents = contents

    def files(self):
        return self

    def get(self, fileId, **kwargs):
        return MockRequest({"size": str(len(self.contents[fileId])), "mimeType": "application/octet-stream"})

    def get_media(self, fileId, **kwargs):
        return MockRequest(self.contents[fileId])


class TestPrivateWiiStaging(unittest.TestCase):
    def test_two_independently_authored_images_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            paths = stage_images(MockDrive(FILES), INPUTS, dest, EXPECTED)
            self.assertEqual(paths["dol"].read_bytes(), FILES[FIRST_ID])
            self.assertEqual(paths["elf"].read_bytes(), FILES[SECOND_ID])
            self.assertEqual(dest.stat().st_mode & 0o777, 0o700)
            self.assertEqual(paths["dol"].stat().st_mode & 0o777, 0o600)

    def test_wrong_payload_hash_refused_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            tampered = dict(FILES, **{SECOND_ID: FILES[SECOND_ID][:-1]+b"X"})
            with self.assertRaisesRegex(OriginalImageError, "SHA-256"):
                stage_images(MockDrive(tampered), INPUTS, dest, EXPECTED)
            self.assertFalse(dest.exists())

    def test_wrong_metadata_length_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "size mismatch"):
                stage_images(MockDrive({**FILES, SECOND_ID: b"tiny"}), INPUTS, dest, EXPECTED)
            self.assertFalse(dest.exists())

    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            dest.mkdir()
            saved = dest / "sentinel"
            saved.write_text("preserve-me")
            with self.assertRaisesRegex(OriginalImageError, "must not already exist"):
                stage_images(MockDrive(FILES), INPUTS, dest, EXPECTED)
            self.assertEqual(saved.read_text(), "preserve-me")

    def test_refuse_duplicate_private_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "duplicate"):
                stage_images(MockDrive(FILES), {"dol": FIRST_ID, "elf": FIRST_ID}, dest, EXPECTED)
            self.assertFalse(dest.exists())

    def test_refuse_malformed_or_missing_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            for ids in ({"dol": FIRST_ID}, {"dol": "../unsafe", "elf": SECOND_ID}):
                with self.assertRaises(OriginalImageError):
                    stage_images(MockDrive(FILES), ids, dest, EXPECTED)
                self.assertFalse(dest.exists())

    def test_reject_google_native_document(self):
        class GoogleDocumentDrive(MockDrive):
            def get(self, fileId, **kwargs):
                return MockRequest({"size": str(len(self.contents[fileId])),
                                    "mimeType": "application/vnd.google-apps.document"})
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            with self.assertRaisesRegex(OriginalImageError, "Google workspace"):
                stage_images(GoogleDocumentDrive(FILES), INPUTS, dest, EXPECTED)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
