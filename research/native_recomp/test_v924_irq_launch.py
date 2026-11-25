import os,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).parent
FLAGS=('UNDERCOVER_RUN_V919_HANDLER_EPILOGUE','UNDERCOVER_RUN_V920_HANDLER_RETURN','UNDERCOVER_RUN_V921_CAPTURE_JOIN','UNDERCOVER_RUN_V922_IRQ_RETURN')
class ReturnPlan(unittest.TestCase):
    def launch(self,flags):
        env={k:v for k,v in os.environ.items() if k not in FLAGS}
        env.update({k:'1' for k in flags})
        return subprocess.run(['bash',str(HERE/'run_v575_dsp_sc_launch.sh'),'--describe-mode','irq-si-handler-suffix'],env=env,capture_output=True,text=True,timeout=5)
    def test_prefix(self):
        audits=('v870_handler_suffix','v919_handler_epilogue','v920_handler_return','v921_capture_join','v922_irq_return')
        for i,a in enumerate(audits):
            p=self.launch(FLAGS[:i]);self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('audit=audit_'+a+'.py',p.stdout)
            for f in ('UNDERCOVER_V919_HANDLER_EPILOGUE=1','UNDERCOVER_V920_HANDLER_RETURN=1','UNDERCOVER_V751_CAPTURE=1')[:min(i,3)]:
                self.assertIn(f,p.stdout)
    def test_no_predecessor(self):
        for i in range(1,4):
            p=self.launch((FLAGS[i],));self.assertEqual(p.returncode,2,p.stdout)
if __name__=='__main__':unittest.main()
