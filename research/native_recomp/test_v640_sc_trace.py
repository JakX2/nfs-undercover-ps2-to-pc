import unittest
from patch_sc_trace_v570 import patch,TRACE
from patch_sc_trace_v640 import rewrite,NEW
class Tests(unittest.TestCase):
    def test_trace(self):
        base='loc_805222E8: ;\n    // 0x805222E8: 44000002\n    ++ctx.inst_count;\n'
        prior=patch(base);new=rewrite(prior)
        self.assertIn(NEW,new);self.assertNotIn(TRACE,new)
        self.assertEqual(rewrite(new),new)
        for bad in (base,prior+prior,prior.replace('44000002','60000000'),prior.replace('++ctx.inst_count;','')):
            with self.assertRaises(ValueError):rewrite(bad)
if __name__=='__main__':unittest.main()
