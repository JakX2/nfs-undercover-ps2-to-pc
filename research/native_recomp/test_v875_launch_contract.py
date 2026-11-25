import subprocess,unittest
from pathlib import Path
HERE=Path(__file__).parent
TRANS='run_v572_full_sc_translation.sh'
LAUNCH='run_v575_dsp_sc_launch.sh'
ROWS=(
    ('callback-frontier','v836_callback_frontier', (0,0,0,0,0),()),
    ('wireless-wrapper','v848_wireless_wrapper',(1,0,0,0,0),('UNDERCOVER_V847_WIRELESS=1',)),
    ('wireless-write','v862_wireless_write',(1,1,0,0,0),('UNDERCOVER_V847_WIRELESS=1','UNDERCOVER_V861_WIRELESS_WRITE=1')),
    ('callback-return','v852_callback_return',(1,0,1,0,0),('UNDERCOVER_V847_WIRELESS=1','UNDERCOVER_V850_CALLBACK_RETURN=1')),
    ('combined-callback','v864_combined_callback',(1,1,1,1,0),('UNDERCOVER_V847_WIRELESS=1','UNDERCOVER_V861_WIRELESS_WRITE=1','UNDERCOVER_V850_CALLBACK_RETURN=1')),
    ('handler-suffix','v870_handler_suffix',(1,1,1,1,1),('UNDERCOVER_V847_WIRELESS=1','UNDERCOVER_V861_WIRELESS_WRITE=1','UNDERCOVER_V850_CALLBACK_RETURN=1','UNDERCOVER_V868_HANDLER_SUFFIX=1')),
)
class LaunchPlan(unittest.TestCase):
    def run_plan(self,script,mode):
        return subprocess.run(['bash',str(HERE/script),'--describe-mode',mode],capture_output=True,text=True,timeout=5)
    def test_translation(self):
        for name,_,bits,_ in ROWS:
            for action in ('run','prepare'):
                mode=f'--{action}-si-{name}';r=self.run_plan(TRANS,mode)
                self.assertEqual(r.returncode,0,r.stderr)
                expected=f'V875_TRANSLATION_PLAN requested={mode} base=--{action}-irq-enable target='+ (f'irq-si-{name}' if action=='run' else 'none')
                expected+=' '+' '.join(f'{k}={v}' for k,v in zip(('wrapper','write','callback','combined','handler'),bits))
                self.assertEqual(r.stdout.strip(),expected)
    def test_launch(self):
        predecessors=('UNDERCOVER_V581_DSP=1','UNDERCOVER_V591_MI=1','UNDERCOVER_V616_IRQ=1','UNDERCOVER_V663_EXTERNAL=1',
          'UNDERCOVER_V667_SI_DISPATCH=1','UNDERCOVER_V672_SI_ACK=1','UNDERCOVER_V726_HANDLER_RETURN=1','UNDERCOVER_V768_TRANSFER_PREFIX=1',
          'UNDERCOVER_V777_TRANSFER_RETURN=1','UNDERCOVER_V786_ALARM_RETURN=1','UNDERCOVER_V807_CALLBACK_PREFIX=1',
          'UNDERCOVER_V813_CALLBACK_TIME=1','UNDERCOVER_V831_CALLBACK_FRONTIER=1')
        new_flags=set(f for _,_,_,flags in ROWS for f in flags)
        for name,audit,_,flags in ROWS:
            mode='irq-si-'+name;r=self.run_plan(LAUNCH,mode)
            self.assertEqual(r.returncode,0,r.stderr)
            head=f'V875_LAUNCH_PLAN requested={mode} base=irq-enable-return audit=audit_{audit}.py flags='
            self.assertTrue(r.stdout.startswith(head),r.stdout)
            tokens=r.stdout[len(head):].split()
            self.assertEqual(len(tokens),len(set(tokens)))
            self.assertTrue(set(predecessors).issubset(tokens))
            self.assertEqual(set(tokens)&new_flags,set(flags))
    def test_legacy(self):
        for script,mode,target in ((TRANS,'--run-dsp-sc','target=dsp-sc'),(TRANS,'--prepare-dsp-sc','target=none'),
                (TRANS,'--run-si-alarm','target=irq-si-alarm'),(LAUNCH,'irq-si-alarm','audit=audit_v786_alarm_return.py')):
            r=self.run_plan(script,mode);self.assertEqual(r.returncode,0);self.assertIn(target,r.stdout)
    def test_invalid(self):
        for script in (TRANS,LAUNCH):
            for mode in ('invalid','--describe-mode','../../test',''):
                r=self.run_plan(script,mode);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'')
if __name__=='__main__':unittest.main()
