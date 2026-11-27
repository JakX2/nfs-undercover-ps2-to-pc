#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_path import first_path,const
from audit_formatter_partial_copy import store_shape,copied_cells
B=0x80001000;T=0x80002000;SP=-160;FRAME=48;S=SP-FRAME;ORIGIN=S+8;DEST=S+16
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def x(xo,rt,ra,rb):return (31<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)
class PartialCopy(unittest.TestCase):
    def probe(self,body,*,admit=True,low=False,extra=None):
        gp=[('reg',r) for r in range(32)];gp[1]=('stack',S)
        lr=const(B-4)
        mem={S+i:('part',('stack',SP),4,i) for i in range(4)}
        for i,b in enumerate((B-4).to_bytes(4,'big')):mem[SP+4+i]=('byte',b)
        a=ORIGIN+2 if low else ORIGIN
        mem.update({a:('byte',0x12),a+1:('byte',0x34)})
        if extra:mem.update(extra)
        ws=tuple(body)+(bl(B+4*len(body),T),)
        state=(tuple(gp),mem,{},None,lr,FRAME,frozenset())
        opts=dict(partial_origin=(ORIGIN,4),entry_lr=lr) if admit else {}
        return first_path(B,ws,{}, {},(),SP,start=B,resume=state,details=True,**opts)
    def test_default_refusal(self):
        with self.assertRaisesRegex(ValueError,'stack read provenance'):self.probe([d(32,3,1,8)],admit=False)
    def test_full_copy_and_reload(self):
        r=self.probe([d(32,3,1,8),d(36,3,1,16),d(32,4,1,16)])
        expected=(('byte',0x12),('byte',0x34),('uninitialized',ORIGIN+2),('uninitialized',ORIGIN+3))
        self.assertEqual(r[5][3],('partial',expected))
        self.assertEqual(r[5][4],r[5][3])
        self.assertEqual(tuple(r[6][DEST+i] for i in range(4)),expected)
        self.assertEqual(copied_cells(r[6],ORIGIN),2)
        self.assertNotIn(ORIGIN+2,r[6])
    def test_narrow_copy(self):
        r=self.probe([d(32,3,1,8),d(44,3,1,16),d(40,4,1,16)])
        self.assertEqual(r[5][4],('partial',(('byte',0),('byte',0),('uninitialized',ORIGIN+2),('uninitialized',ORIGIN+3))))
        self.assertEqual(copied_cells(r[6],ORIGIN),2)
        r=self.probe([d(32,3,1,8),d(44,3,1,16),d(40,4,1,16)],low=True)
        self.assertEqual(r[5][4],const(0x1234))
        self.assertEqual(copied_cells(r[6],ORIGIN),0)
    def test_no_new_unknown_bytes(self):
        with self.assertRaisesRegex(ValueError,'stack read provenance'):self.probe([d(32,3,1,8),d(32,4,1,16)])
    def test_unknown_pointer_and_compare(self):
        for body in ([d(32,3,1,8),d(32,4,3)], [d(32,3,1,8),d(11,0,3)]):
            with self.assertRaisesRegex(ValueError,'pointer provenance|unknown value'):self.probe(body)
    def test_protected_write(self):
        with self.assertRaisesRegex(ValueError,'protected stack write'):self.probe([d(32,3,1,8),d(36,3,1,0)])
    def test_known_overwrite_kills_copy(self):
        r=self.probe([d(32,3,1,8),d(36,3,1,16),d(14,4,0,9),d(36,4,1,16),d(32,5,1,16)])
        self.assertEqual(r[5][5],const(9));self.assertEqual(copied_cells(r[6],ORIGIN),0)
    def test_store_shape(self):
        self.assertEqual(store_shape(d(36,3,1),3),(4,1,0))
        self.assertEqual(store_shape(d(44,4,3),3),(2,0,1))
        self.assertEqual(store_shape(x(151,3,1,3),3),(4,1,1))
        self.assertEqual(store_shape(d(38,3,0),0),(1,0,0))
        with self.assertRaises(ValueError):store_shape(d(32,3,1),3)
if __name__=='__main__':unittest.main(verbosity=2)
