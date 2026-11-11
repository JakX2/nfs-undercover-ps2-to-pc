"""Original-free XNFSModFiles.txt loader manifest validation regressions."""
import json
import tempfile
from pathlib import Path
import unittest

from carbon_pc_xnfsmodfiles_manifest_gate import (
    MAX_CONFIG_BYTES, audit_manifest_file, parse_one_carbon_control,
)

PATH = r'MODS\KnownGoodPC.BUN'
ROW = ('1,1,' + PATH).encode('ascii')


class CarbonManifestTests(unittest.TestCase):
    def test_strict_original_public_loader_format(self):
        out = parse_one_carbon_control(ROW + b'\n', PATH)
        self.assertEqual(out['entries'], 1)
        self.assertEqual(out['loader_stage'], 'postinit')
        self.assertEqual(out['resource_file_type'], 1)
        self.assertTrue(out['relative_control_path_match'])
        self.assertFalse(out['carbon_create_resource_called_verified'])
        self.assertFalse(out['carbon_begin_loading_called_verified'])

    def test_carbon_preinit_and_type_six(self):
        out = parse_one_carbon_control(b'0,6,MODS\\A.BUN\n', 'mods/a.bun')
        self.assertEqual(out['loader_stage'], 'preinit')
        self.assertEqual(out['resource_file_type'], 6)

    def test_windows_crlf_and_comments_allowed(self):
        text = b'# Carbon source-only control\r\n\r\n1,1,MODS\\KnownGoodPC.BUN\r\n'
        self.assertTrue(parse_one_carbon_control(
            text, PATH)['manifest_safe_single_source_entry'])

    def test_filename_is_case_insensitive(self):
        out = parse_one_carbon_control(ROW, 'mods/knowngoodpc.bun')
        self.assertEqual(out['entries'], 1)

    def test_extra_file_even_identical_entry_refused(self):
        for data in (ROW + b'\n' + ROW,
                     ROW + b'\n1,6,MODS\\Other.BUN',
                     b'0,1,MODS\\Other.BUN\n' + ROW):
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_one_carbon_control(data, PATH)

    def test_wrong_control_path_refused(self):
        with self.assertRaises(ValueError):
            parse_one_carbon_control(ROW, 'MODS\\Other.BUN')
        with self.assertRaises(ValueError):
            parse_one_carbon_control(b'1,1,MODS\\Other.BUN', PATH)

    def test_path_traversal_and_absolute_paths_refused(self):
        for name in (r'MODS\..\Other.BUN', r'MODS\.\Other.BUN',
                     r'C:\Carbon\MODS\Good.BUN',
                     r'\\server\share\Other.BUN', r'MODS\Z:Other.BUN',
                     r'GLOBAL\A.BUN', r'MODS\Other.TXT', r'MODS\\Other.BUN'):
            data = ('1,1,' + name).encode('ascii')
            with self.subTest(name=name), self.assertRaises(ValueError):
                parse_one_carbon_control(data, name)

    def test_invalid_stage_or_resource_type_refused(self):
        for row in (b'2,1,MODS\\KnownGoodPC.BUN',
                    b'-1,1,MODS\\KnownGoodPC.BUN',
                    b'01,1,MODS\\KnownGoodPC.BUN',
                    b'1,42,MODS\\KnownGoodPC.BUN',
                    b'1,01,MODS\\KnownGoodPC.BUN'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_one_carbon_control(row, PATH)

    def test_c_parser_ambiguities_refused(self):
        for row in (b'1,1,MODS\\KnownGoodPC.BUN#inline',
                    b' 1,1,MODS\\KnownGoodPC.BUN',
                    b'1,1,MODS\\KnownGoodPC.BUN ',
                    b'1,1,MODS\\KnownGoodPC.BUN foo',
                    b'1,1,MODS\\KnownGoodPC.BUN,more',
                    b'1,1,MODS\\KnownGoodPC.BUN\r',
                    b'1,1,MODS\\KnownGoodPC.BUN\x00garbage'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_one_carbon_control(row, PATH)

    def test_empty_config_or_comments_only_refused(self):
        for row in (b'', b'#comment\n', b'\n', b'\r\n'):
            with self.subTest(data=row), self.assertRaises(ValueError):
                parse_one_carbon_control(row, PATH)

    def test_reject_excessive_config_and_line_length(self):
        with self.assertRaises(ValueError):
            parse_one_carbon_control(b'#' * (MAX_CONFIG_BYTES + 1), PATH)
        with self.assertRaises(ValueError):
            parse_one_carbon_control(b'#' * 300 + b'\n' + ROW, PATH)

    def test_reject_nonascii_and_wrong_argument_type(self):
        with self.assertRaises(ValueError):
            parse_one_carbon_control(ROW + b'\xff', PATH)
        with self.assertRaises(ValueError):
            parse_one_carbon_control(bytearray(ROW), PATH)
        with self.assertRaises(ValueError):
            parse_one_carbon_control(ROW, None)

    def test_private_report_contains_no_path(self):
        output = parse_one_carbon_control(ROW, PATH)
        encoded = json.dumps(output)
        self.assertNotIn('KnownGoodPC', encoded)
        self.assertNotIn('MODS', encoded)

    def test_owner_file_audit_is_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / 'XNFSModFiles.txt'
            file.write_bytes(b'# private test\r\n' + ROW + b'\r\n')
            before = file.stat()
            result = audit_manifest_file(file, PATH)
            after = file.stat()
            self.assertEqual(result['resource_file_type'], 1)
            self.assertFalse(result['local_files_modified'])
            self.assertEqual((before.st_size, before.st_mtime_ns),
                             (after.st_size, after.st_mtime_ns))

    def test_reject_missing_or_oversize_owner_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'missing.txt'
            with self.assertRaises(ValueError):
                audit_manifest_file(path, PATH)
            path.write_bytes(b'1' * (MAX_CONFIG_BYTES + 1))
            with self.assertRaises(ValueError):
                audit_manifest_file(path, PATH)

    def test_reject_symlink_owner_file(self):
        with tempfile.TemporaryDirectory() as td:
            native = Path(td) / 'manifest.txt'
            alias = Path(td) / 'XNFSModFiles.txt'
            native.write_bytes(ROW)
            try:
                alias.symlink_to(native)
            except (OSError, NotImplementedError):
                self.skipTest('No symlink support')
            with self.assertRaises(ValueError):
                audit_manifest_file(alias, PATH)


if __name__ == '__main__':
    unittest.main()
