import ast,inspect,unittest
from unittest.mock import patch
import prepare_v975_second_time as installer
import audit_v1009_second_callback as audit
import prepare_v1009_second_callback as prefix
class InstallerContract(unittest.TestCase):
    def test_handler_edge_not_shadowed(self):
        # Detect the exact Python local-binding regression that failed after
        # the expensive authenticated full-image preparation in V1001.
        self.assertTrue(callable(installer.handler_edge))
        tree=ast.parse(inspect.getsource(installer.install))
        names={x.id for x in ast.walk(tree) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Store)}
        self.assertNotIn('handler_edge',names)
        self.assertEqual(sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='handler_edge' for x in ast.walk(tree)),1)
    def test_native_hook(self):
        pc=0x80004000;w=0x60000000
        before='loc_80004000: ;\n    // 0x80004000: 60000000\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n'
        old='    undercover::wii::v807::before(ctx,0x80004000u,0x60000000u);\n'
        shared='    undercover::wii::v958::before(ctx,0x80004000u,0x60000000u,false);\n'
        legacy='    if(!undercover::wii::v807::active()) undercover::wii::v768::save_before(ctx,0x80004000u,0x60000000u);\n'
        for src in (before+legacy+old,before+shared+legacy+old):
            out=prefix.patch_label(src,pc,w)
            self.assertEqual(out.count('v958::before('),1)
            self.assertEqual(out.count('++ctx.inst_count;'),1)
            self.assertEqual(out.count('si_instruction_boundary();'),1)
            self.assertIn('if(!undercover::wii::v958::callback_active()) if(!undercover::wii::v807::active())',out)
            self.assertLess(out.index('si_instruction_boundary();'),out.index('v958::before('))
        for src in (before,before+shared.replace('false','true')+old,before+old+old):
            with self.assertRaises(ValueError):prefix.patch_label(src,pc,w)
    def test_audit(self):
        known=b'V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
        marker=audit.RESULT
        with patch.object(audit.old,'inspect',return_value=('V995_SUCCESS_CENSUS rc=0 verified=1 branch=6 admitted=1',True)):
            self.assertTrue(audit.inspect(known+b'\n'+marker,0)[1])
            for data in (known,marker,marker+b'\n'+known,known+b'\n'+marker+b'\n'+marker,known+b'\n'+marker+b'\n'+known,known.replace(b'aligned=1',b'aligned=0')+b'\n'+marker):
                self.assertFalse(audit.inspect(data,0)[1])
        with patch.object(audit.old,'inspect',return_value=('V995_SUCCESS_CENSUS rc=0 verified=1 branch=4 admitted=1',True)):
            self.assertTrue(audit.inspect(b'V981_TRANSFER_FRONTIER',0)[1])
        with patch.object(audit.old,'inspect',return_value=('',False)):
            self.assertFalse(audit.inspect(known+b'\n'+marker,126)[1])
if __name__=='__main__':unittest.main()
