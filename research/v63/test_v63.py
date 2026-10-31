"""V63 source-only PE32 compatibility tests. All executables are synthetic."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parent))
import v63_carbon_runtime_preflight as v63


def synthetic_pe(*,image_base=0x400000, text_rva=0x2B0000,
                 raw_size=0x9000,virtual_size=0x9000,
                 text_executable=True,machine=0x14C):
    """Minimal x86 PE32 with one high-RVA synthetic .text section."""
    data=bytearray(0x200+raw_size)
    data[:2]=b'MZ'
    struct.pack_into('<I',data,0x3C,0x80)
    data[0x80:0x84]=b'PE\x00\x00'
    coff=0x84
    struct.pack_into('<HHIIIHH',data,coff,machine,1,0,0,0,0xE0,0x0102)
    opt=0x98
    struct.pack_into('<H',data,opt,0x10B)
    struct.pack_into('<I',data,opt+28,image_base)
    struct.pack_into('<I',data,opt+56,0x2C0000)
    sec=opt+0xE0
    data[sec:sec+8]=b'.text\x00\x00\x00'
    struct.pack_into('<IIII',data,sec+8,virtual_size,text_rva,raw_size,0x200)
    struct.pack_into('<I',data,sec+36,0x60000020 if text_executable else 0x40000040)
    # Distinct synthetic bytes only, never original copyrighted executable code.
    data[0x200:]=b'\xCC'*raw_size
    return bytes(data)


def make_file(td,contents):
    path=Path(td)/'NFSC_SYNTHETIC_DO_NOT_RUN.exe'
    path.write_bytes(contents)
    return path


class RuntimePreflightTests(unittest.TestCase):

    def test_all_historical_addresses_file_backed_in_matching_synthetic_PE(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            r=v63.inspect_executable(p)
            self.assertTrue(r['historical_addresses_in_executable_file_backed_sections'])
            self.assertTrue(r['historical_address_layout_compatible_prerequisite_only'])
            self.assertEqual(len(r['historical_address_checks']),4)
            self.assertFalse(r['safe_to_install_or_patch'])
            self.assertFalse(r['engine_function_ABI_verified'])
            self.assertEqual(r['pe_image_base'],'0x00400000')

    def test_public_addresses_match_pinned_carbon_header_values(self):
        self.assertEqual(v63.CARBON_HISTORICAL_VAS,{
            'CreateResourceFile':0x006B32C0,
            'BeginLoading':0x006B5910,
            'Stage1JumpEntry':0x006B6D56,
            'Stage2CallEntry':0x006B7850,
        })
        self.assertEqual(v63.CARBON_XNFS_SOURCE['commit'],
                         'de4164ac55620f38a173ddf855c28bd036e74883')

    def test_address_to_raw_file_offset(self):
        pe=v63.parse_pe32(synthetic_pe())
        first=v63.audit_address(pe,v63.CARBON_HISTORICAL_VAS['CreateResourceFile'])
        self.assertEqual(first['rva'],'0x002B32C0')
        self.assertEqual(first['section'],'.text')
        self.assertEqual(first['file_offset'],0x200+0x32C0)
        self.assertFalse(first['verified_function_or_hook_abi'])

    def test_different_image_base_means_no_old_address_assumption(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe(image_base=0x500000))
            report=v63.inspect_executable(p)
            self.assertFalse(report['historical_addresses_in_executable_file_backed_sections'])
            self.assertTrue(all(x['within_image'] for x in report['historical_address_checks'].values()))
            self.assertTrue(all(x['section'] is None for x in report['historical_address_checks'].values()))

    def test_nonexecutable_section_rejects_runtime_prerequisite(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe(text_executable=False))
            r=v63.inspect_executable(p)
            self.assertFalse(r['historical_addresses_in_executable_file_backed_sections'])
            self.assertTrue(all(x['file_backed'] for x in r['historical_address_checks'].values()))
            self.assertTrue(all(not x['in_executable_section'] for x in r['historical_address_checks'].values()))

    def test_virtual_only_non_file_backed_addresses(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe(raw_size=0x1000))
            r=v63.inspect_executable(p)
            self.assertFalse(r['historical_addresses_in_executable_file_backed_sections'])
            self.assertTrue(all(not x['file_backed'] for x in r['historical_address_checks'].values()))

    def test_nonmatching_rva_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe(text_rva=0x290000))
            self.assertFalse(v63.inspect_executable(p)['historical_addresses_in_executable_file_backed_sections'])

    def test_valid_expected_sha_guard(self):
        with tempfile.TemporaryDirectory() as td:
            data=synthetic_pe()
            p=make_file(td,data)
            r=v63.inspect_executable(p,expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertTrue(r['expected_executable_sha256_guard_applied'])
            self.assertEqual(r['input_executable_sha256'],hashlib.sha256(data).hexdigest())

    def test_bad_expected_sha_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            with self.assertRaisesRegex(v63.PEError,'SHA-256 mismatch'):
                v63.inspect_executable(p,expected_sha256='0'*64)

    def test_malformed_expected_sha_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            with self.assertRaisesRegex(v63.PEError,'exactly 64'):
                v63.inspect_executable(p,expected_sha256='invalid')

    def test_truncated_mz_rejected(self):
        with self.assertRaises(v63.PEError):
            v63.parse_pe32(b'MZ\x00')

    def test_wrong_pe_signature_rejected(self):
        raw=bytearray(synthetic_pe())
        raw[0x80:0x84]=b'BAD!'
        with self.assertRaisesRegex(v63.PEError,'PE signature'):
            v63.parse_pe32(bytes(raw))

    def test_pe32plus_rejected(self):
        raw=bytearray(synthetic_pe())
        struct.pack_into('<H',raw,0x98,0x20B)
        with self.assertRaisesRegex(v63.PEError,'PE32'):
            v63.parse_pe32(bytes(raw))

    def test_wrong_machine_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe(machine=0x8664))
            with self.assertRaisesRegex(v63.PEError,'32-bit x86'):
                v63.inspect_executable(p)

    def test_zero_section_count_rejected(self):
        raw=bytearray(synthetic_pe())
        struct.pack_into('<H',raw,0x86,0)
        with self.assertRaisesRegex(v63.PEError,'section count'):
            v63.parse_pe32(bytes(raw))

    def test_truncated_section_raw_data_rejected(self):
        raw=synthetic_pe()
        with self.assertRaisesRegex(v63.PEError,'raw data exceeds file'):
            v63.parse_pe32(raw[:-100])

    def test_section_extent_outside_image_rejected(self):
        raw=bytearray(synthetic_pe())
        struct.pack_into('<I',raw,0x178+12,0x2C0000)
        with self.assertRaisesRegex(v63.PEError,'Section exceeds'):
            v63.parse_pe32(bytes(raw))

    def test_early_pe_pointer_rejected(self):
        raw=bytearray(synthetic_pe())
        struct.pack_into('<I',raw,0x3C,0x20)
        with self.assertRaises(v63.PEError):
            v63.parse_pe32(bytes(raw))

    def test_mutation_during_parser_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            original=v63.parse_pe32
            changed=[False]
            def mutate(data):
                if not changed[0]:
                    changed[0]=True
                    with p.open('r+b') as out:
                        out.seek(-1,2)
                        out.write(b'\x20')
                return original(data)
            with mock.patch.object(v63,'parse_pe32',side_effect=mutate):
                with self.assertRaisesRegex(v63.PEError,'changed during preflight'):
                    v63.inspect_executable(p)
            self.assertTrue(changed[0])

    def test_path_replacement_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            other=Path(td)/'replacement.exe'
            other.write_bytes(p.read_bytes())
            orig=v63.parse_pe32
            changed=[False]
            def replace(data):
                if not changed[0]:
                    changed[0]=True
                    other.replace(p)
                return orig(data)
            with mock.patch.object(v63,'parse_pe32',side_effect=replace):
                with self.assertRaisesRegex(v63.PEError,'path replaced'):
                    v63.inspect_executable(p)

    def test_original_synthetic_exe_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            data=synthetic_pe()
            p=make_file(td,data)
            v63.inspect_executable(p)
            self.assertEqual(p.read_bytes(),data)

    def test_report_omits_private_paths_and_executable_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            report=json.dumps(v63.inspect_executable(p))
            self.assertNotIn(str(p),report)
            self.assertNotIn('NFSC_SYNTHETIC',report)
            self.assertFalse(json.loads(report)['safe_to_install_or_patch'])

    def test_cli_report_written_exclusively(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            report=Path(td)/'report.json'
            cmd=[sys.executable,str(Path(v63.__file__)),'--executable',str(p),
                 '--report',str(report)]
            call=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(call.returncode,0,call.stderr)
            self.assertFalse(json.loads(report.read_text())['safe_to_install_or_patch'])
            retry=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(retry.returncode,0)

    def test_cli_refuses_to_overwrite_original_exe(self):
        with tempfile.TemporaryDirectory() as td:
            p=make_file(td,synthetic_pe())
            before=p.read_bytes()
            cmd=[sys.executable,str(Path(v63.__file__)),'--executable',str(p),
                 '--report',str(p)]
            call=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(call.returncode,0)
            self.assertEqual(p.read_bytes(),before)


if __name__=='__main__':
    unittest.main()
