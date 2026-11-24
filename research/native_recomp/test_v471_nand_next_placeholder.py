import unittest
from repair_v471_nand_next_placeholder import plan,outcome
from derive_v437_nand_restored_frame import entries
from test_v414_nand_resumed_coverage import dol,BODY,A,NOP
from test_v424_nand_aot_placeholder import cpp
from test_v437_nand_restored_frame import entry,log,BEGIN,BLR,RESUME
PCS=[A+16*i for i in range(23)]
SIZES={p:16 for p in PCS}
OWNER=dol(BODY*23)
SOURCE=''.join(cpp(p) for p in PCS)
def raw():
    order=PCS[:2]+[PCS[1]]*12+PCS[2:]
    lines=[BEGIN]
    for i,pc in enumerate(order):
        if i in (1,2):lines.append(f'V437_FRAME_NESTED call={i}'.encode())
        lines.append(entry(i,pc,A+0x1000))
    return log(*lines)
RAW=raw()
PREFIX=tuple(entries(RAW)[:4])
class Tests(unittest.TestCase):
    def test_repair(self):
        for i in (2,10,22):
            fixture=dol(BODY*i+NOP*4+BODY*(22-i))
            p=plan(OWNER,fixture,SIZES,SOURCE,RAW,PREFIX)
            self.assertEqual(p.pc,PCS[i])
            self.assertEqual(p.candidate,OWNER)
            self.assertEqual(p.prefix[-1][1],p.pc)
            self.assertIn('original=23',outcome(RAW,134,OWNER,SIZES,p))
            rows=RAW.splitlines()
            stop=next(j for j,l in enumerate(rows) if l.startswith(f'V420_CB_ENTRY call={p.prefix[-1][0]} '.encode()))
            self.assertIn('blr=1 resume=1',outcome(log(*rows[:stop+1],BLR,RESUME),0,OWNER,SIZES,p))
            with self.assertRaises(ValueError):outcome(log(*rows[:stop]),134,OWNER,SIZES,p)
    def test_reject(self):
        fixture=dol(BODY*22+NOP*4)
        for bad in (OWNER,dol(BODY*21+NOP*8),dol(BODY*22+NOP*3+BODY[-4:]),dol(NOP*4+BODY*22)):
            with self.assertRaises(ValueError):plan(OWNER,bad,SIZES,SOURCE,RAW,PREFIX)
        for bad in (RAW.replace(b'call=34',b'call=35'),RAW.replace(b'resumed=0',b'resumed=1',1),RAW+BEGIN+b'\n'):
            with self.assertRaises(ValueError):plan(OWNER,fixture,SIZES,SOURCE,bad,PREFIX)
        for source in (cpp(PCS[0]),SOURCE+cpp(PCS[-1])):
            with self.assertRaises(ValueError):plan(OWNER,fixture,SIZES,source,RAW,PREFIX)
        for prefix in ((),((0,PCS[1],A+0x1000,0),),tuple(entries(RAW))):
            with self.assertRaises(ValueError):plan(OWNER,fixture,SIZES,SOURCE,RAW,prefix)
if __name__=='__main__':unittest.main()
