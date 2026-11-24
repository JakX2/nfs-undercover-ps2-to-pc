import struct
import unittest
from derive_v478_nand_post_return import *
from test_v414_nand_resumed_coverage import A,BODY,dol
from test_v424_nand_aot_placeholder import cpp
from test_v437_nand_restored_frame import entry,log
PCS=[A+16*i for i in range(25)]
SIZES={p:16 for p in PCS}
# Put the actual call inside the selected original caller.
CALLER=PCS[0];TARGET=PCS[-1];LR=CALLER+8
WORD=0x48000001|((TARGET-(LR-4))&0x03fffffc)
BODY0=BODY[:4]+struct.pack('>I',WORD)+BODY[8:]
OWNER=dol(BODY0+BODY*24)
CPP=''.join(cpp(p) for p in PCS)
HARNESS='\n'.join((STATE,RESET,OWN,STOP,GUARD))
def raw():
    order=PCS[:2]+[PCS[1]]*20+PCS[2:]
    lines=[BEGIN]
    for i,pc in enumerate(order):
        if i in (1,2):lines.append(f'V437_FRAME_NESTED call={i}'.encode())
        if i==40:lines.extend((BLR,RESUME))
        lines.append(entry(i,pc,LR if i==44 else A+0x1000).replace(b'lm=1',b'lm=0') if i==44 else entry(i,pc,A+0x1000))
    lines.extend((b'V404_NAND_EXTENDED_STOP calls=44 owner=1 selected_return=0 parent_return=0',
                  b"terminate called after throwing an instance of 'std::runtime_error'",
                  b'  what():  V402 extended original guest frontier incomplete'))
    return log(*lines)
RAW=raw()
class Tests(unittest.TestCase):
    def test_exact_edge(self):
        p=terminal(OWNER,OWNER,SIZES,CPP,HARNESS,RAW)
        self.assertTrue(p.ready);self.assertEqual(p.pc,TARGET)
        updated=patch(HARNESS,p)
        self.assertIn('v396_calls==43u',updated)
        self.assertIn(STOP,updated);self.assertIn(GUARD,updated)
        good=RAW.replace(b'V420_CB_ENTRY call=44 ',MARK+b'\nV420_CB_ENTRY call=44 ')
        self.assertIn('continued=1',outcome(good,134,OWNER,OWNER,SIZES,p))
        for bad in (RAW,good+MARK+b'\n',good.replace(b'call=44 pc=',b'call=45 pc=')):
            with self.assertRaises(ValueError):outcome(bad,134,OWNER,OWNER,SIZES,p)
    def test_other_stop_preserved(self):
        for raw in (RAW.replace(b'owner=1',b'owner=0'),
                    RAW.replace(b'what():  V402 extended original guest frontier incomplete',b'what():  unrelated runtime failure'),
                    RAW.replace(b'lm=0 resumed=0 sc=1 r3=0',b'lm=1 resumed=0 sc=1 r3=0')):
            p=terminal(OWNER,OWNER,SIZES,CPP,HARNESS,raw)
            self.assertFalse(p.ready)
            with self.assertRaises(ValueError):patch(HARNESS,p)
        for bad in (HARNESS+HARNESS,HARNESS.replace(OWN,'missing')):
            with self.assertRaises(ValueError):patch(bad,terminal(OWNER,OWNER,SIZES,CPP,HARNESS,RAW))
if __name__=='__main__':unittest.main()
