import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from write_sram_profile_v536 import payload,sram_fixture
from write_exi_profile_v505 import create
class Tests(unittest.TestCase):
    def test_fixture(self):
        s=sram_fixture()
        self.assertEqual(len(s),64)
        self.assertEqual(s[:4],bytes([7,24,41,58]))
        self.assertEqual(s[60:62],b'\x12\x00')
        self.assertGreaterEqual(len(set(s)),62)
        self.assertEqual(payload().splitlines()[-1],b'sram='+s.hex().encode())
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
