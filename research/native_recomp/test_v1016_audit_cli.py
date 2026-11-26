import subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import audit_v1015_error_completion as error
import audit_v967_post_ack as post
from audit_second_irq_output_v1016 import EXACT
HERE=Path(__file__).resolve().parent
ACK=b'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=48 reads=3 writes=1 boot_verified=0'
POST=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=130 handler_instruction_executed=0 boot_verified=0'
DETAIL=b'V989_SHARED_DETAIL phase=3 depth=0 started=0 seen=0 post=0 held=1 entries=6 returns=6 msr=2 visits=178'
FAULT=b'V958_ACK_INVALID kind=12 stage=4 reason=0 call_reason=0 visits=178'
SECRET=b'V989_SHARED_DETAIL phase=3 depth=0 started=0 seen=0 post=0 held=1 entries=6 returns=6 msr=2 visits=178 pc=0x80004000'
MODULES=('v958_second_ack','v967_post_ack','v975_second_time','v986_transfer_frontier','v989_shared_time','v995_success_frontier','v1009_second_callback','v1014_second_callback_time','v1015_error_completion')
class CliAudit(unittest.TestCase):
    def test_real_failure_cli(self):
        with tempfile.TemporaryDirectory() as td:
            log=Path(td)/'run.log';log.write_bytes(b'\n'.join((*EXACT,ACK,DETAIL,FAULT,SECRET)))
            for module in MODULES:
                with self.subTest(module=module):
                    run=subprocess.run([sys.executable,str(HERE/f'audit_{module}.py'),str(log),'126'],capture_output=True,timeout=10)
                    self.assertEqual(run.returncode,1,run.stderr)
                    self.assertEqual(run.stderr,b'')
                    rows=run.stdout.splitlines()
                    self.assertIn(ACK,rows);self.assertIn(EXACT[0],rows)
                    self.assertNotIn(SECRET,rows)
                    self.assertNotIn(b'pc=0x80004000',run.stdout)
                    self.assertIn(b'verified=0',rows[-1])
                    if module in MODULES[4:]:self.assertIn(DETAIL,rows)
    def test_positive_cli_wrapper(self):
        # Exercise actual main/output and the V1015 ordering check.
        # Only the upstream pre-ACK proof is substituted here.
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as td:
            log=Path(td)/'run.log';log.write_bytes(b'\n'.join((ACK,POST,error.RESULT)))
            stream=io.StringIO()
            with patch.object(post,'inspect',return_value=('',True)),patch.object(sys,'argv',['audit',str(log),'0']),redirect_stdout(stream):
                self.assertEqual(error.main(),0)
            self.assertIn(error.RESULT.decode(),stream.getvalue())
            self.assertIn('V1015_COMPLETION_CENSUS verified=1 no_response=1 shared_time=0 boot_verified=0',stream.getvalue())
if __name__=='__main__':unittest.main()
