import unittest
from unittest.mock import patch
from prepare_v616_irq_enable import patch_probe,patch_label,INCLUDE,DECL,END
from audit_v616_irq_enable import EVENTS,RESULT,inspect
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
    def test_audit(self):
        seq=EVENTS+[RESULT]
        with patch('audit_v616_irq_enable.inspect_arena',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(seq),0)[1])
            for bad in (seq+seq,seq[:-1],seq[:2]+seq[3:],seq[:-1]+[RESULT.replace(b'pending=0',b'pending=1')],seq+[b'V425_HARDWARE_FALLBACK hit=1']):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(seq),119)[1])
if __name__=='__main__':unittest.main()
