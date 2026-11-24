import tempfile
import unittest
from pathlib import Path
from write_exi_profile_v505 import encode,create
class Tests(unittest.TestCase):
    def test_format(self):
        src=bytes(range(64))
        result=encode(0xbeef0010,1,0x12345678,8,src)
        self.assertEqual(result,b'UNDERCOVER_EXI_PROFILE_V1\nid=beef0010\ndi_config=00000001\nrtc_seconds=12345678\nlatency=00000008\nsram='+src.hex().encode()+b'\n')
        for args in ((-1,1,0,8,src),(0,1<<32,0,8,src),(0,1,0,0,src),(0,1,0,1000001,src),
                     (0,1,0,8,src[:-1]),(0,1,0,8,bytearray(src)),(True,1,0,8,src)):
            with self.assertRaises(ValueError):encode(*args)
    def test_exclusive_create(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'profile.txt';create(p,b'first')
            with self.assertRaises(OSError):create(p,b'overwrite')
            self.assertEqual(p.read_bytes(),b'first')
            link=Path(td)/'link'
            try:link.symlink_to(p)
            except (OSError,NotImplementedError):return
            with self.assertRaises(OSError):create(link,b'overwrite')
            self.assertEqual(p.read_bytes(),b'first')
if __name__=='__main__':unittest.main()
