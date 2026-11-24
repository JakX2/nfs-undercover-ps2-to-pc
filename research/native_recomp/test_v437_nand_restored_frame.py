import unittest
from derive_v437_nand_restored_frame import INCLUDE,STATE,SELECT,RESET,OWNED,STOP,GUARD,BEGIN,BLR,RESUME,patch_harness,instrument,inspect
PC=0x80501000;LR=0x804f0e40;RET=PC+56
SOURCE='\n'.join((INCLUDE,STATE,SELECT,RESET,OWNED,STOP,GUARD))
CPP=f'loc_{RET:X}: ;\n    // 0x{RET:08X}: 4E800020\nloc_{LR:X}: ;\n    // 0x{LR:08X}: 60000000\n'
def entry(call,pc,lr):return f'V420_CB_ENTRY call={call} pc={pc:x} lr={lr:x} ew=0 lw=0 em=1 lm=1 resumed=0 sc=1 r3=0'.encode()
def reader(data,pc,n):
    if pc not in (PC,PC+0x100):raise ValueError('missing')
    return data[:n]
def log(*lines):return b'\n'.join(lines)+b'\n'
class Tests(unittest.TestCase):
    def test_patch(self):
        out=patch_harness(SOURCE,PC,LR)
        self.assertIn('v437_frame.active()',out);self.assertIn(STOP,out);self.assertIn(GUARD,out)
        for bad in (out,SOURCE+SOURCE,SOURCE.replace(SELECT,'')):
            with self.assertRaises(ValueError):patch_harness(bad,PC,LR)
    def test_instruction_seams(self):
        out=instrument(CPP,RET,LR,0x60000000)
        self.assertIn('v437_before_return(ctx);',out);self.assertIn('v437_after_return(ctx);',out)
        for bad in (CPP+CPP,CPP.replace('4E800020','60000000'),out):
            with self.assertRaises(ValueError):instrument(bad,RET,LR,0x60000000)
    def test_audit(self):
        raw=log(BEGIN,entry(0,PC,LR),b'V437_FRAME_NESTED call=1',entry(1,PC+0x100,PC+24),BLR,RESUME)
        row=inspect(raw,134,b'abcdefgh',b'abcdefgh',{PC:4,PC+0x100:4},reader)
        self.assertIn('begins=1 blr=1 resume=1 nested=1',row);self.assertIn('original=2',row)
        for bad in (raw+BEGIN,raw.replace(BLR,RESUME),raw.replace(b'call=1',b'call=2',1),raw+RESUME):
            with self.assertRaises(ValueError):inspect(bad,134,b'abcdefgh',b'abcdefgh',{PC:4,PC+0x100:4},reader)
if __name__=='__main__':unittest.main()
