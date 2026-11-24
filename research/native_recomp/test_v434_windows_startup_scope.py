import unittest
from windows_startup_scope_v434 import contract,audit,SCOPES,PREFIXES,HARDWARE_PATCHES,CACHE_PATCHES,OS_HW_PATCHES,OS_IPC_PATCHES,MAX_LOG
from audit_v419_full_start import STAGES as START,RESULT as START_RESULT
from audit_v425_full_hardware import STAGES as HW,RESULT as HW_RESULT
from audit_v428_full_cache import STAGES as CACHE,RESULT as CACHE_RESULT
from audit_v430_full_data import HELPERS,RESULT as DATA_RESULT
from audit_v433_full_os_entry import DB,RESULT as OS_RESULT
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT
from audit_v439_full_os_hardware import STAGES as OS_HW,RESULT as OS_HW_RESULT,COPY
from audit_v444_full_os_arena import STAGES as ARENA,RESULT as ARENA_RESULT
from audit_v446_full_os_ipc import STAGES as IPC,RESULT as IPC_RESULT


def log(lines):return b'\n'.join(lines)+b'\n'
DATA=CACHE+[b'V430_DATA_BEGIN before_nonzero=0']+HELPERS+[DATA_RESULT]
OS=DATA+[b'V433_OS_BEGIN arena_hi_nonzero=1 boot_info_nonzero=0',DB,OS_RESULT]
OS_TIME=OS+TIME+[TIME_RESULT]
OS_HARDWARE=OS_TIME+[b'V439_HW_BEGIN copy=0']+OS_HW+[OS_HW_RESULT]
OS_ARENA=OS_HARDWARE+[b'V444_ARENA_BEGIN boot_path=1 direct_low=0']+ARENA+[ARENA_RESULT]
OS_IPC=OS_ARENA+[b'V446_IPC_BEGIN clamp=0']+IPC+[IPC_RESULT]
LOGS={name:log(lines) for name,lines in (
    ('startup',START+[START_RESULT]),('hardware',HW+[HW_RESULT]),
    ('cache',CACHE+[CACHE_RESULT]),('data',DATA),('os-entry',OS),
    ('os-time',OS_TIME),('os-hardware',OS_HARDWARE),('os-arena',OS_ARENA),('os-ipc',OS_IPC))}


class Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(contract('startup',True),((),'prepare_v419_full_start.py','audit_v419_full_start'))
        self.assertEqual(contract('hardware')[0],HARDWARE_PATCHES)
        for scope in ('cache','data','os-entry','os-time'):
            self.assertEqual(contract(scope)[0],CACHE_PATCHES)
            with self.assertRaises(ValueError):contract(scope,True)
        self.assertEqual(contract('os-hardware'),(OS_HW_PATCHES,'prepare_v439_full_os_hardware.py','audit_v439_full_os_hardware'))
        self.assertEqual(contract('os-arena')[0],OS_HW_PATCHES)
        self.assertEqual(contract('os-ipc')[0],OS_IPC_PATCHES)
        self.assertEqual(OS_HW_PATCHES,('apply_function_root_v443','apply_perf_sprs_v29')+CACHE_PATCHES+('verify_perf_combo_v29','apply_hid4_continuous_v30'))
        self.assertEqual(OS_IPC_PATCHES,OS_HW_PATCHES+('apply_exact_dispatch_v445',))
        for scope in ('os-hardware','os-arena','os-ipc'):
            with self.assertRaises(ValueError):contract(scope,True)
        self.assertEqual(set(LOGS),set(SCOPES))
        for scope in ('', 'bogus', 'CACHE'):
            with self.assertRaises(ValueError):contract(scope)
    def test_all_scope_pairs(self):
        for scope in SCOPES:
            for source,raw in LOGS.items():
                with self.subTest(scope=scope,source=source):
                    self.assertEqual(audit(raw,0,scope)[1],scope==source)
    def test_optional_copy_and_hex_rejection(self):
        prefix=OS_TIME+[b'V439_HW_BEGIN copy=1']+OS_HW[:1]+[COPY]+OS_HW[1:]+[OS_HW_RESULT]
        for scope,tail in (('os-hardware',[]),('os-arena',OS_ARENA[len(OS_HARDWARE):]),('os-ipc',OS_IPC[len(OS_HARDWARE):])):
            good=log(prefix+tail)
            self.assertTrue(audit(good,0,scope)[1])
            self.assertFalse(audit(good.replace(b'V439_HW_STAGE n=10 valid=1',b'V439_HW_STAGE n=a valid=1'),0,scope)[1])
            self.assertFalse(audit(good.replace(COPY+b'\n',b''),0,scope)[1])
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
