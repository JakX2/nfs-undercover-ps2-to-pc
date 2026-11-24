import unittest
from derive_v551_nand_chain_lifetime import history,patch,NEW,GUARD
from derive_v391_nand_post_ack_next import TRIAL_PROOF
POST=b'V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=1 context=0'
EVENT=b'V391_NAND_POST_ACK_EVENT kind=1 verified=1 owner=1 cache=1 context=0 callback=0 cap=0'
TRIAL=b'V391_NAND_POST_ACK_TRIAL kind=1 stopped=1 completed=0'
class Tests(unittest.TestCase):
    def test_history(self):
        raw=b'\n'.join((POST,EVENT,TRIAL))
        self.assertIn('verified=1',history(raw))
        for bad in ((EVENT,POST,TRIAL),(POST,EVENT,EVENT,TRIAL),(POST,EVENT.replace(b'owner=1',b'owner=0'),TRIAL),(POST,EVENT,TRIAL.replace(b'completed=0',b'completed=1')),(POST,TRIAL)):
            with self.assertRaises(ValueError):history(b'\n'.join(bad))
    def test_patch(self):
        old='v392_start_inst=ctx.inst_count;\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old)
        self.assertIn(NEW,new);self.assertIn(GUARD,new)
        self.assertIn('c.pc==nwii::runtime::v391_next_pc',new)
        self.assertIn('check(later,"later guard");',new)
        for bad in (new,old.replace('v392_start_inst=ctx.inst_count;',''),old.replace('c.pc==','')):
            with self.assertRaises(ValueError):patch(bad)
if __name__=='__main__':unittest.main()
