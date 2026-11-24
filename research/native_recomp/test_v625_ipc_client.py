import unittest
from unittest.mock import patch
from prepare_v625_ipc_client import patch_probe,patch_return,audit_native,INCLUDE,DECL,END,RETURN
from audit_v625_ipc_client import inspect,STAGES,RESULT
class Tests(unittest.TestCase):
    def test_probe(self):
        old='\n'.join((INCLUDE,DECL,END));s=patch_probe(old)
        self.assertIn('ipc_client.begin(cpu)',s);self.assertIn('UNDERCOVER_V625_IPC',s)
        self.assertEqual(s.count('std::_Exit(0)'),1)
        for bad in (old+old,s,old.replace(END,'')):
            with self.assertRaises(ValueError):patch_probe(bad)
        label=f'loc_{RETURN:X}: ;\n    // 0x{RETURN:08X}: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('V625 IPC client return',patch_return(label,0x60000000))
        for bad in (label+label,patch_return(label,0x60000000),label.replace('60000000','00000000')):
            with self.assertRaises(ValueError):patch_return(bad,0x60000000)
    def test_native(self):
        root=0x805194c4;owner=f'fn_{root:08X}'
        s=f'void {owner}(CPUContext& ctx) {{\nloc_{root:X}: ;\n    // 0x{root:08X}: 60000000\n    ++ctx.inst_count;\n}}\n'
        main=f'case 0x{root:X}: {owner}(ctx); break;\n';exp={root:(root,0x60000000)}
        self.assertEqual(audit_native([s],main,exp),1)
        for ss,mm in ((s+s,main),(s,main+main),(s,main+'case 0x805194C4: return;\n'),
                      (s.replace('++ctx.inst_count;','interpret_step(ctx);'),main),
                      (s.replace(owner,'fn_805194C8'),main),(s.replace('60000000','00000000'),main),
                      (s,main.replace(owner,'func_805194C4'))):
            with self.assertRaises(ValueError):audit_native([ss],mm,exp)
    def test_audit(self):
        rows=STAGES+[RESULT]
        with patch('audit_v625_ipc_client.inspect_irq',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(rows),0)[1])
            for bad in (rows+rows,rows[:-1],rows[:5]+rows[6:],rows[:-1]+[RESULT.replace(b'serviced=0',b'serviced=1')],
                        rows+[b'V425_HARDWARE_FALLBACK hit=1'],rows+[b'V625_IPC_INVALID reason=1 stage=19']):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(rows),120)[1])
if __name__=='__main__':unittest.main()
