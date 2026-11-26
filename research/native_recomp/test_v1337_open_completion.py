import unittest
from prepare_v1337_open_completion import corridor,merge,rebuild,ensure_resume,STM,BLR,ROOT,SOURCE,SC_SOURCE,VECTORS
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
import struct
NOP=0x60000000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def bc(pc,dst):return 0x41820000|((dst-pc)&0xfffc)
class Tests(unittest.TestCase):
    def test_resume(self):
        root=0x80004000;pc=root+4
        body=' switch(ctx.pc) {\n case 0x80004004: goto loc_80004004;\n }\n'
        main=' switch(ctx.pc) {\n case 0x80004000: func_80004000(ctx); break;\n }\n'
        fixed,added=ensure_resume(main,body,root,pc)
        self.assertTrue(added)
        self.assertEqual(ensure_resume(fixed,body,root,pc),(fixed,False))
        for m,b in ((fixed.replace('case 0x80004004: func_80004000','case 0x80004004: func_80005000'),body),
                    (fixed+fixed,body),(main,body.replace('loc_80004004','loc_80004008')),(main,'')):
            with self.assertRaises(ValueError):ensure_resume(m,b,root,pc)
    def test_corridor(self):
        a=0x80004000;b=a+0x100
        ws=(NOP,bc(a+4,a+16),NOP,bl(a+12,b))
        self.assertEqual(corridor(a,ws,a,a+12,b),((a,a+4,a+8,a+12),(a+16,)))
        with self.assertRaises(ValueError):corridor(a,ws,a,a+12,b+4)
        with self.assertRaises(ValueError):corridor(a,(BLR,*ws[1:]),a,a+12,b)
    def test_roundtrip(self):
        expanded={ROOT:(BLR,),STM:(NOP,BLR)}
        raw=bytearray(assemble({**expanded,SOURCE:(NOP,)*38,SC_SOURCE:(NOP,)*7},ROOT,max_roots=48))
        for off,v in ((0x1c,len(raw)),(0x64,VECTORS),(0xac,60)):struct.pack_into('>I',raw,off,v)
        image=rebuild(bytes(raw)+bytes(60),expanded)
        for a,ws in expanded.items():self.assertEqual(words_at(image,a,len(ws)),ws)
    def test_merge(self):
        old=(NOP,)*23;new=old+(NOP,)*10;shared={0x80004000:(BLR,)}
        blocks={STM:old+(BLR,),**shared}
        self.assertEqual(merge(blocks,shared,old,new)[STM],new+(BLR,))
        self.assertEqual(blocks[STM],old+(BLR,))
        for bad in ({STM:old+(BLR,)},{**blocks,STM:old},{**blocks,STM+96:(BLR,)}):
            with self.assertRaises(ValueError):merge(bad,shared,old,new)
        with self.assertRaises(ValueError):merge(blocks,shared,old,(BLR,*new[1:]))
if __name__=='__main__':unittest.main()
