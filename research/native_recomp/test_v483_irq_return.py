import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v476_irq_mmio import fixture as mmio_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,patch_probe as mmio_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v483_irq_return import expectations,patch_probe,CALLS,RETURNS
from audit_v483_irq_return import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_MMIO,log
from apply_irq_mask_trace_v482 import PAIRS
from apply_irq_bootstrap_v475 import rewrite
def fixture():
    data=bytearray(mmio_fixture())
    for site,target in CALLS:put(data,site,bl(site,target))
    for pc in RETURNS:put(data,pc,0x4e800020)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(header.count('VectorEdge{'),5)
        for pc in [x[0] for x in CALLS]+list(RETURNS):
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::IrqReturnWitness w(undercover::wii::v483::expected_return);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('irq_return.begin(cpu)',new);self.assertIn('irq_return.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_mmio_transform(self):
        source='\n'.join(a for a,_ in PAIRS)
        new=rewrite(source,PAIRS)
        self.assertEqual(rewrite(new,PAIRS),new)
        for a,b in reversed(PAIRS):new=new.replace(b,a,1)
        self.assertEqual(new,source)
        for a,_ in PAIRS:
            for bad in (source.replace(a,'missing',1),source+'\n'+a):
                with self.assertRaises(ValueError):rewrite(bad,PAIRS)
    def test_gate(self):
        good=OS_MMIO+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,96),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                       (OS_MMIO[:-1]+STAGES+[RESULT],0),(OS_MMIO+STAGES[1:]+[RESULT],0),
                       (OS_MMIO+STAGES[::-1]+[RESULT],0),(OS_MMIO+[STAGES[0]]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
