import unittest
from unittest.mock import patch
from audit_v663_external_entry import inspect,EVENTS,RESULT
from prepare_v663_external_entry import (patch_probe,patch_ios,verify_dispatch_tick,
    LEGACY_DISPATCH_DIAG,NATIVE_DISPATCH_DIAG,HEADER,PROBE,START,CALLBACK,IOS_INCLUDE)
class Tests(unittest.TestCase):
    def test_dispatch_tick(self):
        def wrapper(diag,native=False):
            return ((('    uint64_t last_dispatch_diagnostic_count = 0;\n')
                     if native else '')+
                    '        process_pending_callbacks(ctx);\n'
                    '        uint32_t target = ctx.pc;\n'+diag+
                    '\n        switch (target) {')
        old=wrapper(LEGACY_DISPATCH_DIAG)
        current=wrapper(NATIVE_DISPATCH_DIAG,True)
        for s in (old,current):
            verify_dispatch_tick(s)
            # Pinned split dispatcher also calls callbacks in its idle path.
            verify_dispatch_tick('          process_pending_callbacks(ctx);\n'+s)
        for bad in (old+old,current+current,
                    old.replace('++ctx.inst_count','ctx.inst_count'),
                    current.replace('ctx.inst_count &&','++ctx.inst_count &&'),
                    current.replace('last_dispatch_diagnostic_count = 0','other_counter = 0'),
                    current.replace('last_dispatch_diagnostic_count = ctx.inst_count','last_dispatch_diagnostic_count = 0'),
                    current.replace('uint32_t target','++ctx.inst_count;\n        uint32_t target'),
                    current.replace('switch (target)', 'switch (ctx.pc)'),
                    old.replace('        switch (target)',NATIVE_DISPATCH_DIAG+'\n        switch (target)'),
                    old.replace('        process_pending_callbacks(ctx);',''),
                    current.replace('        process_pending_callbacks(ctx);','')):
            with self.subTest(bad=bad[-90:]),self.assertRaises(ValueError):
                verify_dispatch_tick(bad)
        with self.assertRaises(ValueError):verify_dispatch_tick(b'raw not decoded')
    def test_failure_marker(self):
        with patch('audit_v663_external_entry.inspect_arena',return_value=('ok',True)):
            rows=EVENTS+[RESULT]
            self.assertTrue(inspect(b'\n'.join(rows),0)[1])
            for bad in (b'V670_VECTOR_REFUSAL mask=2',b'V678_DISPATCH_REFUSAL mask=256 gpr_mask=2147483648'):
                self.assertFalse(inspect(b'\n'.join(rows+[bad]),0)[1])
    def test_patch(self):
        s='\n'.join((HEADER,PROBE,START))
        out=patch_probe(s)
        self.assertIn('v663::observe(addr,cpu)',out)
        self.assertIn('v663::begin(cpu,irq_cause,irq_mask)',out)
        self.assertIn(START,out)
        for x in (out,s+s,s.replace(START,'')):
            with self.assertRaises(ValueError):patch_probe(x)
        t=IOS_INCLUDE+'\n'+CALLBACK
        self.assertIn('return undercover::wii::v663::poll(ctx);',patch_ios(t))
        with self.assertRaises(ValueError):patch_ios(t+t)
if __name__=='__main__':unittest.main()
