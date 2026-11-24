import unittest
import struct
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v488_os_cache_reuse import fixture as reuse_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,patch_probe as reuse_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v491_exi_poll import expectations,patch_probe,CALLS,BIND_PAIRS,EXI,STOP
from audit_v491_exi_poll import STAGES,RESULT,inspect
from audit_v488_os_cache_reuse import STAGES as REUSE,RESULT as REUSE_RESULT
from test_v434_windows_startup_scope import OS_CONTEXT,log
from apply_irq_bootstrap_v475 import rewrite
def fixture():
    data=bytearray(reuse_fixture())
    size=STOP-EXI+4;struct.pack_into('>I',data,0x90+4*5,size)
    data.extend(struct.pack('>I',0x60000000)*((size-4)//4))
    for site,target in CALLS:put(data,site,bl(site,target))
    put(data,EXI,0x9421ffe0)
    for pc in (0x804ef9dc,0x804ef9ec,0x804ef9fc):put(data,pc,0x80030000)
    for pc in (0x804ef9e8,0x804ef9f8,0x804efa08):put(data,pc,0x40820000|((0x804ef9dc-pc)&0xfffc))
    put(data,0x804efa10,0x38600000)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(header.count('VectorEdge{'),2)
        for pc in [x[0] for x in CALLS]+[EXI,0x804ef9dc,0x804ef9e8,0x804efa10]:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::ExiColdPollWitness w(undercover::wii::v491::expected_poll);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('exi_poll.begin(cpu,IrqBankBinding::exi_enabled())',new)
        with self.assertRaises(ValueError):patch_probe(new)
        old='\n'.join(a for a,_ in BIND_PAIRS);new=rewrite(old,BIND_PAIRS)
        self.assertEqual(rewrite(new,BIND_PAIRS),new)
        for a,_ in BIND_PAIRS:
            with self.assertRaises(ValueError):rewrite(old+'\n'+a,BIND_PAIRS)
    def test_gate(self):
        prefix=OS_CONTEXT+REUSE+[REUSE_RESULT];good=prefix+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,99),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                       (prefix[:-1]+STAGES+[RESULT],0),(prefix+STAGES[1:]+[RESULT],0),
                       (prefix+STAGES[::-1]+[RESULT],0),(prefix+[STAGES[0]]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
