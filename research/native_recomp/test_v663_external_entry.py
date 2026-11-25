import unittest
from unittest.mock import patch
from audit_v663_external_entry import inspect,EVENTS,RESULT
from prepare_v663_external_entry import patch_probe,patch_ios,verify_dispatch_tick,HEADER,PROBE,START,CALLBACK,IOS_INCLUDE
class Tests(unittest.TestCase):
    def test_dispatch_tick(self):
        s='        process_pending_callbacks(ctx);\n        uint32_t target = ctx.pc;\n        if ((++ctx.inst_count % 100000) == 0) std::cout << "Dispatcher PC: 0x" << std::hex << target << std::endl;\n        switch (target) {'
        verify_dispatch_tick(s)
        # Real split dispatcher also calls the callback inside its idle path.
        verify_dispatch_tick('          process_pending_callbacks(ctx);\n'+s)
        for x in (s+s,s.replace('++ctx.inst_count','ctx.inst_count'),s.replace('uint32_t target','++ctx.inst_count;\n        uint32_t target')):
            with self.assertRaises(ValueError):verify_dispatch_tick(x)
    def test_failure_marker(self):
        with patch('audit_v663_external_entry.inspect_arena',return_value=('ok',True)):
            rows=EVENTS+[RESULT]
            self.assertTrue(inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(inspect(b'\n'.join(rows+[b'V670_VECTOR_REFUSAL mask=2']),0)[1])
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
