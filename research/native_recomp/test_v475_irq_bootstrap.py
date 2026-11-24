import unittest
from apply_irq_bootstrap_v475 import MAIN_PAIRS,STUB_PAIRS,rewrite
class Tests(unittest.TestCase):
    def test_roundtrip(self):
        for pairs in (MAIN_PAIRS,STUB_PAIRS):
            source='\n'.join(a for a,_ in pairs)
            out=rewrite(source,pairs)
            self.assertEqual(rewrite(out,pairs),out)
            for a,b in reversed(pairs):out=out.replace(b,a,1)
            self.assertEqual(out,source)
            for a,_ in pairs:
                for bad in (source.replace(a,'missing',1),source+'\n'+a):
                    with self.assertRaises(ValueError):rewrite(bad,pairs)
    def test_opt_in(self):
        main=rewrite('\n'.join(a for a,_ in MAIN_PAIRS),MAIN_PAIRS)
        self.assertIn('UNDERCOVER_V419_START',main)
        self.assertIn('NativeIosBinding binding(transport)',main)
        self.assertNotIn('service_at_guest_boundary',main)
        self.assertEqual(main.count('run_game(*ctx);'),2)
        stubs=rewrite('\n'.join(a for a,_ in STUB_PAIRS),STUB_PAIRS)
        self.assertIn('record(addr,val,32u,true)',stubs)
        self.assertIn('record(addr,val,32u,false)',stubs)
        self.assertIn('record(addr,val,16u,false)',stubs)
if __name__=='__main__':unittest.main()
