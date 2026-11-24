import unittest
from derive_v542_nand_successor_lifetime import BEGIN,END,GUARD,NEW,patch
from derive_v508_nand_ack_lifetime import NEW_FINAL
from derive_v390_nand_post_ack import TRIAL_PROOF
class Tests(unittest.TestCase):
    def test_patch(self):
        old=NEW_FINAL+'\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old)
        self.assertIn('const bool v542_legacy_successor=v389_completed',new)
        self.assertIn(NEW,new);self.assertIn(GUARD,new)
        self.assertIn('check(later,"later guard");',new)
        self.assertIn('c.pc==nwii::runtime::v390_call_pc',new)
        self.assertNotIn('ctx.mmu.write',new)
        for seam in (BEGIN,END,GUARD,'const bool v508_historical=','c.pc=='):
            with self.assertRaises(ValueError):patch(old.replace(seam,''))
        with self.assertRaises(ValueError):patch(new)
if __name__=='__main__':unittest.main()
