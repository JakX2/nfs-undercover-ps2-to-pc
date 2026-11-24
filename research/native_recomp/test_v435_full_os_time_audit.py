import unittest
from audit_v430_full_data import CACHE,HELPERS,RESULT as DATA_RESULT
from audit_v433_full_os_entry import DB,RESULT as OS_RESULT
from audit_v435_full_os_time import STAGES,RESULT,inspect,MAX_LOG
PREFIX=CACHE+[b'V430_DATA_BEGIN before_nonzero=4']+HELPERS+[DATA_RESULT,b'V433_OS_BEGIN arena_hi_nonzero=1 boot_info_nonzero=0',DB,OS_RESULT]
def log(lines):return b'\n'.join(lines)+b'\n'
class Tests(unittest.TestCase):
    def test_pass_and_partial(self):
        self.assertTrue(inspect(log(PREFIX+STAGES+[RESULT]),0)[1])
        for i in range(7):
            row,ok=inspect(log(PREFIX+STAGES[:i]),87);self.assertFalse(ok);self.assertIn(f'stages={i}',row)
    def test_reject(self):
        good=PREFIX+STAGES+[RESULT]
        for bad in (good[:-1],good+[RESULT],good+[b'V425_HARDWARE_FALLBACK hit=1'],good+[b'V433_OS_INVALID reason=1 stage=1'],good[:len(PREFIX)-1]+good[len(PREFIX):],PREFIX+[STAGES[1]]+STAGES[1:]+[RESULT]):
            self.assertFalse(inspect(log(bad),0)[1])
        for rc in (1,87,124,134,255):self.assertFalse(inspect(log(good),rc)[1])
        self.assertIn('reason=7',inspect(log(PREFIX+STAGES[:4]+[b'V435_TIME_INVALID reason=7 stage=4']),87)[0])
        with self.assertRaises(ValueError):inspect(b'x'*(MAX_LOG+1),0)
if __name__=='__main__':unittest.main()
