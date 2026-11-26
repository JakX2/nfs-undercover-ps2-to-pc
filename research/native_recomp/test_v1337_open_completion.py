import unittest
from prepare_v1337_open_completion import corridor,merge,rebuild,ensure_resume,hook_submit,STM,BLR,ROOT,SOURCE,SC_SOURCE,VECTORS
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
import struct
NOP=0x60000000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def bc(pc,dst):return 0x41820000|((dst-pc)&0xfffc)
class Tests(unittest.TestCase):
    def test_open_return_scope(self):
        from prepare_v1358_open_return import expand_scope
        self.assertEqual(expand_scope([(STM,96),(ROOT,4)],96,136),sorted([(STM,136),(ROOT,4)]))
        for prior,old,new in (([(STM,92)],96,136), ([(STM,96),(STM+100,4)],96,136), ([(STM,96)],92,136), ([(STM,96)],96,132)):
            with self.assertRaises(ValueError):expand_scope(prior,old,new)
    def test_hook_prefix(self):
        pc=0x8051963c
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {NOP:08X}\n'
        trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V625 IPC client return\n'
        tick='    ++ctx.inst_count;\n'
        for prefix in ('',trace):
            s=label+prefix+tick
            patched,found=hook_submit(s,pc,NOP)
            self.assertTrue(found);self.assertTrue(patched.startswith(s))
            self.assertEqual(patched.count('v1344_before'),1)
        for s in (label+trace.replace(f'0x{pc:X}',f'0x{pc+4:X}')+tick,
                  label+'    arbitrary(ctx);\n'+tick,label+tick+label+tick,label):
            with self.assertRaises(ValueError):hook_submit(s,pc,NOP)
        self.assertEqual(hook_submit('other',pc,NOP),('other',False))
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
