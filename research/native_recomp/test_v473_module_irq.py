import struct
import unittest
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
from test_v468_exception_pack_geometry import fixture,digest,bl,put,seed_ipc
from test_v439_full_os_hardware import trace
from prepare_v466_exception_pack import expectations as pack_geometry
from prepare_v470_alarm_startup import expectations as alarm_geometry
from prepare_v457_exception_vector import geometry as vector_geometry,STOP as VECTOR_STOP
from test_v466_exception_pack import HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe
from prepare_v466_exception_pack import patch_probe as pack_probe
from prepare_v470_alarm_startup import patch_probe as alarm_probe,CALLS as ALARM_CALLS,ENDS as ALARM_ENDS
from prepare_v473_module_irq import expectations,patch_probe,CALLS,ENDS,return_seam,STOP,install
from test_v434_windows_startup_scope import OS_IPC,log
from audit_v457_exception_vector import STAGES as VECTOR,RESULT as VECTOR_RESULT
from audit_v466_exception_pack import STAGES as PACK,RESULT as PACK_RESULT
from audit_v470_alarm_startup import STAGES as ALARM,RESULT as ALARM_RESULT
from audit_v473_module_irq import STAGES,RESULT,inspect
def irq_fixture():
    raw=bytearray(fixture())
    base=0x80004388;size=0xe4
    for h,v in ((0,len(raw)),(0x48,base),(0x90,size)):struct.pack_into('>I',raw,h+4*3,v)
    raw.extend(struct.pack('>I',0x60000000)*(size//4))
    for site,target in (*ALARM_CALLS,*CALLS):put(raw,site,bl(site,target))
    for end in (*ALARM_ENDS,*ENDS):put(raw,end-4,0x4e800020)
    return bytes(raw)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=irq_fixture()
        header,targets,stop=expectations(raw,digest(raw))
        self.assertEqual(header.count('VectorEdge{'),4)
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(stop,0x60000000)
        for site in [s for s,_ in CALLS]+[end-4 for end in ENDS]:
            bad=bytearray(raw);put(bad,site,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    @patch('prepare_v457_exception_vector.install_ipc',side_effect=seed_ipc)
    def test_install_chain(self,seed,_):
        raw=irq_fixture();sha=digest(raw)
        vheader,vword,vtargets=vector_geometry(raw,sha)
        pheader,ptargets=pack_geometry(raw,sha)
        aheader,atargets=alarm_geometry(raw,sha)
        iheader,itargets,iword=expectations(raw,sha)
        targets=sorted(vtargets|set(ptargets)|set(atargets)|set(itargets))
        source='\n'.join(trace(pc) for pc in targets)
        for pc,word in ((VECTOR_STOP,vword),(STOP,iword)):
            source+=f'\nloc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n    ++ctx.inst_count;\n'
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);shard=root/'output_0.cpp';dest=root/'nWiiRuntime/include/undercover'
            # IRQ preparation validates its own seams before calling the
            # predecessor installers; a failed plan leaves files unchanged.
            for bad in (source.replace(trace(itargets[-1]),''),source+'\n'+trace(itargets[-1]),
                        source.replace(f'loc_{STOP:X}: ;','wrong_label: ;')):
                shard.write_text(bad)
                with self.assertRaises(ValueError):install(raw,root,HOST,sha)
                self.assertEqual(shard.read_text(),bad);self.assertFalse(dest.exists())
            shard.write_text(source)
            install(raw,root,HOST,sha)
            self.assertEqual(seed.call_count,1)
            for name,header in (('v457_private_vector_expectations.h',vheader),
                                ('v466_private_pack_expectations.h',pheader),
                                ('v470_private_alarm_expectations.h',aheader),
                                ('v473_private_irq_expectations.h',iheader)):
                self.assertEqual((dest/name).read_text(),header)
            for label in ('V457 original vector cache return','V473 original IRQ memset return'):
                self.assertEqual(shard.read_text().count(label),1)
            probe=(dest/'wii_full_start_probe_v419.h').read_text()
            self.assertEqual(probe.count('std::_Exit(0)'),1)
            self.assertIn('alarm.begin(cpu)',probe);self.assertIn('irq.begin(cpu)',probe)
            if shutil.which('g++'):
                check=root/'check.cpp'
                check.write_text('#include "v457_private_vector_expectations.h"\n'
                    '#include "v466_private_pack_expectations.h"\n'
                    '#include "v470_private_alarm_expectations.h"\n'
                    '#include "v473_private_irq_expectations.h"\n'
                    'int main(){undercover::wii::AlarmStartupWitness a(undercover::wii::v470::expected_alarm);'
                    'undercover::wii::ModuleIrqWitness i(undercover::wii::v473::expected_irq);'
                    'return a.stage()+i.stage();}\n')
                subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+str(dest),str(check)],check=True,timeout=30)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('irq.begin(cpu)',new);self.assertIn('irq.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_return_seam(self):
        source=f'loc_{STOP:X}: ;\n    // 0x{STOP:X}: 60000000\n    ++ctx.inst_count;\n'
        updated=return_seam(source,0x60000000)
        self.assertIn('trace_call(0x8052664C, ctx)',updated)
        for bad in (source+source,updated,source.replace('60000000','12345678')):
            with self.assertRaises(ValueError):return_seam(bad,0x60000000)
    def test_gate(self):
        prefix=OS_IPC+[b'V457_VECTOR_BEGIN debug_needed=1',b'V457_VECTOR_PRELUDE n=1']+VECTOR+[VECTOR_RESULT]+PACK+[PACK_RESULT]+ALARM+[ALARM_RESULT]
        good=prefix+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for i in range(len(STAGES)):
            self.assertFalse(inspect(log(prefix+STAGES[:i]+STAGES[i+1:]+[RESULT]),0)[1])
            self.assertFalse(inspect(log(prefix+STAGES[:i]+[STAGES[i]]+STAGES[i:]+[RESULT]),0)[1])
        for rows,rc in ((good,94),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prefix[:-1]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(rows),rc)[1])
if __name__=='__main__':unittest.main()
