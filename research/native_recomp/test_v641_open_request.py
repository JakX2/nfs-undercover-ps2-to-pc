import unittest
from prepare_v641_open_request import patch_probe,patch_ios,patch_sc,INCLUDE,DECL,RESULT,IOS_INC,IOS_HOOK,OLD_SC
from test_v628_startup_census import ALL,log
from audit_v629_stm_open import STAGES
from audit_v641_open_request import inspect,EVENTS,RESULT as OPEN_RESULT
STM=b'V629_STM_RESULT entry=1 open=1 pathname=1 mode=0 native_transport=1 serviced=0 actual_ios=0 fallback=0 boot_verified=0'
class Tests(unittest.TestCase):
    def test_seams(self):
        probe=INCLUDE+'\n'+DECL+'\n'+RESULT
        self.assertIn('ipc_client.heap_size()',patch_probe(probe))
        self.assertIn('v641::active=true',patch_probe(probe))
        ios=patch_ios(IOS_INC+'\n'+IOS_HOOK)
        self.assertLess(ios.index('v641::try_sc'),ios.index('v609::try_sc'))
        src='loc_805222E8: ;\n    // 0x805222E8: 44000002\n'+OLD_SC+'    ++ctx.inst_count;\n'
        self.assertIn('ctx.pc = 0x805222E8',patch_sc(src))
        for f,s in ((patch_probe,probe),(patch_ios,IOS_INC+'\n'+IOS_HOOK),(patch_sc,src)):
            for bad in (s+s,''):
                with self.assertRaises(ValueError):f(bad)
    def test_audit(self):
        good=ALL+STAGES+[STM]+EVENTS+[OPEN_RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad in (good[:-1],good+[OPEN_RESULT],good+[STM],good+[b'V425_HARDWARE_FALLBACK hit=1'],ALL+EVENTS+[OPEN_RESULT]):
            self.assertFalse(inspect(log(bad),0)[1])
        self.assertFalse(inspect(log(good),122)[1])
        # A verified complete report is not a completed STM/open proof.
        from audit_v603_boot_report import EVENTS as report_events
        stop=next(i for i,x in enumerate(ALL) if x==report_events[0])
        rows,ok=inspect(log(ALL[:stop]+report_events[:4]+[b'V603_REPORT_INVALID reason=8 stage=2 reports=3 getters=0']),116)
        self.assertFalse(ok)
        self.assertIn('mi=20/20 report=4/17',rows[1])
        self.assertIn('stm=0 events=0/11 verified=0',rows[-1])
        # An open request with a skipped vector or a duplicate stage cannot
        # consume a preceding complete-image STM proof as its own success.
        for bad in (EVENTS[:7]+EVENTS[8:],EVENTS[:8]+EVENTS[7:]):
            self.assertFalse(inspect(log(ALL+STAGES+[STM]+bad+[OPEN_RESULT]),0)[1])
        self.assertIn('events=3/11',inspect(log(ALL+STAGES+[STM]+EVENTS[:3]+[b'V641_OPEN_INVALID reason=3 stage=3']),122)[0][-1])
if __name__=='__main__':unittest.main()
