"""Synthetic-only PE32 address mapping tests; no executable modification."""
import struct
import tempfile
import unittest
from pathlib import Path
from carbon_pc_external_loader_abi_preflight import inspect_exe, audit_file, REFERENCE_ADDRESSES


def fixture(exec_section=True, a=0x401000, b=0x401010):
    blob=bytearray(8192)
    blob[:2]=b'MZ'
    struct.pack_into('<I',blob,0x3c,0x80)
    blob[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<H',blob,0x84,0x14c)
    struct.pack_into('<H',blob,0x86,1)
    struct.pack_into('<H',blob,0x94,224)
    opt=0x98
    struct.pack_into('<H',blob,opt,0x10b)
    struct.pack_into('<I',blob,opt+28,0x400000)
    sec=opt+224
    blob[sec:sec+8]=b'.text\0\0\0'
    struct.pack_into('<IIII',blob,sec+8,0x1000,0x1000,0x1000,0x1000)
    struct.pack_into('<I',blob,sec+36,0x60000020 if exec_section else 0x40000040)
    blob[0x1000:0x2000]=b'\x90'*0x1000
    return bytes(blob),{'one':a,'two':b}


class LoaderPEChecks(unittest.TestCase):
    def test_valid_synthetic_sites(self):
        source,sites=fixture()
        x=inspect_exe(source,sites)
        self.assertTrue(x['all_external_addresses_in_executable_section'])
        self.assertEqual(x['external_addresses_examined'],2)
        self.assertFalse(x['matches_owner_audited_original_nfsc_sha256'])
        self.assertFalse(x['runtime_compatibility_verified'])

    def test_wrong_dos_signature(self):
        s,a=fixture()
        with self.assertRaises(ValueError):inspect_exe(b'NO'+s[2:],a)

    def test_wrong_pe_signature(self):
        s,a=fixture();b=bytearray(s);b[0x80]=0
        with self.assertRaises(ValueError):inspect_exe(bytes(b),a)

    def test_wrong_machine(self):
        s,a=fixture();b=bytearray(s);struct.pack_into('<H',b,0x84,0x8664)
        with self.assertRaises(ValueError):inspect_exe(bytes(b),a)

    def test_wrong_image_type(self):
        s,a=fixture();b=bytearray(s);struct.pack_into('<H',b,0x98,0x20b)
        with self.assertRaises(ValueError):inspect_exe(bytes(b),a)

    def test_out_of_range_section(self):
        s,a=fixture();b=bytearray(s);struct.pack_into('<I',b,0x178+20,0x5000)
        with self.assertRaises(ValueError):inspect_exe(bytes(b),a)

    def test_nonexecutable_section(self):
        s,a=fixture(exec_section=False)
        with self.assertRaises(ValueError):inspect_exe(s,a)

    def test_unmapped_site(self):
        s,a=fixture(b=0x500010)
        with self.assertRaises(ValueError):inspect_exe(s,a)

    def test_zero_code_window(self):
        s,a=fixture();b=bytearray(s);b[0x1000:0x1010]=bytes(16)
        with self.assertRaises(ValueError):inspect_exe(bytes(b),a)

    def test_malformed_address_set(self):
        s,a=fixture()
        for invalid in ({'x':True},{'x':-1},{'x':'401000'},{},None):
            with self.subTest(invalid=repr(invalid)),self.assertRaises(ValueError):
                inspect_exe(s,invalid)

    def test_nonbytes_source(self):
        s,a=fixture()
        with self.assertRaises(ValueError):inspect_exe(bytearray(s),a)

    def test_reject_missing_owner_exe(self):
        with self.assertRaises(ValueError):audit_file('/not/real/NFSC.exe')

    def test_audit_synthetic_exe(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'test.exe';path.write_bytes(fixture()[0])
            with self.assertRaises(ValueError):audit_file(path)

    def test_known_reference_sites_count(self):
        self.assertEqual(len(REFERENCE_ADDRESSES),5)


if __name__=='__main__':
    unittest.main()
