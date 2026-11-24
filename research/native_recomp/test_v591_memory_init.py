import unittest
from prepare_v591_memory_init import patch_probe,patch_label,DECL,END,INCLUDE,SITES,TRAMP
from audit_v591_memory_init import STAGES,RESULT,inspect,mapper_diagnostic,MARKERS
from test_v575_dsp_sc_frontier import GOOD
from audit_v581_dsp_return import STAGES as DSP,RESULT as DSP_RESULT
from test_v559_dsp_stage import log
class Tests(unittest.TestCase):
    def test_patch(self):
        old=INCLUDE+'\n'+DECL+'\n'+END
        new=patch_probe(old)
        self.assertIn('dsp_session.reset()',new)
        self.assertIn('memory_init.begin(cpu)',new)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        for bad in (old+old,new,old.replace(DECL,'')):
            with self.assertRaises(ValueError):patch_probe(bad)
        label='loc_805208F4: ;\n    // 0x805208F4: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('trace_call(0x805208F4, ctx)',patch_label(label,0x805208f4,0x60000000))
        for bad in (label+label,patch_label(label,0x805208f4,0x60000000)):
            with self.assertRaises(ValueError):patch_label(bad,0x805208f4,0x60000000)
        self.assertEqual(len(SITES),12);self.assertEqual(len(TRAMP),2)
    def test_audit(self):
        good=GOOD+DSP+[DSP_RESULT]+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,115),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(good+[b'V591_MI_INVALID reason=1 stage=20'],0),(GOOD+DSP+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
    def test_mapper_diagnostic(self):
        prefix=b'V591_MI_INVALID reason=4 stage=11\n'
        row=b'V620_MI_MAPPER refusal=4096 bat_count=33 msr=32'
        self.assertEqual(mapper_diagnostic(prefix+row,115),row.decode())
        for raw,rc in ((prefix+row,0),(row,115),(prefix+row+b'\n'+row,115),
                       (prefix.replace(b'11',b'12')+row,115),
                       (prefix+row.replace(b'4096',b'0'),115),
                       (prefix+row.replace(b'4096',b'16384'),115),
                       (prefix+row.replace(b'33',b'4294967296'),115),
                       (row+b'\n'+prefix,115),(prefix+row+b' private',115)):
            self.assertIsNone(mapper_diagnostic(raw,rc))
        good=GOOD+DSP+[DSP_RESULT]+STAGES+[RESULT]
        self.assertFalse(inspect(log(good+[row]),0)[1])
        # The report/arena/IRQ parent audits filter by inherited MARKERS.
        # A contradictory refusal must survive that filter.
        filtered=[line for line in log(good+[row]).splitlines() if line.startswith(MARKERS)]
        self.assertIn(row,filtered)
        self.assertFalse(inspect(b'\n'.join(filtered),0)[1])
if __name__=='__main__':unittest.main()
