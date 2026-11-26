import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from write_sram_profile_v536 import payload,sram_fixture,wireless_zero_fixture
from write_exi_profile_v505 import create
class Tests(unittest.TestCase):
    def test_fixture(self):
        s=sram_fixture()
        self.assertEqual(len(s),64)
        self.assertEqual(s[:4],bytes([7,24,41,58]))
        self.assertEqual(s[60:62],b'\x12\x00')
        self.assertGreaterEqual(len(set(s)),62)
        self.assertEqual(payload().splitlines()[-1],b'sram='+s.hex().encode())
    def test_wireless_zero_profile(self):
        old=sram_fixture();new=wireless_zero_fixture()
        self.assertEqual(len(new),64)
        self.assertEqual(new[:48],old[:48]);self.assertEqual(new[56:],old[56:])
        for channel in range(4):
            at=48+2*channel
            self.assertNotEqual(old[at:at+2],bytes(2))
            self.assertEqual(new[at:at+2],bytes(2))
        self.assertEqual(payload('wireless-zero').splitlines()[:-1],payload().splitlines()[:-1])
        self.assertEqual(payload('wireless-zero').splitlines()[-1],b'sram='+new.hex().encode())
        with self.assertRaises(ValueError):payload('unknown')
    def test_exclusive_create(self):
        with TemporaryDirectory() as td:
            p=Path(td)/'profile'
            create(p,payload())
            with self.assertRaises(OSError):create(p,b'wrong')
            self.assertEqual(p.read_bytes(),payload())
            target=Path(td)/'link';target.symlink_to(p)
            with self.assertRaises(OSError):create(target,b'wrong')
            self.assertEqual(p.read_bytes(),payload())
if __name__=='__main__':unittest.main()
