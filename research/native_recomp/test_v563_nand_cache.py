import unittest
from derive_v563_nand_cache_lifetime import event_history,patch,NEW,GUARD
from derive_v392_nand_post_cache import TRIAL_PROOF
POST=b'V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=1 context=0'
CHAIN=b'V391_NAND_POST_ACK_EVENT kind=1 verified=1 owner=1 cache=1 context=0 callback=0 cap=0'
EVENT=b'V392_NAND_POST_CACHE_EVENT kind=1 verified=1 owner=1 cache=0 context=1 callback=0 bounded=0 caches=1'
TRIAL=b'V392_NAND_POST_CACHE_TRIAL kind=1 stopped=1 completed=0'
class Tests(unittest.TestCase):
    def test_history(self):
        self.assertIn('verified=1',event_history(b'\n'.join((POST,CHAIN,EVENT,TRIAL))))
        for bad in ((POST,EVENT,CHAIN,TRIAL),(POST,CHAIN,TRIAL),(POST,CHAIN,EVENT,EVENT,TRIAL),
                    (POST,CHAIN,EVENT.replace(b'owner=1',b'owner=0'),TRIAL),(POST,CHAIN,EVENT.replace(b'cache=0',b'cache=1'),TRIAL),
                    (POST,CHAIN,EVENT.replace(b'caches=1',b'caches=24'),TRIAL),(POST,CHAIN,EVENT,TRIAL.replace(b'completed=0',b'completed=1'))):
            with self.assertRaises(ValueError):event_history(b'\n'.join(bad))
    def test_patch(self):
        old='v393_start_inst=ctx.inst_count;\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old)
        self.assertIn(NEW,new);self.assertIn(GUARD,new);self.assertIn('c.pc==nwii::runtime::v392_next_pc',new)
        self.assertIn('check(later,"later guard");',new)
        for bad in (new,old.replace('v393_start_inst=ctx.inst_count;',''),old.replace('c.pc==','')):
            with self.assertRaises(ValueError):patch(bad)
if __name__=='__main__':unittest.main()
