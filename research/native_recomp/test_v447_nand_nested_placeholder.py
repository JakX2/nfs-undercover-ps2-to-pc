import unittest
from repair_v447_nand_nested_placeholder import plan,outcome,RepairRejected
from test_v414_nand_resumed_coverage import dol,BODY,A,NOP
from test_v424_nand_aot_placeholder import cpp
from test_v437_nand_restored_frame import entry,log,BEGIN,BLR,RESUME
PCS=[A+16*i for i in range(5)]
SIZES={p:16 for p in PCS}
RAW=log(BEGIN,entry(0,PCS[0],A+0x100),
        b'V437_FRAME_NESTED call=1',entry(1,PCS[1],A+0x104),
        entry(2,PCS[2],A+0x108),b'V437_FRAME_NESTED call=3',
        entry(3,PCS[3],A+0x10c),entry(4,PCS[4],A+0x110))
OWNER=dol(BODY*5)
FIXTURE=dol(BODY*4+NOP*4)
SOURCE=''.join(cpp(p) for p in PCS)
class Tests(unittest.TestCase):
    def test_restore(self):
        p=plan(OWNER,FIXTURE,SIZES,SOURCE,RAW)
        self.assertEqual(p.candidate,OWNER)
        self.assertEqual(p.pc,PCS[-1]);self.assertEqual(p.size,16)
        self.assertNotIn(f'{p.pc:08x}',p.row())
        row=outcome(RAW+BLR+b'\n'+RESUME+b'\n',0,OWNER,SIZES,p)
        self.assertIn('blr=1 resume=1',row);self.assertIn('original=5',row)
        self.assertTrue(row.endswith('restored_entry=1'))
    def test_observed_nop_position_and_changed_suffix(self):
        for index in (2,3,4):
            fixture=dol(BODY*index+NOP*4+BODY*(4-index))
            p=plan(OWNER,fixture,SIZES,SOURCE,RAW)
            self.assertEqual(p.pc,PCS[index])
            self.assertEqual(p.candidate,OWNER)
            self.assertEqual(len(p.prefix),index+1)
            # Native execution after the repaired function may follow a
            # completely different path; never require old stub behavior.
            rows=RAW.splitlines()
            last=next(i for i,l in enumerate(rows) if l.startswith(f'V420_CB_ENTRY call={index} '.encode()))
            new=log(*rows[:last+1],BLR,RESUME)
            self.assertIn('restored_entry=1',outcome(new,0,OWNER,SIZES,p))
            altered=new.replace(f'pc={PCS[index]:08x}'.encode(),f'pc={PCS[0]:08x}'.encode())
            with self.assertRaises(ValueError):outcome(altered,0,OWNER,SIZES,p)
        for index in (0,1):
            fixture=dol(BODY*index+NOP*4+BODY*(4-index))
            with self.assertRaises(ValueError):plan(OWNER,fixture,SIZES,SOURCE,RAW)
    def test_rejection_census(self):
        for raw,source,reason,ordinal,body,dispatch in (
            (RAW.replace(b'call=4',b'call=5'),SOURCE,'entry_order',0,0,0),
            (RAW.replace(f'pc={PCS[-1]:08x}'.encode(),b'pc=80004338'),SOURCE,'entry_range',5,0,0),
            (RAW,cpp(PCS[0]),'aot_entry',5,0,0),
            (RAW,SOURCE.replace(f'func_{PCS[-1]:08X}}}', 'other}'),'aot_entry',5,1,0)):
            with self.assertRaises(RepairRejected) as e:plan(OWNER,FIXTURE,SIZES,source,raw)
            self.assertEqual(e.exception.row(),f'V452_REPAIR_REJECT reason={reason} ordinal={ordinal} body={body} dispatch={dispatch}')
            self.assertNotIn(f'{PCS[-1]:08x}',e.exception.row())
    def test_reject(self):
        for raw in (RAW.replace(b'call=4',b'call=5'),RAW.replace(b'call=4',b'call=3'),RAW+BEGIN+b'\n',RAW.replace(b'resumed=0',b'resumed=1',1)):
            with self.assertRaises(ValueError):plan(OWNER,FIXTURE,SIZES,SOURCE,raw)
        for image in (OWNER,dol(BODY*4+NOP*3+BODY[-4:]),dol(BODY*3+NOP*8)):
            with self.assertRaises(ValueError):plan(OWNER,image,SIZES,SOURCE,RAW)
        for source in (cpp(PCS[0]),SOURCE+cpp(PCS[-1])):
            with self.assertRaises(ValueError):plan(OWNER,FIXTURE,SIZES,source,RAW)
        p=plan(OWNER,FIXTURE,SIZES,SOURCE,RAW)
        with self.assertRaises(ValueError):outcome(RAW.replace(b'call=4',b'call=5'),134,OWNER,SIZES,p)
if __name__=='__main__':unittest.main()
