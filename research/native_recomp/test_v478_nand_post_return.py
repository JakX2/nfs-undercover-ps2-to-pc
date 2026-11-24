import struct
import unittest
import tempfile
from pathlib import Path
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
    def test_diagnosis(self):
        row=diagnosis(RAW,HARNESS)
        self.assertIn('guard=frontier',row)
        self.assertIn('stop=1 stop_calls=44 owner=1 selected=0 parent=0',row)
        self.assertIn('exit=0 exit_calls=0',row)
        with_exit=RAW+b'V410_NAND_GUEST_RUN_EXIT calls=44 kind=1 running=0 mapped=1 matched_stop=1 v390=1\n'
        self.assertIn('exit=1 exit_calls=44 kind=1 running=0 mapped=1 matched=1 post_ack=1',diagnosis(with_exit,HARNESS))
        private=RAW.replace(b'what():  V402 extended original guest frontier incomplete',b'what():  private address 0x81234567')
        self.assertIn('guard=unknown id=0000',diagnosis(private,HARNESS))
        self.assertNotIn('81234567',diagnosis(private,HARNESS))
        for bad in (RAW+b'V404_NAND_EXTENDED_STOP calls=44 owner=1 selected_return=0 parent_return=0\n',
                    RAW+b'V410_NAND_GUEST_RUN_EXIT malformed\n'):
            with self.assertRaises(ValueError):diagnosis(bad,HARNESS)
    def test_source_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            msg='public guard [specific]'
            harness=HARNESS+'\ncheck(false,"'+msg+'");'
            raw=RAW.replace(b'what():  V402 extended original guest frontier incomplete',('what():  '+msg).encode())
            (root/'derive_v100.py').write_text('first\ncheck(false,"'+msg+'");\n')
            (root/'test_v100.py').write_text('"'+msg+'"')
            names=['derive_v100.py','test_v100.py','../private.cpp']
            row=source_provenance(raw,harness,root,names)
            self.assertIn('matches=1 file=derive_v100.py line=2 unique=1',row)
            self.assertNotIn(msg,row)
            (root/'derive_v101.py').write_text('"'+msg+'"')
            self.assertIn('matches=2 file=none line=0 unique=0',source_provenance(raw,harness,root,names+['derive_v101.py']))
            rows=source_candidates(raw,harness,root,names+['derive_v101.py'])
            self.assertEqual(len(rows),2)
            self.assertIn('n=1 total=2 file=derive_v100.py line=2',rows[0])
            self.assertIn('n=2 total=2 file=derive_v101.py line=1',rows[1])
            self.assertNotIn(msg,' '.join(rows))
            private=raw.replace(msg.encode(),b'private address 0x81234567')
            self.assertEqual(source_candidates(private,harness,root,names),())
            self.assertIn('id=0000 matches=0 file=none line=0 unique=0',source_provenance(private,harness,root,names))
    def test_ack_history(self):
        harness=HARNESS+'\ncheck(false,"'+ACK_GUARD+'");'
        prefix=(b'V389_NAND_FLAG_ACK before=1 wrote=1 cleared=1 down=1 y1=1 guest=1 registered=1\n'
                b'V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=1 context=0\n'
                b'V388_NAND_BOUNDED_TRIAL kind=1 calls=44 stopped=1 completed=1\n'
                b'V389_NAND_FLAG_TRIAL y1=1 flag=1 completed=0\n')
        raw=prefix+RAW.replace(b'V402 extended original guest frontier incomplete',ACK_GUARD.encode())
        self.assertIn('stale_candidate=1',ack_history(raw,harness))
        for bad in (raw.replace(b'down=1',b'down=0'),raw.replace(b'masked=1',b'masked=0'),
                    raw.replace(b'stopped=1 completed=1',b'stopped=0 completed=0'),
                    raw.replace(ACK_GUARD.encode(),b'unrelated failure'),RAW):
            self.assertIn('stale_candidate=0',ack_history(bad,harness))
        with self.assertRaises(ValueError):ack_history(prefix+raw,harness)
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
