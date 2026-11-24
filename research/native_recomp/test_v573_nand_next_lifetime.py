import unittest
from derive_v573_nand_next_lifetime import history,patch,NEW,GUARD
from derive_v393_nand_guest_next import TRIAL_PROOF
from test_v563_nand_cache import POST,CHAIN,EVENT
NEXT=b'V393_NAND_NEXT_CALL guest=1 clear=1 registered=1 masked=1 reply=1 clearctx=0 setctx=1 cache=0 isfs=0'
ISFS=b'V394_NAND_ISFS_ENTRY guest=1 clear=1 masked=1 registered=1 mapped=1 selected=1 result=1 userdata=1'
CACHE=b'V563_NAND_CACHE_TRIAL history=1 legacy_stop=0'
TRIAL=b'V393_NAND_NEXT_TRIAL first=1 next=1 completed=0'
PROOF=b'V573_NAND_NEXT_PROOF history=1 legacy_stop=0'
class Tests(unittest.TestCase):
    def test_history(self):
        seq=(POST,CHAIN,EVENT,NEXT,ISFS,CACHE,TRIAL)
        self.assertIn('ordered=1',history(b'\n'.join(seq)))
        self.assertIn('ordered=1',history(b'\n'.join(seq[:-1]+(PROOF,TRIAL.replace(b'completed=0',b'completed=1'))),False))
        for bad in (seq[:3]+seq[4:],seq[:4]+seq[5:],seq[:3]+(ISFS,NEXT)+seq[5:],
                    seq[:4]+(NEXT,)+seq[4:],seq[:3]+(NEXT.replace(b'setctx=1',b'setctx=0'),)+seq[4:],
                    seq[:4]+(ISFS.replace(b'guest=1',b'guest=0'),)+seq[5:],
                    seq[:5]+(CACHE.replace(b'history=1',b'history=0'),TRIAL),
                    seq[:-1]+(TRIAL.replace(b'next=1',b'next=0'),)):
            with self.assertRaises(ValueError):history(b'\n'.join(bad))
    def test_patch(self):
        old='v394_context_inst=ctx.inst_count;\nv395_isfs_inst=ctx.inst_count;\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old)
        self.assertIn(NEW,new);self.assertIn(GUARD,new)
        self.assertIn('c.pc==nwii::runtime::v393_next_pc',new)
        self.assertIn('check(later,"later guard");',new)
        for bad in (new,old.replace('v395_isfs_inst=ctx.inst_count;',''),old.replace('c.pc==','')):
            with self.assertRaises(ValueError):patch(bad)
if __name__=='__main__':unittest.main()
