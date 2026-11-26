import unittest,struct
from prepare_v1260_scheduler_vector import extend,analyzer,patch_label,render,ROOT,SC_SOURCE,SOURCE,TRAMP,DISPATCH,VECTOR,VECTORS,ANALYZE_ROOT,READ
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
class Vector(unittest.TestCase):
    def test_extend(self):
        raw=assemble({ROOT:(0x4e800020,),SC_SOURCE:(0x60000000,)*7},ROOT)
        csv='Name,Location,Size\n'+f'func_{ROOT:08X},{ROOT:08x},4\n'
        table=bytes(range(60))
        out,syms=extend(raw,csv,(0x60000000,)*38,table,(0x60000000,)*20,0x9421fff0)
        self.assertEqual(words_at(out,TRAMP,20),(0x60000000,)*20)
        self.assertEqual(words_at(out,DISPATCH,2),(0x9421fff0,0x4e800020))
        self.assertEqual(words_at(out,SOURCE,38),(0x60000000,)*38)
        self.assertEqual(struct.unpack_from('>I',out,0x64)[0],VECTORS)
        self.assertEqual(out[struct.unpack_from('>I',out,0x1c)[0]:],table)
        self.assertIn(f'func_{TRAMP:08X},{TRAMP:08x},80',syms)
        with self.assertRaises(ValueError):extend(raw,csv,(0,)*37,table,(0,)*20,0)
    def test_hooks(self):
        old='loc_80000500: ;\n    // 0x80000500: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('v1260_before(ctx,0x80000500u,0x60000000u);',patch_label(old,VECTOR,0x60000000))
        with self.assertRaises(ValueError):patch_label(old+old,VECTOR,0x60000000)
        with self.assertRaises(ValueError):patch_label(old,VECTOR,0)
        src=ANALYZE_ROOT+'\n'+READ
        self.assertEqual(analyzer(analyzer(src)),analyzer(src))
        self.assertIn('std::array<uint32_t,38>',render([0]*38,[0]*20,0))
if __name__=='__main__':unittest.main()
