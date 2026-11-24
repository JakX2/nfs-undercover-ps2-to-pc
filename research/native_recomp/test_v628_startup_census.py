import unittest
from test_v575_dsp_sc_frontier import GOOD
from test_v559_dsp_stage import log
import audit_v628_startup_census as a
REPORT=b'V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed=1 returned=1 output_backend=0 fallback=0 boot_verified=0'
ARENA=b'V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros=32768 flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0'
D=GOOD+a.dsp.STAGES+[a.dsp.RESULT]
M=D+a.mi.STAGES+[a.mi.RESULT]
R=M+a.report.EVENTS+[REPORT]
A=R+a.arena.EVENTS+[ARENA]
I=A+a.irq.EVENTS+[a.irq.RESULT]
ALL=I+a.ipc.STAGES+[a.ipc.RESULT]
class Tests(unittest.TestCase):
    def test_complete(self):
        rows,ok=a.inspect(log(ALL),0)
        self.assertTrue(ok)
        self.assertIn('sc=4/4 dsp=5/5 mi=20/20 report=17/17 arena=24/24 irq=4/4 ipc=19/19',rows[1])
        self.assertIn('sc=1 dsp=1 mi=1 report=1 arena=1 irq=1 ipc=1',rows[2])
        self.assertIsNone(rows[3])
    def test_partial(self):
        for i,seq in enumerate((GOOD,D,M,R,A,I)):
            rows,ok=a.inspect(log(seq),124);self.assertFalse(ok)
            bits=' '.join(f'{n}={int(k<=i)}' for k,(n,*_) in enumerate(a.SCOPES))
            self.assertIn(bits,rows[2])
        rows,ok=a.inspect(log(D+a.mi.STAGES[:11]+[b'V591_MI_INVALID reason=4 stage=11',b'V620_MI_MAPPER refusal=16 bat_count=0 msr=32']),115)
        self.assertFalse(ok);self.assertIn('mi=11/20 report=0/17',rows[1])
        self.assertIn('sc=1 dsp=1 mi=0',rows[2])
        self.assertEqual(rows[3],'V628_STARTUP_STOP phase=mi reason=4 stage=11')
        for bad,rc in ((b'V591_MI_INVALID reason=4 stage=11',116),
                       (b'V591_MI_INVALID reason=4 stage=99',115),
                       (b'V591_MI_INVALID reason=0 stage=11',115)):
            self.assertIsNone(a.inspect(log(D+a.mi.STAGES[:11]+[bad]),rc)[0][3])
    def test_refusals(self):
        cases=(ALL+[a.mi.RESULT],ALL+[b'V620_MI_MAPPER refusal=16 bat_count=0 msr=32'],
               ALL+[b'V425_HARDWARE_FALLBACK hit=1'],ALL[:-1],ALL+[a.ipc.RESULT],
               D+a.report.EVENTS+M[len(D):]+[REPORT]+ALL[len(R):],
               ALL+[b'V625_IPC_INVALID reason=1 stage=19'])
        for bad in cases:self.assertFalse(a.inspect(log(bad),0)[1])
        self.assertFalse(a.inspect(log(ALL),124)[1])
        self.assertIsNone(a.inspect(log(D+[b'V591_MI_INVALID reason=4 stage=11']*2),115)[0][3])
        self.assertIsNone(a.inspect(log(D+[b'V625_IPC_INVALID reason=4 stage=1']),120)[0][3])
        with self.assertRaises(ValueError):a.inspect(b'',256)
    def test_launch(self):
        from pathlib import Path
        s=(Path(__file__).parent/'run_v575_dsp_sc_launch.sh').read_text()
        self.assertIn('UNDERCOVER_V625_IPC=1);audit=audit_v628_startup_census.py',s)
        self.assertIn('mapper_diagnostic',s)
if __name__=='__main__':unittest.main()
