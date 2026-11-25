import unittest
from unittest.mock import patch
import audit_v975_second_time as audit
from prepare_v975_second_time import shared_label,patch_existing,render_time
from prepare_v667_si_dispatch import TIME,DISABLE,RESTORE
class SharedTime(unittest.TestCase):
    def test_shared_leaf(self):
        for root in (TIME,DISABLE,RESTORE):
            pc=root;w=0x60000000
            base=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n'
            if root==TIME:
                old=f'    undercover::wii::v922::second_dispatch_before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n'
                legacy=f'    if(!undercover::wii::v922::second_dispatch_active_now()) undercover::wii::v709::before(ctx,0x{pc:08x}u,0x{w:08x}u,2u);\n'
            else:
                old=f'    undercover::wii::v922::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
                legacy=''
            s=base+old+legacy;out=shared_label(s,pc,w,root,False)
            self.assertIn('if(!undercover::wii::v958::active()) '+old.lstrip(),out)
            self.assertIn(f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n',out)
            self.assertLess(out.index('ctx.si_instruction_boundary'),out.index('v958::before'))
            with self.assertRaises(ValueError):shared_label(out,pc,w,root,False)
            with self.assertRaises(ValueError):shared_label(s.replace(old,''),pc,w,root,False)
    def test_guard_upgrade(self):
        s='    undercover::wii::v958::before(ctx,0x80004000u,0x60000000u,true);\n'
        self.assertIn(',false);',patch_existing(s,0x80004000,0x60000000,True,False))
        with self.assertRaises(ValueError):patch_existing(s+s,0x80004000,0x60000000,True,False)
        with self.assertRaises(ValueError):patch_existing('',0x80004000,0x60000000,True,True)
    def test_chained_audit(self):
        p=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=11 handler_instruction_executed=0 boot_verified=0'
        r=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
        rows=[p,r]
        with patch('audit_v967_post_ack.inspect',return_value=('',True)):
            self.assertTrue(audit.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[r],[r,*rows],rows+[b'V958_ACK_INVALID kind=10 stage=4 reason=0 call_reason=0 visits=2']):
                self.assertFalse(audit.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(audit.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
