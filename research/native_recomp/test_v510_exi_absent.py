import unittest
import struct
from unittest.mock import patch
from test_v504_exi_id import fixture as id_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,patch_probe as id_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v510_exi_absent import expectations,patch_probe,patch_label,CALLS,RETURNS,EDGES,EXI_END,PROBE_END,VERSION_POINTER
from audit_v510_exi_absent import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(id_fixture())
    # Extend the synthetic EXI segment just enough to map special-device target.
    slot=5;off,base,size=(struct.unpack_from('>I',data,h+4*slot)[0] for h in (0,0x48,0x90))
    old=bytes(data[off:off+size]);new=old+struct.pack('>I',0x60000000)*((0x804f02a4-base-size)//4)
    for h,v in ((0,len(data)),(0x48,base),(0x90,len(new))):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(new)
    for site,target in (*CALLS,*EDGES):put(data,site,bl(site,target))
    for pc in (EXI_END,PROBE_END):put(data,pc-4,0x4e800020)
    for slot in range(11):
        if struct.unpack_from('>I',data,0xac+4*slot)[0]==0:break
    else:raise ValueError('data slot')
    for h,v in ((0x1c,len(data)),(0x64,VERSION_POINTER),(0xac,4)):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(struct.pack('>I',0x80610000))
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets,words=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(set(words),set(RETURNS))
        self.assertEqual(header.count('VectorEdge{'),6)
        for pc in {s for s,_ in (*CALLS,*EDGES)}|{EXI_END-4,PROBE_END-4}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    def test_probe(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
        for pc in RETURNS:
            line=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: 60000000\n'
            self.assertIn('V510 original absent ID return',patch_label(line,pc,0x60000000))
            with self.assertRaises(ValueError):patch_label(line+line,pc,0x60000000)
    def test_gate(self):
        good=OS_EXI_ID+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,103),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (OS_EXI_ID[:-1]+STAGES+[RESULT],0),(OS_EXI_ID+STAGES[1:]+[RESULT],0),(OS_EXI_ID+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
