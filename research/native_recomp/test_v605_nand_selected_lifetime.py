import unittest
from derive_v605_nand_selected_lifetime import history,patch,GUARD
from derive_v395_nand_isfs_next import TRIAL_PROOF
from test_v583_nand_isfs_lifetime import SELECTED,TRIAL,PROOF
from test_v573_nand_next_lifetime import POST,CHAIN,EVENT,NEXT,ISFS,CACHE,PROOF as PRIOR_PROOF,TRIAL as PRIOR_TRIAL
FRAME=b'V437_FRAME_BEGIN valid=1'
ENTRY=b'V420_CB_ENTRY call=0 pc=80510000 lr=804f0f54 ew=60000000 lw=4e800421 em=1 lm=1 resumed=0 sc=0 r3=0'
BLR=b'V437_FRAME_BLR valid=1'
RESUME=b'V437_FRAME_RESUME valid=1'
FINAL=b'V395_NAND_ISFS_TRIAL isfs=1 next=1 completed=0'
NEW=b'V605_NAND_SELECTED_PROOF history=1 legacy_stop=0'
class Tests(unittest.TestCase):
    def test_history(self):
        seq=(POST,CHAIN,EVENT,NEXT,ISFS,SELECTED,FRAME,ENTRY,BLR,RESUME,CACHE,PRIOR_PROOF,PRIOR_TRIAL.replace(b'completed=0',b'completed=1'),PROOF,TRIAL.replace(b'completed=0',b'completed=1'),FINAL)
        self.assertEqual(history(b'\n'.join(seq))[:2],(0x80510000,0x804f0f54))
        self.assertEqual(history(b'\n'.join(seq[:-1]+(NEW,FINAL.replace(b'completed=0',b'completed=1'))),False)[:2],(0x80510000,0x804f0f54))
        for bad in (seq[:6]+seq[7:],seq[:8]+seq[9:],seq[:9]+seq[10:],seq[:7]+(ENTRY.replace(b'em=1',b'em=0'),)+seq[8:],seq[:7]+(ENTRY.replace(b'lr=804f0f54',b'lr=80510000'),)+seq[8:],seq[:8]+(RESUME,BLR)+seq[10:],seq[:-1]+(FINAL.replace(b'next=1',b'next=0'),)):
            with self.assertRaises(ValueError):history(b'\n'.join(bad))
    def test_patch(self):
        old='V583_NAND_ISFS_PROOF history=\nv396_start_inst=ctx.inst_count;\nV437_FRAME_RESUME valid=1\n'+TRIAL_PROOF+'\n  check(later,"later guard");'
        new=patch(old,0x80510000,0x804f0f54)
        self.assertIn('v437_frame.stage()==3u',new);self.assertIn('v395_next_pc==0x80510000u',new);self.assertIn(GUARD,new)
        self.assertIn('check(later,"later guard");',new)
        for bad in (new,old.replace('V437_FRAME_RESUME valid=1',''),old.replace('c.pc==','')):
            with self.assertRaises(ValueError):patch(bad,0x80510000,0x804f0f54)
if __name__=='__main__':unittest.main()
