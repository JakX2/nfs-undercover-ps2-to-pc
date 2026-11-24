"""Original-free DOL geometry and composed observer installation tests."""
import hashlib
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from prepare_v466_exception_pack import expectations,install,EXC_END,SYS_END,BRIDGE,SYS_REQUIRED
from prepare_v457_exception_vector import REQUIRED,STOP,geometry,patch_probe as vector_probe
from prepare_v453_debug_leaf import VECTORS
from test_v466_exception_pack import HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe
from test_v439_full_os_hardware import trace,put

def bl(site,target):return 0x48000001|((target-site)&0x03fffffc)

def fixture():
    # Independently authored test DOL with only synthetic NOPs and branch
    # geometry. Previous authenticated startup stages are mocked explicitly.
    groups=((0x80004338,4),(0x804e50a0,28),(0x805208ac,0x80545138-0x805208ac))
    data=bytearray(256)
    for i,(base,size) in enumerate(groups):
        for h,v in ((0,len(data)),(0x48,base),(0x90,size)):struct.pack_into('>I',data,h+4*i,v)
        data.extend(struct.pack('>I',0x60000000)*(size//4))
    offsets=[0x100*i for i in range(1,16)]
    for h,v in ((0x1c,len(data)),(0x64,VECTORS),(0xac,60)):struct.pack_into('>I',data,h,v)
    data.extend(struct.pack('>15I',*offsets))
    for site,target in (*REQUIRED.items(),*SYS_REQUIRED.items(),*BRIDGE,
                        (0x80520e58,0x804e50b8),(0x80520e60,0x80545134)):
        put(data,site,bl(site,target))
    for end in (EXC_END,SYS_END):put(data,end-4,0x4e800020)
    return bytes(data)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def seed_ipc(data,root,host,digest):
    dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
    source=(host/'wii_full_hardware_probe_v425.h').read_text()
    for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe):source=f(source)
    (dest/'wii_full_start_probe_v419.h').write_text(source)

class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_original_free_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(header.count('VectorEdge{'),14)
        self.assertIn('9u,3u,VectorEdge{',header)
        self.assertEqual(targets,sorted(set(targets)))
        for pc in (next(iter(REQUIRED)),next(iter(SYS_REQUIRED)),BRIDGE[1][0],EXC_END-4,SYS_END-4):
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        # Reject a missing syscall slot while retaining otherwise aligned,
        # non-overlapping vector geometry.
        bad=bytearray(raw);off=struct.unpack_from('>I',bad,0x1c)[0]
        struct.pack_into('>I',bad,off+11*4,0x2000)
        with self.assertRaises(ValueError):expectations(bad,digest(bad))

    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    @patch('prepare_v457_exception_vector.install_ipc',side_effect=seed_ipc)
    def test_full_install_and_header(self,seed,_):
        raw=fixture();sha=digest(raw);header,targets=expectations(raw,sha)
        _,word,first_targets=geometry(raw,sha)
        self.assertTrue(first_targets<=set(targets))
        seam=f'\nloc_80520DB8: ;\n    // 0x80520DB8: {word:08X}\n'
        source='\n'.join(trace(pc) for pc in targets)+seam
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);shard=root/'output_0.cpp';dest=root/'nWiiRuntime/include/undercover'
            for bad in (source.replace(trace(targets[0]),''),source+'\n'+trace(targets[-1])):
                shard.write_text(bad)
                with self.assertRaises(ValueError):install(raw,root,HOST,sha)
                self.assertEqual(shard.read_text(),bad);self.assertFalse(dest.exists())
            shard.write_text(source);install(raw,root,HOST,sha)
            self.assertEqual(seed.call_count,1)
            self.assertIn('V457 original vector cache return',shard.read_text())
            self.assertEqual((dest/'v466_private_pack_expectations.h').read_text(),header)
            probe=(dest/'wii_full_start_probe_v419.h').read_text()
            self.assertEqual(probe.count('std::_Exit(0)'),1)
            self.assertIn('pack.first_copy(cpu)',probe)
            self.assertIn('pack.observe(addr,cpu)',probe)
            if shutil.which('g++'):
                # Compile exactly the generated synthetic header, not a
                # manually copied approximation of the aggregate format.
                test=root/'header_check.cpp'
                test.write_text('#include "v466_private_pack_expectations.h"\n'
                    '#include "v457_private_vector_expectations.h"\n'
                    'static_assert(undercover::wii::v466::expected_pack.exception_count==9);\n'
                    'static_assert(undercover::wii::v466::expected_pack.syscall_count==3);\n'
                    'static_assert(undercover::wii::v457::expected_vector.count==7);\n'
                    'int main(){undercover::wii::ExceptionPackRoute x(undercover::wii::v466::expected_pack);return x.phase();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(dest),str(test)],check=True,timeout=30)

if __name__=='__main__':unittest.main()
