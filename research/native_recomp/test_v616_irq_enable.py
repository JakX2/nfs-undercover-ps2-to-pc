import unittest
from unittest.mock import patch
from prepare_v616_irq_enable import patch_probe,patch_label,native_leaf,INCLUDE,DECL,END,ENTRY
from audit_v616_irq_enable import EVENTS,RESULT,inspect
from audit_v613_irq_resume import check as check_isolated
class Tests(unittest.TestCase):
    def test_probe(self):
        old='\n'.join((INCLUDE,DECL,END));out=patch_probe(old)
        self.assertIn('pi_intsr.load(),pi_intmr.load()',out)
        self.assertIn('UNDERCOVER_V616_IRQ',out);self.assertEqual(out.count('std::_Exit(0)'),1)
        for bad in (old+old,out,old.replace(END,'')):
            with self.assertRaises(ValueError):patch_probe(bad)
    def test_label(self):
        s='loc_805265CC: ;\n    // 0x805265CC: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('V616 native IRQ resume',patch_label(s,0x805265cc,0x60000000))
        for bad in (s+s,s.replace('60000000','00000000'),patch_label(s,0x805265cc,0x60000000)):
            with self.assertRaises(ValueError):patch_label(bad,0x805265cc,0x60000000)
    def test_native_leaf_identity(self):
        words=(1,2,3,4,0x4e800020);resume=ENTRY+12
        def source(owner):
            return 'void '+owner+'(CPUContext& ctx) {\n'+''.join(f'loc_{ENTRY+4*i:X}: ;\n    // 0x{ENTRY+4*i:08X}: {w:08X}\n    ++ctx.inst_count;\n' for i,w in enumerate(words))+'}\n'
        for owner in ('func_805265C0','fn_805265C0'):
            s=source(owner);main=f'case 0x{ENTRY:X}: {owner}(ctx); break;\ncase 0x{resume:X}: {owner}(ctx); break;\n'
            self.assertEqual(native_leaf([s],main,resume,words),owner)
            for bad,m in ((s+s,main),(s.replace(owner,'fn_805265C4'),main),(s,main.replace(owner+'(ctx); break;\n', 'fn_805265C4(ctx); break;\n',1)),(s,main+main),(s,main+f'case 0x{resume:X}: return;\n'),(s.replace('++ctx.inst_count;','interpret_step(ctx);',1),main),(s.replace('00000003','00000004',1),main)):
                with self.assertRaises(ValueError):native_leaf([bad],m,resume,words)
    def test_isolated_dispatch(self):
        resume=ENTRY+12
        header=f'#pragma once\ninline constexpr uint32_t Resume=0x{resume:08x}u;\n'
        main=f'case 0x{ENTRY:X}: func_805265C0(ctx); break;\ncase 0x{resume:X}: func_805265C0(ctx); break;\n'
        check_isolated(header,main)
        for bad in (main+main,main.splitlines()[1],main+f'case 0x{resume:X}: return;\n',main.replace('func_805265C0','fn_805265C0')):
            with self.assertRaises(ValueError):check_isolated(header,bad)
        with self.assertRaises(ValueError):check_isolated(header.replace('805265cc','805265d4'),main)
    def test_audit(self):
        seq=EVENTS+[RESULT]
        with patch('audit_v616_irq_enable.inspect_arena',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(seq),0)[1])
            for bad in (seq+seq,seq[:-1],seq[:2]+seq[3:],seq[:-1]+[RESULT.replace(b'pending=0',b'pending=1')],seq+[b'V425_HARDWARE_FALLBACK hit=1']):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(seq),119)[1])
if __name__=='__main__':unittest.main()
