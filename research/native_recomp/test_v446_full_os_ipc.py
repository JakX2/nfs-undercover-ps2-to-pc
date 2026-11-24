import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import patch_probe as time_probe
from prepare_v439_full_os_hardware import patch_probe as hw_probe
from prepare_v444_full_os_arena import patch_probe as arena_probe
from prepare_v446_full_os_ipc import patch_probe,install,EDGES,IpcPreparationError
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT
from test_v435_full_os_time_audit import PREFIX
from audit_v439_full_os_hardware import STAGES as HW,RESULT as HW_RESULT,COPY
from audit_v444_full_os_arena import STAGES as ARENA,RESULT as ARENA_RESULT
from audit_v446_full_os_ipc import STAGES,RESULT,inspect
HOST=Path(__file__).parent
def log(lines):return b'\n'.join(lines)+b'\n'
class Tests(unittest.TestCase):
    def test_trace_diagnostics(self):
        def trace(pc):return f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);'
        markers=[trace(pc) for _,pc in EDGES]
        with tempfile.TemporaryDirectory() as td, patch('prepare_v446_full_os_ipc.expectations',return_value='synthetic'):
            root=Path(td);shard=root/'output_0.cpp'
            for i in range(4):
                for rows,stage in ((markers[:i]+markers[i+1:],'trace_missing'),(markers+[markers[i]],'trace_duplicate')):
                    shard.write_text('\n'.join(rows))
                    with self.assertRaises(IpcPreparationError) as e:install(b'',root,HOST)
                    self.assertEqual((e.exception.stage,e.exception.ordinal),(stage,i+1))
                    self.assertFalse((root/'nWiiRuntime').exists())

    def test_probe(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for transform in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe):old=transform(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('os_ipc.begin(cpu)',new);self.assertIn('os_ipc.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_legacy_chain_diagnostic(self):
        for upper in (False,True):
            legacy=[line if i<9 else f'V439_HW_STAGE n={format(i+1,"X" if upper else "x")} valid=1'.encode()
                    for i,line in enumerate(HW)]
            for copy in (0,1):
                prefix=PREFIX+TIME+[TIME_RESULT,f'V439_HW_BEGIN copy={copy}'.encode()]+legacy[:1]+([COPY] if copy else [])+legacy[1:]+[HW_RESULT]
                prefix += [b'V444_ARENA_BEGIN boot_path=1 direct_low=0']+ARENA+[ARENA_RESULT]
                good=prefix+[b'V446_IPC_BEGIN clamp=0']+STAGES+[RESULT]
                row,ok=inspect(log(good),0)
                self.assertFalse(ok)
                self.assertIn('arena=0 stages=4',row)
                self.assertIn('terminal=1 legacy_chain_complete=1 verified=0',row)
                for bad,rc in ((good[:-1],0),(good+[RESULT],0),(good,90),
                        (good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                        (good+[legacy[-1]],0),
                        (good[:good.index(legacy[9])]+good[good.index(legacy[9])+1:],0)):
                    row,ok=inspect(log(bad),rc);self.assertFalse(ok)
                    self.assertIn('legacy_chain_complete=0',row)
    def test_gate(self):
        for copy in (0,1):
            prior=PREFIX+TIME+[TIME_RESULT,f'V439_HW_BEGIN copy={copy}'.encode()]+HW[:1]+([COPY] if copy else [])+HW[1:]+[HW_RESULT]
            prior += [b'V444_ARENA_BEGIN boot_path=1 direct_low=0']+ARENA+[ARENA_RESULT]
            for clamp in (0,1):
                begin=f'V446_IPC_BEGIN clamp={clamp}'.encode()
                good=prior+[begin]+STAGES+[RESULT]
                self.assertTrue(inspect(log(good),0)[1])
                for bad,rc in ((good,90),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prior+[begin]+STAGES[1:]+[RESULT],0),(prior[:-1]+[begin]+STAGES+[RESULT],0)):
                    self.assertFalse(inspect(log(bad),rc)[1])
                self.assertIn('reason=7',inspect(log(prior+[begin,b'V446_IPC_INVALID reason=7 stage=1']),90)[0])
if __name__=='__main__':unittest.main()
