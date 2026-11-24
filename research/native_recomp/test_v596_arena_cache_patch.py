import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from apply_arena_cache_trace_v596 import PAIRS,FILE,HEADER,apply
from apply_irq_bootstrap_v475 import rewrite
HOST=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_exact_composition(self):
        src='\n'.join(a for a,_ in PAIRS)
        out=rewrite(src,PAIRS)
        self.assertEqual(rewrite(out,PAIRS),out)
        self.assertLess(out.index('arena_cache_range.on_zero(ea)'),out.index('guest_dcbz_trace.zero(mmu,ea)'))
        for bad in (src+src,src.replace(PAIRS[-1][0],'')):
            with self.assertRaises(ValueError):rewrite(bad,PAIRS)
        with TemporaryDirectory() as d:
            root=Path(d);p=root/FILE;p.parent.mkdir(parents=True);p.write_text(src)
            apply(root,HOST);apply(root,HOST)
            self.assertEqual(p.read_text(),out)
            self.assertEqual((p.parent.parent/HEADER).read_bytes(),(HOST/Path(HEADER).name).read_bytes())
if __name__=='__main__':unittest.main()
