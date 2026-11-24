import unittest
from apply_open_cache_trace_v649 import PAIRS
from apply_irq_bootstrap_v475 import rewrite
class Tests(unittest.TestCase):
    def test_seams(self):
        src='\n'.join(a for a,_ in PAIRS);new=rewrite(src,PAIRS)
        self.assertIn('open_cache_range.on_flush(effective_address);',new)
        self.assertIn('open_cache_range.on_zero(ea);',new)
        self.assertEqual(new,rewrite(new,PAIRS))
        for bad in ('',src+src,src.replace('arena_cache_range.on_flush(effective_address);','')):
            with self.assertRaises(ValueError):rewrite(bad,PAIRS)
if __name__=='__main__':unittest.main()
