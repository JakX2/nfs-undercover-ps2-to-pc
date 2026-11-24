import unittest
from apply_cold_mapping_v612 import PAIRS
from apply_irq_bootstrap_v475 import rewrite
class Tests(unittest.TestCase):
    def test_exact_patch(self):
        src='\n'.join(a for a,b in PAIRS);out=rewrite(src,PAIRS)
        self.assertEqual(rewrite(out,PAIRS),out)
        self.assertIn('!is_gc,!vdisc.valid()',out)
        self.assertIn('UNDERCOVER_V591_MI',out)
        for bad in (src+src,src.replace(PAIRS[-1][0],'')):
            with self.assertRaises(ValueError):rewrite(bad,PAIRS)
if __name__=='__main__':unittest.main()
