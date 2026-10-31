"""V35 safe recovery tests. Synthetic ZIPs only, no proprietary recordings."""
import io
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import legacy_audio_research_recovery_v35 as v35


class OriginalResearchRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.archive = self.root / "research.zip"

    def make_zip(self, items):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in items:
                z.writestr(name, data)

    def test_original_safe_source_files_are_recovered(self):
        self.make_zip([
            ("v21/idx_parser.py", b"# IDX BIG offset\nparser = 1\n"),
            ("v21/evt_notes.md", b"EVT group / CSI event\n"),
            ("v21/voice.asf", b"SCHl" + b"\x00" * 32),
        ])
        target = self.root / "private"
        report = v35.recover(self.archive, target)
        self.assertEqual(report["selected_source_files"], 2)
        self.assertTrue((target/"research_sources/v21/idx_parser.py").exists())
        self.assertFalse((target/"research_sources/v21/voice.asf").exists())
        self.assertFalse(report["original_undercover_voice_decoded"])

    def test_manifest_is_deterministic(self):
        self.make_zip([("legacy/v20/parser.py", "IDX group SCHl".encode())])
        a, _ = v35.manifest(self.archive)
        b, _ = v35.manifest(self.archive)
        self.assertEqual(a, b)
        self.assertEqual(len(a["archive_sha256"]), 64)

    def test_keyword_index_references_source_file(self):
        self.make_zip([
            ("parser.py", b"IDX EVT CSI MicroTalk SCDl\n"),
            ("readme.md", b"Unrelated content."),
        ])
        r, _ = v35.manifest(self.archive)
        self.assertIn("parser.py", r["likely_relevant_source_paths"])
        self.assertNotIn("readme.md", r["likely_relevant_source_paths"])

    def test_sources_not_executed(self):
        self.make_zip([("malicious.py", b"raise RuntimeError('must not run')\n")])
        result = v35.recover(self.archive, self.root/"safe")
        self.assertTrue(result["no_source_code_executed"])

    def test_excluded_binary_extensions(self):
        self.make_zip([
            ("game.BIG", b"SCHl" + b"\0" * 20),
            ("game.IDX", b"\x00" * 64),
            ("game.EVT", b"\x00" * 64),
            ("game.CSI", b"\x00" * 64),
            ("code.py", b"def inspect(): pass\n"),
        ])
        r, _ = v35.manifest(self.archive)
        self.assertEqual(r["selected_source_files"], 1)

    def test_reject_binary_disguised_as_text(self):
        self.make_zip([("bad.txt", b"hello\x00world")])
        r, _ = v35.manifest(self.archive)
        self.assertEqual(r["selected_source_files"], 0)

    def test_reject_non_utf8_text(self):
        self.make_zip([("bad.py", b"\xff\xfe\xf5")])
        r, _ = v35.manifest(self.archive)
        self.assertEqual(r["selected_source_files"], 0)

    def test_utf8_with_bom_is_accepted(self):
        self.make_zip([("good.py", b"\xef\xbb\xbf# EVT\n")])
        r, _ = v35.manifest(self.archive)
        self.assertEqual(r["selected_source_files"], 1)

    def test_reject_parent_path_traversal(self):
        self.make_zip([("../outside.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_nested_path_traversal(self):
        self.make_zip([("safe/../../outside.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_backslash_windows_path_traversal(self):
        self.make_zip([("safe\\..\\outside.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_absolute_member(self):
        self.make_zip([("/tmp/outside.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_windows_drive_member(self):
        self.make_zip([("C:/something.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_noncanonical_double_slash(self):
        self.make_zip([("a//b.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_file_names_with_colon(self):
        self.make_zip([("some:stream.py", b"hello")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_symlink_member(self):
        with zipfile.ZipFile(self.archive, "w") as z:
            info = zipfile.ZipInfo("malicious.py")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, "outside.py")
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_reject_case_insensitive_filename_collisions(self):
        self.make_zip([("IDX.PY", b"a"), ("idx.py", b"b")])
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_existing_output_never_overwritten(self):
        self.make_zip([("readme.md", b"hello")])
        directory = self.root/"target"
        directory.mkdir()
        sentinel = directory / "file"
        sentinel.write_bytes(b"unchanged")
        with self.assertRaises(v35.RecoveryError):
            v35.recover(self.archive, directory)
        self.assertEqual(sentinel.read_bytes(), b"unchanged")

    def test_reject_missing_archive(self):
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.root / "missing.zip")

    def test_reject_corrupt_zip(self):
        self.archive.write_bytes(b"not a real ZIP")
        with self.assertRaises(v35.RecoveryError):
            v35.manifest(self.archive)

    def test_member_count_limit(self):
        self.make_zip([("tiny/%04d.py" % i, b"a") for i in range(31)])
        with patch.object(v35, "MAX_MEMBERS", 30):
            with self.assertRaises(v35.RecoveryError):
                v35.manifest(self.archive)

    def test_reject_oversized_source(self):
        self.make_zip([("giant.py", b"A" * 1025)])
        with patch.object(v35, "MAX_MEMBER_BYTES", 1024):
            with self.assertRaises(v35.RecoveryError):
                v35.manifest(self.archive)

    def test_reject_total_size_limit(self):
        self.make_zip([("a.py", b"x" * 50), ("b.md", b"y" * 50)])
        with patch.object(v35, "MAX_TOTAL_BYTES", 60):
            with self.assertRaises(v35.RecoveryError):
                v35.manifest(self.archive)

    def test_reject_zip_compression_bomb_ratio(self):
        self.make_zip([("huge.py", b"A" * 100_000)])
        with patch.object(v35, "MAX_RATIO", 10):
            with self.assertRaises(v35.RecoveryError):
                v35.manifest(self.archive)

    def test_empty_archive_has_no_source(self):
        self.make_zip([])
        report, _ = v35.manifest(self.archive)
        self.assertEqual(report["selected_source_files"], 0)
        self.assertEqual(report["likely_relevant_source_paths"], [])

    def test_cli_inspect_prints_manifest_without_export(self):
        self.make_zip([("v21/idx.py", b"# IDX parser\n")])
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = v35.main(["inspect", "--archive", str(self.archive)])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue())["selected_source_files"], 1)
        self.assertFalse((self.root / "research_sources").exists())

    def test_cli_recover_writes_new_source_only(self):
        self.make_zip([("v21/idx.py", b"pass\n"), ("audio.wav", b"RIFF")])
        folder = self.root/"private"
        with patch("sys.stdout", new_callable=io.StringIO):
            rc = v35.main([
                "recover", "--archive", str(self.archive),
                "--out-dir", str(folder)
            ])
        self.assertEqual(rc, 0)
        self.assertEqual((folder/"research_sources/v21/idx.py").read_bytes(), b"pass\n")
        self.assertFalse((folder/"research_sources/audio.wav").exists())
        self.assertTrue((folder/"manifest.json").exists())

    def test_recover_does_not_mangle_source_bytes(self):
        source = b"# SCHl\x0aif True:\x0a  print('hello')\x0a"
        self.make_zip([("tools/check.py", source)])
        v35.recover(self.archive, self.root/"private")
        self.assertEqual((self.root/"private/research_sources/tools/check.py").read_bytes(), source)

    def test_self_test_copyright_free_archive(self):
        result = v35.self_test()
        self.assertTrue(result["audio_files_excluded"])
        self.assertFalse(result["real_v21_zip_inspected"])
        self.assertEqual(result["selected_source_files"], 2)

    def test_nested_zip_is_not_auto_extracted(self):
        self.make_zip([("archive-with-game-files.zip", b"just fake data"),
                       ("parser.bms", b"get OFFSET long\n")])
        r, _ = v35.manifest(self.archive)
        self.assertEqual(r["selected_source_files"], 1)

    def test_cli_missing_source_returns_error(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            rc = v35.main(["inspect", "--archive", str(self.root / "missing.zip")])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
