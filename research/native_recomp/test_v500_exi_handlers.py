import unittest
import struct
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v491_exi_poll import fixture as poll_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,patch_probe as poll_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v500_exi_handlers import expectations,patch_probe,CALLS,WRITES,MASK,SETTER,ID,PAIRS
from audit_v500_exi_handlers import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_POLL,log
from apply_irq_bootstrap_v475 import rewrite
def fixture():
    data=bytearray(poll_fixture())
    base=0x804ef9bc;old=struct.unpack_from('>I',data,0x90+4*5)[0];size=ID-base+4
    struct.pack_into('>I',data,0x90+4*5,size)
    data.extend(struct.pack('>I',0x60000000)*((size-old)//4))
    for site,target in CALLS:put(data,site,bl(site,target))
    put(data,0x80526988,bl(0x80526988,0x805266e0))
    put(data,MASK,0x9421ffe0);put(data,MASK+124,0x4e800020)
    for i,w in enumerate((0x80030000,0x5463103a,0x7c64182e,0x7c64192e,0x4e800020)):put(data,SETTER+4*i,w)
    for pc in WRITES:put(data,pc,0x90030000)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}));self.assertEqual(header.count('VectorEdge{'),12)
        for pc in [x[0] for x in CALLS]+list(WRITES)+[MASK,MASK+124,SETTER+16]:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::ExiHandlerWitness w(undercover::wii::v500::expected_handlers);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('exi_handlers.begin(cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
        old='\n'.join(a for a,_ in PAIRS);new=rewrite(old,PAIRS);self.assertEqual(rewrite(new,PAIRS),new)
        for a,_ in PAIRS:
            with self.assertRaises(ValueError):rewrite(old+'\n'+a,PAIRS)
    def test_gate(self):
        good=OS_EXI_POLL+STAGES+[RESULT];self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,100),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (OS_EXI_POLL[:-1]+STAGES+[RESULT],0),(OS_EXI_POLL+STAGES[1:]+[RESULT],0),(OS_EXI_POLL+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
