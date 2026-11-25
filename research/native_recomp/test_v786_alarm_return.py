import unittest
from unittest.mock import patch
from prepare_v786_alarm_return import scheduler_hook,patch_ack
from audit_v786_alarm_return import inspect
class Alarm(unittest.TestCase):
    def test_order(self):
        s='loc_80004000: ;\n    // 0x80004000: 60000000\n    ++ctx.inst_count;\n    undercover::wii::v693::before(ctx,0x80004000u,0x60000000u,0,0);\n    ctx.si_instruction_boundary();\n'
        x=scheduler_hook(s,0x80004000,0x60000000,'move')
        self.assertLess(x.index('ctx.si_instruction_boundary'),x.index('v693::before'))
        x=scheduler_hook(s.replace('    undercover::wii::v693::before(ctx,0x80004000u,0x60000000u,0,0);\n',''),0x80004000,0x60000000,'insert')
        self.assertLess(x.index('ctx.si_instruction_boundary'),x.index('v786::before'))
        with self.assertRaises(ValueError):scheduler_hook(s.replace('ctx.si_instruction_boundary();','ctx.gpr[3]=1;'),0x80004000,0x60000000,'move')
    def test_ack(self):
        s=patch_ack('    if(v768::active()&&!v768::returned_active())return v768::poll(c);\nif(v768::observe(a,c))return;')
        self.assertLess(s.index('v786::poll'),s.index('v768::poll'))
        self.assertLess(s.index('v786::observe'),s.index('v768::observe'))
    def test_audit(self):
        base=b'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle=1 irq_lane=1 reads=2 writes=3 follow=2 pending=1 total=80 handler_instruction_executed=0 boot_verified=0'
        a=b'V786_ALARM_ENTRY lane=4 timer=1'
        b=b'V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane=4 timer=1 deferred=1 calls=77 visits=90 polls=1 follow=3 handler_instruction_executed=0 boot_verified=0'
        with patch('audit_v786_alarm_return.transfer',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join((base,a,b)),0)[1])
            for bad in (b.replace(b'calls=77',b'calls=65'),b.replace(b'follow=3',b'follow=0'),b.replace(b'lane=4',b'lane=3')):
                self.assertFalse(inspect(b'\n'.join((base,a,bad)),0)[1])
            self.assertFalse(inspect(b'\n'.join((base,a,b)),126)[1])
if __name__=='__main__':unittest.main()
