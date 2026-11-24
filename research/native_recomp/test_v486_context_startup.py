import unittest
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v483_irq_return import fixture as irq_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,patch_probe as return_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v486_context_startup import expectations,patch_probe,CALLS,RET,CONTEXT
from audit_v486_context_startup import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_IRQ_RETURN,log
def fixture():
    data=bytearray(irq_fixture())
    for site,target in CALLS:put(data,site,bl(site,target))
    put(data,CONTEXT,0x9421fff0);put(data,RET,0x4e800020)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertIn('},16u}',header)
        for pc in [x[0] for x in CALLS]+[RET,CONTEXT]:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::ContextStartupWitness w(undercover::wii::v486::expected_context);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('context.begin(cpu)',new);self.assertIn('context.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        good=OS_IRQ_RETURN+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,97),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                       (OS_IRQ_RETURN[:-1]+STAGES+[RESULT],0),(OS_IRQ_RETURN+STAGES[1:]+[RESULT],0),
                       (OS_IRQ_RETURN+STAGES[::-1]+[RESULT],0),(OS_IRQ_RETURN+[STAGES[0]]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
