import unittest
import struct
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v486_context_startup import fixture as context_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,patch_probe as context_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v488_os_cache_reuse import expectations,patch_probe,CALLS,RETURNS
from audit_v488_os_cache_reuse import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_CONTEXT,log
def fixture():
    data=bytearray(context_fixture())
    for slot,base,size in ((4,0x804b7920,0x18),(5,0x804ef9bc,4)):
        for h,v in ((0,len(data)),(0x48,base),(0x90,size)):struct.pack_into('>I',data,h+4*slot,v)
        data.extend(struct.pack('>I',0x60000000)*(size//4))
    for site,target in CALLS:put(data,site,bl(site,target))
    for pc in RETURNS:put(data,pc,0x4e800020)
    put(data,0x8052259c,0x408200a8)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(header.count('VectorEdge{'),9)
        for pc in [x[0] for x in CALLS]+list(RETURNS)+[0x8052259c]:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::OsCacheReuseWitness w(undercover::wii::v488::expected_cache);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('reuse.begin(cpu)',new);self.assertIn('reuse.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        good=OS_CONTEXT+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,98),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                       (OS_CONTEXT[:-1]+STAGES+[RESULT],0),(OS_CONTEXT+STAGES[1:]+[RESULT],0),
                       (OS_CONTEXT+STAGES[::-1]+[RESULT],0),(OS_CONTEXT+[STAGES[0]]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
