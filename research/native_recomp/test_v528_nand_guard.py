import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from export_v528_nand_guard import select
HEAD=b'V517_NAND_NEXT_GUARD aborted=1 id=1237 class=other matches=1 boot_verified=0'
SRC=b'V517_NAND_GUARD_SOURCE id=1237 n=1 file=derive_public.py line=2 boot_verified=0'
ABORT=b'V508_ABORT_CENSUS rc=134 public_id=1237 known=1 category=public_guard exception=runtime boot_verified=0'
class Tests(unittest.TestCase):
    def test_export(self):
        with TemporaryDirectory() as td:
            host=Path(td);(host/'derive_public.py').write_text('first\nsecond\n')
            good=b'\n'.join((b'private bytes ignored',ABORT,HEAD,SRC))
            self.assertEqual(select(good,host),(HEAD,SRC))
            for bad in (good+b'\n'+SRC,good.replace(b'line=2',b'line=3'),good.replace(b'class=other',b'class=private'),good.replace(b'file=derive_public.py',b'file=../private.py'),good.replace(b'n=1 file=',b'n=2 file='),good.replace(b'public_id=1237',b'public_id=1238'),good.replace(b'matches=1',b'matches=2'),good.replace(b'boot_verified=0',b'boot_verified=1')):
                with self.assertRaises(ValueError):select(bad,host)
            self.assertEqual(select(b'V517_NAND_NEXT_GUARD aborted=0 boot_verified=0',host),(b'V517_NAND_NEXT_GUARD aborted=0 boot_verified=0',))
if __name__=='__main__':unittest.main()
