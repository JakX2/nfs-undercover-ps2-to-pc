import subprocess
import unittest
from test_v559_dsp_stage import (HOST,OS_EXI_ID,A,AR,E,ER,S,SR,D,DR,R,RR,T,TR,O,OR,STAGES as DSP,RESULT as DSP_RESULT,log)
from audit_v574_dsp_sc import STAGES,RESULT
from audit_v575_dsp_sc_frontier import inspect,frontier
SI=OS_EXI_ID+A+[AR]+E+[ER]+S+[SR]+D+[DR]
SRAM=SI+R+[RR]
THREAD=SRAM+T+[TR]
AUDIO=THREAD+O+[OR]
STAGING=AUDIO+DSP+[DSP_RESULT]
GOOD=STAGING+STAGES+[RESULT]
class Tests(unittest.TestCase):
    def test_success_and_prefixes(self):
        rows,ok=inspect(log(GOOD),0)
        self.assertTrue(ok);self.assertIn('si=1 sram=1 thread=1 audio=1 stage=1 sc=1',rows[0])
        for i,stage in enumerate((SI,SRAM,THREAD,AUDIO,STAGING)):
            rows,ok=inspect(log(stage),113)
            self.assertFalse(ok)
            bits=' '.join(f'{n}={int(k<=i)}' for k,n in enumerate(('si','sram','thread','audio','stage','sc')))
            self.assertIn(bits,rows[0])
    def test_no_false_success(self):
        for bad,rc in ((GOOD,124),(GOOD+[RESULT],0),(GOOD+[b'V572_SC_DIRECT_ONLY rejected=1'],0),(GOOD+[b'V425_HARDWARE_FALLBACK hit=1'],0),(STAGING+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
        self.assertIn('sram=0 thread=0',frontier(log(SI+R+[RR,RR]+T+[TR]),108)[0])
        rows,ok=inspect(log(SI+[b'V534_SRAM_INVALID reason=4 stage=5 completed=1']),108)
        self.assertFalse(ok);self.assertEqual(rows[1],'V575_DSP_SC_BOUNDARY phase=sram reason=4 stage=5')
        self.assertIsNone(frontier(log(SI+[b'V534_SRAM_INVALID reason=123456789 stage=5 completed=1']),108)[1])
    def test_launch_contract(self):
        for name in ('run_v572_full_sc_translation.sh','run_v575_dsp_sc_launch.sh'):
            subprocess.run(['bash','-n',str(HOST/name)],check=True)
        s=(HOST/'run_v575_dsp_sc_launch.sh').read_text()
        for item in ('UNDERCOVER_V419_START=1','UNDERCOVER_V574_SC=1','UNDERCOVER_V537_ACR=1','UNDERCOVER_V522_VICLK=0','UNDERCOVER_V512_SI=1','UNDERCOVER_V490_EXI_CONTROLLER=1','UNDERCOVER_V481_IRQ_BANKS=1','UNDERCOVER_V475_IRQ_MMIO=1','write_sram_profile_v536.py','env -i','audit_v575_dsp_sc_frontier.py'):
            self.assertIn(item,s)
        self.assertIn('--run-dsp-sc',(HOST/'run_v572_full_sc_translation.sh').read_text())
if __name__=='__main__':unittest.main()
