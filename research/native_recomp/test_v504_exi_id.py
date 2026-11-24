import unittest
import struct
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch
from test_v500_exi_handlers import fixture as handler_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,patch_probe as handler_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v504_exi_id import expectations,patch_probe,patch_label,CALLS,RETURN,EDGES,RANGES
from audit_v504_exi_id import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_HANDLERS,log
def fixture():
    data=bytearray(handler_fixture())
    # Rebuild the EXI code segment privately from synthetic NOPs, keeping
    # the predecessor geometry and extending it in both directions.
    slot=5;off,base,size=(struct.unpack_from('>I',data,h+4*slot)[0] for h in (0,0x48,0x90))
    old=bytes(data[off:off+size]);lo=0x804ee894;hi=0x804f0128
    new=bytearray(struct.pack('>I',0x60000000)*((hi-lo)//4))
    new[base-lo:base-lo+size]=old
    for h,v in ((0,len(data)),(0x48,lo),(0x90,len(new))):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(new)
    # The two optional branches must be mapped too, even though their
    # execution is deliberately rejected by the bounded witness.
    # Slot 3 is already the predecessor's original-free memset region.
    # Extend slot 2 instead of replacing any predecessor text mapping.
    slot=2;off,base,size=(struct.unpack_from('>I',data,h+4*slot)[0] for h in (0,0x48,0x90))
    lo=0x8051fd44;hi=0x8054879c
    old=bytes(data[off:off+size])
    new=bytearray(struct.pack('>I',0x60000000)*((hi-lo)//4))
    new[base-lo:base-lo+size]=old
    for h,v in ((0,len(data)),(0x48,lo),(0x90,len(new))):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(new)
    for site,target in (*CALLS,*EDGES):put(data,site,bl(site,target))
    for _,hi in RANGES:put(data,hi-4,0x4e800020)
    put(data,RETURN,0x80030000)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets,word=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(header.count('VectorEdge{'),12)
        for pc in set([x[0] for x in CALLS]+[x[0] for x in EDGES]+[h-4 for _,h in RANGES]+[RETURN]):
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        if shutil.which('g++'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td);(p/'expected.h').write_text(header)
                c=p/'test.cpp';c.write_text('#include "expected.h"\nint main(){undercover::wii::ExiIdWitness w(undercover::wii::v504::expected_id);return w.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(HOST),str(c)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('exi_id.begin(cpu,ExiTickBinding::active()&&ExiDiConfigBinding::active())',new)
        with self.assertRaises(ValueError):patch_probe(new)
        label='loc_804EFAB0: ;\n    // 0x804EFAB0: 80030000\n'
        self.assertIn('V504 original ID return',patch_label(label,0x80030000))
        for bad in (label+label,label.replace('80030000','00000000'),patch_label(label,0x80030000)):
            with self.assertRaises(ValueError):patch_label(bad,0x80030000)
    def test_gate(self):
        good=OS_EXI_HANDLERS+STAGES+[RESULT];self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,102),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (OS_EXI_HANDLERS[:-1]+STAGES+[RESULT],0),(OS_EXI_HANDLERS+STAGES[1:]+[RESULT],0),(OS_EXI_HANDLERS+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
