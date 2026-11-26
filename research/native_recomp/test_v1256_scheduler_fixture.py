import unittest
from make_v1256_scheduler_fixture import extend,analyzer,ROOT,SOURCE,SELECT,ALLOWED,FORBIDDEN,BLR,ANALYZE_ROOT,READ,SCANNER
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
class Scheduler(unittest.TestCase):
    def test_merge(self):
        native={pc:(0x60000000,BLR) for pc in ALLOWED};native[SELECT]=(0x60000000,0x60000000,BLR)
        stops={pc:(0x60000000,) for pc in FORBIDDEN}
        raw=assemble({ROOT:(BLR,),SELECT:(native[SELECT][0],BLR),SOURCE:(0x60000000,)*7},ROOT)
        csv='Name,Location,Size\n'+f'func_{ROOT:08X},{ROOT:08x},4\nfunc_{SELECT:08X},{SELECT:08x},8\n'
        image,syms=extend(raw,csv,native,stops)
        for pc,ws in native.items():self.assertEqual(words_at(image,pc,len(ws)),ws)
        for pc,ws in stops.items():self.assertEqual(words_at(image,pc,2),ws+(BLR,))
        self.assertIn(f'func_{SELECT:08X},{SELECT:08x},12',syms)
        with self.assertRaises(ValueError):extend(raw,csv,{**native,SELECT:(BLR,)},stops)
    def test_analyzer(self):
        native={pc:(BLR,) for pc in ALLOWED};stops={pc:(BLR,) for pc in FORBIDDEN}
        src='\n'.join((ANALYZE_ROOT,READ,SCANNER))
        out=analyzer(src,native,stops)
        self.assertEqual(analyzer(out,native,stops),out)
        for pc in (*ALLOWED,*FORBIDDEN):self.assertIn(f'func.start_address==0x{pc:08x}u',out)
        with self.assertRaises(ValueError):analyzer(src,{},stops)
    def test_explicit_limit(self):
        blocks={ROOT+4*i:(BLR,) for i in range(33)}
        with self.assertRaises(ValueError):assemble(blocks,ROOT)
        self.assertEqual(words_at(assemble(blocks,ROOT,max_roots=48),ROOT,1),(BLR,))
        with self.assertRaises(ValueError):assemble(blocks,ROOT,max_roots=49)
if __name__=='__main__':unittest.main()
