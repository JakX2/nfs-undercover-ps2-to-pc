import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v473_module_irq import irq_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v473_module_irq import patch_probe as irq_probe
from prepare_v476_irq_mmio import expectations,patch_probe,CALL,STORES,DISABLE
from audit_v476_irq_mmio import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_PACK,log
from audit_v470_alarm_startup import STAGES as ALARM,RESULT as ALARM_RESULT
from audit_v473_module_irq import STAGES as IRQ,RESULT as IRQ_RESULT
def stw(src,base,disp):return (36<<26)|(src<<21)|(base<<16)|disp
def fixture():
    data=bytearray(irq_fixture())
    for pc,src,base,disp in STORES:put(data,pc,stw(src,base,disp))
    put(data,CALL,bl(CALL,DISABLE))
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,target=expectations(raw,digest(raw))
        self.assertEqual(target,DISABLE)
        self.assertIn('disable_edge=VectorEdge{',header)
        for pc in [x[0] for x in STORES]+[CALL]:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::IrqMmioWitness w(undercover::wii::v476::start_word,undercover::wii::v476::disable_edge);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('mmio.begin(cpu)',new);self.assertIn('mmio.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        prefix=OS_PACK+ALARM+[ALARM_RESULT]+IRQ+[IRQ_RESULT]
        good=prefix+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,95),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                       (prefix[:-1]+STAGES+[RESULT],0),(prefix+STAGES[1:]+[RESULT],0),
                       (prefix+STAGES[::-1]+[RESULT],0),(prefix+[STAGES[0]]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
