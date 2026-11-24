import unittest
from derive_v583_nand_isfs_lifetime import history,patch,NEW,GUARD
from derive_v394_nand_isfs_entry import TRIAL_PROOF
from test_v573_nand_next_lifetime import POST,CHAIN,EVENT,NEXT,ISFS,CACHE,PROOF as PRIOR_PROOF,TRIAL as PRIOR_TRIAL
SELECTED=b'V395_NAND_ISFS_NEXT guest=1 clear=1 masked=1 registered=1 mapped=1 selected=1 userdata=1 nand=0'
TRIAL=b'V394_NAND_ISFS_TRIAL context=1 isfs=1 completed=0'
PROOF=b'V583_NAND_ISFS_PROOF history=1 legacy_stop=0'
class Tests(unittest.TestCase):
    def test_history(self):
        seq=(POST,CHAIN,EVENT,NEXT,ISFS,SELECTED,CACHE,PRIOR_PROOF,PRIOR_TRIAL.replace(b'completed=0',b'completed=1'),TRIAL)
        self.assertIn('selected=1',history(b'\n'.join(seq)))
        self.assertIn('selected=1',history(b'\n'.join(seq[:-1]+(PROOF,TRIAL.replace(b'completed=0',b'completed=1'))),False))
        for bad in (seq[:5]+seq[6:],seq[:4]+(SELECTED,ISFS)+seq[6:],seq[:6]+(SELECTED,)+seq[6:],
                    seq[:5]+(SELECTED.replace(b'selected=1',b'selected=0'),)+seq[6:],
                    seq[:5]+(SELECTED.replace(b'userdata=1',b'userdata=0'),)+seq[6:],
                    seq[:5]+(SELECTED.replace(b'mapped=1',b'mapped=0'),)+seq[6:],
                    seq[:-1]+(TRIAL.replace(b'isfs=1',b'isfs=0'),)):
            with self.assertRaises(ValueError):history(b'\n'.join(bad))
    def test_patch(self):
        old='v395_isfs_inst=ctx.inst_count;\nv396_start_inst=ctx.inst_count;\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old)
        self.assertIn(NEW,new);self.assertIn(GUARD,new)
        self.assertIn('c.pc==0x804f0e04u',new)
        self.assertIn('check(later,"later guard");',new)
        for bad in (new,old.replace('v396_start_inst=ctx.inst_count;',''),old.replace('c.pc==','')):
            with self.assertRaises(ValueError):patch(bad)
if __name__=='__main__':unittest.main()
