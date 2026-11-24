import unittest
from windows_startup_scope_v434 import contract,audit,SCOPES,PREFIXES,HARDWARE_PATCHES,CACHE_PATCHES,MAX_LOG
from audit_v419_full_start import STAGES as START,RESULT as START_RESULT
from audit_v425_full_hardware import STAGES as HW,RESULT as HW_RESULT
from audit_v428_full_cache import STAGES as CACHE,RESULT as CACHE_RESULT
from audit_v430_full_data import HELPERS,RESULT as DATA_RESULT
from audit_v433_full_os_entry import DB,RESULT as OS_RESULT
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT


def log(lines):return b'\n'.join(lines)+b'\n'
DATA=CACHE+[b'V430_DATA_BEGIN before_nonzero=0']+HELPERS+[DATA_RESULT]
OS=DATA+[b'V433_OS_BEGIN arena_hi_nonzero=1 boot_info_nonzero=0',DB,OS_RESULT]
LOGS=dict(zip(SCOPES,map(log,(START+[START_RESULT],HW+[HW_RESULT],CACHE+[CACHE_RESULT],DATA,OS,OS+TIME+[TIME_RESULT]))))

class Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(contract('startup',True),((),'prepare_v419_full_start.py','audit_v419_full_start'))
        self.assertEqual(contract('hardware')[0],HARDWARE_PATCHES)
        for scope in ('cache','data','os-entry','os-time'):
            self.assertEqual(contract(scope)[0],CACHE_PATCHES)
            with self.assertRaises(ValueError):contract(scope,True)
        for scope in ('', 'bogus', 'CACHE'):
            with self.assertRaises(ValueError):contract(scope)
    def test_all_scope_pairs(self):
        for scope in SCOPES:
            for source,raw in LOGS.items():
                with self.subTest(scope=scope,source=source):
                    self.assertEqual(audit(raw,0,scope)[1],scope==source)
    def test_exit_and_duplicates(self):
        for scope,raw in LOGS.items():
            for rc in (1,124,134,256,0xc0000005,-1,-1073741819):
                self.assertFalse(audit(raw,rc,scope)[1])
            self.assertFalse(audit(raw+raw.splitlines()[-1]+b'\n',0,scope)[1])
            self.assertFalse(audit(log(raw.splitlines()[:-1]),0,scope)[1])
            self.assertTrue(audit(b'private non-marker line\n'+raw,0,scope)[1])
    def test_foreign_markers_and_bounds(self):
        for scope,raw in LOGS.items():
            for prefix in PREFIXES:
                self.assertFalse(audit(raw+prefix+b'UNEXPECTED\n',0,scope)[1])
        with self.assertRaises(ValueError):audit(b'x'*(MAX_LOG+1),0,'startup')
        with self.assertRaises(ValueError):audit(b'',0,'bad')
if __name__=='__main__':unittest.main()
