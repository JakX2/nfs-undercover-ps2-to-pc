import hashlib
from pathlib import Path
import struct
import unittest
from test_v433_full_os_entry import fixture as os_fixture
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v435_full_os_time import OS,EDGES,BODIES,expectations,patch_probe
HOST=Path(__file__).parent
def fixture():
    data=bytearray(os_fixture())
    # Independent extra text region for the time and register helpers.
    offset=len(data);base=0x8052a800;size=0x80545120-base
    for h,v in ((0,offset),(0x48,base),(0x90,size)):struct.pack_into('>I',data,h+8,v)
    data.extend(b'\0'*size)
    def put(pc,word):
        for i in range(7):
            off,addr,n=(struct.unpack_from('>I',data,h+4*i)[0] for h in (0,0x48,0x90))
            if addr<=pc and pc+4<=addr+n:
                struct.pack_into('>I',data,off+pc-addr,word);return
        raise ValueError('fixture range')
    for pc,n in BODIES:put(pc,0x60000000);put(pc+(n-1)*4,0x4e800020)
    for site,target in EDGES:put(site,0x48000001|((target-site)&0x03fffffc))
    for site,reg,disp in ((OS+0x3c,4,0xf254),(OS+0x40,3,0xf250)):
        put(site,(36<<26)|(reg<<21)|(13<<16)|disp)
    return bytes(data)
class Tests(unittest.TestCase):
    def test_geometry(self):
        data=fixture();digest=hashlib.sha256(data).hexdigest()
        self.assertEqual(expectations(data,digest).count('OsTimeEdge{'),6)
        with self.assertRaises(ValueError):expectations(data)
    def test_probe(self):
        old=os_probe(data_probe(cache_probe((HOST/'wii_full_hardware_probe_v425.h').read_text())))
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('os_time.begin(cpu)',new);self.assertIn('os_time.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
if __name__=='__main__':unittest.main()
