import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v672_si_ack_route import patch_si
from prepare_v680_si_helper import patch_binding as first_patch,patch_helper
from prepare_v688_si_second import patch_binding
from si_second_geometry_v688 import second_edge
from audit_v672_si_ack_route import inspect,EVENTS,RESULT
from audit_v699_si_postack import inspect as inspect_post,STAGE,END,NESTED,RETURN
HOST=Path(__file__).resolve().parent
H=0x80004000;A=0x80005000;B=0x80006000
FIRST=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
SECOND=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,4)]
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
class Tests(unittest.TestCase):
    def test_second_edge(self):
        words=[bl(H,A),bl(H+4,B),0x90030000,0x4e800020]
        self.assertEqual(second_edge(H,words,{B:16}),(H+4,B,16,words[1]))
        for bad,sizes in ((words,{}),(words,{B:3}),(words,{B:8192}),([words[0],0x4e800421,*words[1:]],{B:16})):
            with self.assertRaises(ValueError):second_edge(H,bad,sizes)
    def test_labels_and_audit(self):
        words=[0x90030000,bl(B+4,A),0x60000000,0x4e800020]
        s='#include "runtime/cpu_context.h"\n'+f'void func_{B:X}(CPUContext& ctx) {{\n'+''.join(
            f'loc_{B+4*i:X}: ;\n    // 0x{B+4*i:08X}: {w:08X}\n    ++ctx.inst_count;\n    body();\n' for i,w in enumerate(words))+'}\n'
        out,seen=patch_helper(s,B,words,True)
        self.assertEqual(len(seen),4);self.assertEqual(out.count('v688::before('),4)
        self.assertIn(f'0x{words[1]:08x}u,1u,1u);',out)
        with patch('audit_v672_si_ack_route.inspect_dispatch',return_value=('ok',True)):
            for hs in (SECOND,SECOND[:2]+[b'V688_SI_SECOND_ACK n=1']):
                good=EVENTS[:1]+FIRST+hs+EVENTS[1:]+[RESULT]
                self.assertTrue(inspect(b'\n'.join(good),0)[1])
                for bad in (good[:2]+good[3:],good+[b'V688_SI_SECOND_CALL ordinal=1 kind=1'],good+[b'V688_SI_SECOND_INVALID reason=4 stage=2 trace=0']):
                    self.assertFalse(inspect(b'\n'.join(bad),0)[1])
    def test_post_audit(self):
        prefix=EVENTS[:1]+FIRST+SECOND[:2]+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]
        with patch('audit_v672_si_ack_route.inspect_dispatch',return_value=('ok',True)):
            for suffix in ([STAGE,RETURN,END],[STAGE,*NESTED,RETURN,END]):
                self.assertTrue(inspect_post(b'\n'.join(prefix+suffix),0)[1])
                for bad in (suffix[:-1],suffix+[END],suffix+[b'V699_POSTACK_INVALID reason=1 trace=0'],suffix[::-1]):
                    self.assertFalse(inspect_post(b'\n'.join(prefix+bad),0)[1])
                self.assertFalse(inspect_post(b'\n'.join(prefix+suffix),126)[1])
    @unittest.skipIf(os.name=='nt','GCC sanitizer integration control')
    def test_compiled_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for n in ('wii_si_controller_v511.h','wii_si_completion_ack_v668.h','wii_si_first_helper_v680.h','wii_si_helper_binding_v680.h','wii_si_second_binding_v688.h','wii_si_type_scheduler_v514.h','test_si_second_v689.cpp'):
                shutil.copyfile(HOST/n,root/n)
            (root/'wii_si_binding_v512.h').write_text(patch_si((HOST/'wii_si_binding_v512.h').read_text()))
            (root/'wii_si_ack_binding_v672.h').write_text(patch_binding(first_patch((HOST/'wii_si_ack_binding_v672.h').read_text())))
            (root/'v672_private_si_ack_expectations.h').write_text('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v672 {inline constexpr uint32_t handler_first=0x80004000u,handler_end=0x80004020u;}\n')
            (root/'v680_private_si_helper_expectations.h').write_text('#pragma once\nnamespace undercover::wii::v680 {inline constexpr SiHelperExpectation expected{0x80004000u,0x80005000u,0x80005008u,0x48001001u};}\n')
            (root/'v688_private_si_second_expectations.h').write_text('#pragma once\nnamespace undercover::wii::v688 {inline constexpr SiHelperExpectation expected_second{0x80004004u,0x80006000u,0x80006010u,0x48001ffdu};}\n')
            hw=root/'runtime/hw/hw.h';hw.parent.mkdir(parents=True)
            hw.write_text('#pragma once\n#include <atomic>\n#include <cstdint>\nnamespace nwii::runtime::hw {inline std::atomic<uint32_t> pi_intsr{0},pi_intmr{0};}\n')
            exe=root/'probe'
            subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'test_si_second_v689.cpp'),'-o',str(exe)],check=True)
            base=EVENTS[:1]+FIRST;entered=base+SECOND[:2]
            expected={
                'inside':(0,entered+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]),
                'after':(0,base+SECOND+EVENTS[1:]+[RESULT]),
                'out-of-order':(126,EVENTS[:1]+[b'V673_SI_ACK_CALL ordinal=2 kind=1',b'V672_SI_ACK_INVALID reason=6 trace=0']),
                'wrong-lr':(126,base+SECOND[:1]+[b'V688_SI_SECOND_INVALID reason=2 stage=1 trace=0']),
                'nested':(126,entered+[b'V688_SI_SECOND_CALL ordinal=1 kind=1',b'V688_SI_SECOND_INVALID reason=4 stage=2 trace=0']),
                'gap':(126,entered+[b'V688_SI_SECOND_INVALID reason=3 stage=2 trace=2']),
                'wrong-next':(126,entered+[b'V688_SI_SECOND_INVALID reason=3 stage=2 trace=3']),
                'stale':(126,entered+[b'V677_SI_ACK_WRITE_INVALID trace=5']),
                'unsupported':(126,entered+[b'V677_SI_ACK_WRITE_INVALID trace=6']),
                'abi':(126,entered+[b'V688_SI_SECOND_INVALID reason=5 stage=3 trace=0'])}
            post=entered+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]
            expected.update({
                'post-return':(0,post+[STAGE,RETURN,END]),
                'post-branch':(126,post+[b'V699_POSTACK_INVALID reason=1 trace=0']),
                'post-start':(126,post+[STAGE,b'V677_SI_ACK_WRITE_INVALID trace=10']),
                'post-stale':(126,post+[STAGE,b'V677_SI_ACK_WRITE_INVALID trace=9']),
                'post-cause':(126,post+[STAGE,b'V688_SI_SECOND_INVALID reason=3 stage=2 trace=4']),
                'post-abi':(126,post+[STAGE,b'V688_SI_SECOND_INVALID reason=5 stage=3 trace=0'])})
            for mode,(rc,rows) in expected.items():
                with self.subTest(mode=mode):
                    env=dict(os.environ);env.pop('UNDERCOVER_V699_SI_POSTACK',None)
                    if mode.startswith('post-'):env['UNDERCOVER_V699_SI_POSTACK']='1'
                    got=subprocess.run([str(exe),mode],capture_output=True,timeout=10,env=env)
                    self.assertEqual(got.returncode,rc,got.stderr.decode(errors='replace'))
                    self.assertEqual(got.stdout.splitlines(),rows)
                    self.assertEqual(got.stderr,b'')
            print('V689_SECOND_BINDING synthetic=1 cases=16 actual_mmio=1 original_execution=0')
if __name__=='__main__':unittest.main()
