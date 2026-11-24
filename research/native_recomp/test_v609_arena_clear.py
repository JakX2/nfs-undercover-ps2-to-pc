import unittest
from unittest.mock import patch
from prepare_v609_arena_clear import patch_probe,patch_ios,patch_label,native_zero,INCLUDE,DECL,END,HOOK_NEW,IOS_INCLUDE,LANES
from audit_v609_arena_clear import EVENTS,inspect
class Tests(unittest.TestCase):
    def test_composition(self):
        old='\n'.join((INCLUDE,DECL,END));out=patch_probe(old)
        self.assertIn('v609::enable()',out);self.assertIn('v609::vector_trace',out)
        self.assertEqual(out.count('std::_Exit(0)'),1)
        for bad in (old+old,out,old.replace(END,'')):
            with self.assertRaises(ValueError):patch_probe(bad)
        old=IOS_INCLUDE+'\n'+HOOK_NEW;out=patch_ios(old)
        self.assertLess(out.index('v609::try_sc'),out.index('v574::try_sc'))
        self.assertEqual(len(set(s for lane in LANES for s,p in lane)),14)
    def test_native_label(self):
        old='loc_80522360: ;\n    // 0x80522360: 7C001FEC\n    ++ctx.inst_count;\n    ctx.guest_dcbz(ctx.gpr[3]);\n'
        self.assertTrue(native_zero(old,0x80522360,0x7c001fec))
        self.assertIn('V609 original arena return',patch_label(old,0x80522360,0x7c001fec))
        for bad in (old+old,old.replace('guest_dcbz','micro_interpret'),old.replace('7C001FEC','60000000')):
            with self.assertRaises(ValueError):native_zero(bad,0x80522360,0x7c001fec)
    def test_audit(self):
        result=b'V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros=32768 flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0'
        seq=EVENTS+[result];self.assertEqual(len(EVENTS),24)
        with patch('audit_v609_arena_clear.inspect_report',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(seq),0)[1])
            for bad in (seq+seq,seq[:-1],seq[:10]+seq[11:],seq[:-1]+[result.replace(b'zeros=32768',b'zeros=1')],seq+[b'V425_HARDWARE_FALLBACK hit=1']):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(seq),117)[1])
if __name__=='__main__':unittest.main()
