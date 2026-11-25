import unittest
from unittest.mock import patch
from prepare_v777_transfer_return import move_hooks,patch_si,patch_ack
from prepare_v672_si_ack_route import patch_si as predecessor
from pathlib import Path
from audit_v777_transfer_return import inspect,HANDOFF
class Transfer(unittest.TestCase):
    def test_order(self):
        hook='    undercover::wii::v768::before(ctx,0x80004000u,0x60000000u);\n'
        s='loc_80004000: ;\n    ++ctx.inst_count;\n'+hook+'    ctx.exi_instruction_boundary();\n    ctx.si_instruction_boundary();\n    ctx.gpr[3]=1;\n'
        out,n=move_hooks(s);self.assertEqual(n,1)
        self.assertLess(out.index('ctx.si_instruction_boundary()'),out.index(hook))
        self.assertLess(out.index(hook),out.index('ctx.gpr[3]=1;'))
        for bad in (s.replace('    ctx.si_instruction_boundary();\n',''),s.replace('    ctx.exi_instruction_boundary();\n','    ctx.gpr[3]=0;\n')):
            with self.assertRaises(ValueError):move_hooks(bad)
    def test_si(self):
        host=Path(__file__).parent
        s=patch_si(predecessor((host/'wii_si_binding_v512.h').read_text()))
        self.assertIn('SiTickBinding::configuration',s)
        self.assertIn('si_transfer_device.write',s)
        self.assertIn('else si_completion_ack_trace.write',s)
        self.assertIn('return si_completion_ack_trace.read',s)
        self.assertIn('v768::handler_return',' '.join(patch_ack('    if(!si_completion_ack_trace.before(pc,word))reject(3);').split()))
    def test_audit(self):
        time=b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=43 handler_return=0 boot_verified=0'
        entry=b'V768_TRANSFER_ENTRY channel=1 type=1 idle=1'
        result=b'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle=1 irq_lane=2 reads=2 writes=3 follow=3 pending=0 total=120 handler_instruction_executed=0 boot_verified=0'
        with patch('audit_v777_transfer_return.time',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join((time,entry,HANDOFF,result)),0)[1])
            self.assertTrue(inspect(b'\n'.join((time,entry,HANDOFF,result.replace(b'follow=3 pending=0',b'follow=2 pending=1'))),0)[1])
            for bad in ((time,entry,result),(time,HANDOFF,entry,result),(time,entry,HANDOFF,result,result),(time,entry,HANDOFF,result.replace(b'pending=0',b'pending=1'))):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join((time,entry,HANDOFF,result)),126)[1])
if __name__=='__main__':unittest.main()
