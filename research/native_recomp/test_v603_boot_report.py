import unittest
from prepare_v603_boot_report import patch_probe,patch_label,INCLUDE,DECL,MI_END,NEXT,MI_NEXT,LRS
from apply_bat_roots_v586 import PAIRS as BAT
from apply_report_table_v594 import pairs
from apply_irq_bootstrap_v475 import rewrite
from audit_v603_boot_report import EVENTS,inspect
from unittest.mock import patch
class Tests(unittest.TestCase):
    def test_probe(self):
        old='\n'.join((INCLUDE,DECL,MI_END))
        out=patch_probe(old)
        self.assertIn(NEXT,out);self.assertIn(MI_NEXT,out)
        self.assertEqual(len(LRS),19);self.assertEqual(len(set(LRS)),19)
        for bad in (old+old,old.replace(MI_END,''),out):
            with self.assertRaises(ValueError):patch_probe(bad)
    def test_labels(self):
        old='loc_80520410: ;\n    // 0x80520410: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('V603 original report label',patch_label(old,0x80520410,0x60000000))
        for bad in (old+old,old.replace('60000000','00000000'),patch_label(old,0x80520410,0x60000000)):
            with self.assertRaises(ValueError):patch_label(bad,0x80520410,0x60000000)
    def test_analyzer_composition(self):
        report=pairs(0x805204e8)
        old='\n'.join(dict.fromkeys([a for a,b in BAT]+[a for a,b in report]))
        out=rewrite(rewrite(old,BAT),report)
        self.assertIn('terminal RFI in exact mapper',out)
        self.assertIn('report target count',out)
        self.assertIn('bat_owner(func_start)',out)
        self.assertIn('report_pc!=(func_start==0x805203c4u)',out)
    def test_audit(self):
        result=b'V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed=1 returned=1 output_backend=0 fallback=0 boot_verified=0'
        seq=EVENTS+[result];self.assertEqual(len(EVENTS),17)
        with patch('audit_v603_boot_report.inspect_mi',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(seq),0)[1])
            for bad in (seq[:-1],seq+seq,seq[:2]+seq[3:],seq[:2]+[seq[3],seq[2]]+seq[4:],seq+[b'V425_HARDWARE_FALLBACK hit=1'],seq[:-1]+[result.replace(b'computed=1',b'computed=2')]):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(seq),116)[1])
        with patch('audit_v603_boot_report.inspect_mi',return_value=('bad',False)):
            self.assertFalse(inspect(b'\n'.join(seq),0)[1])
if __name__=='__main__':unittest.main()
