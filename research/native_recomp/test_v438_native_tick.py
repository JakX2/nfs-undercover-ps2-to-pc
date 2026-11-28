import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from apply_native_tick_v438 import (BEFORE,AFTER,LABEL,LABEL_TICK,TICK,FILE,
    DISPATCH_BEFORE,DISPATCH_AFTER,rewrite,apply)

SOURCE='''void emit_function(){
  for(const auto& inst: instructions){
'''+BEFORE+'''
  }
}
void emit_instruction(){
'''+LABEL+'''
  out << "original body\\n";
}
'''

FULL_SOURCE=SOURCE+'\n'+DISPATCH_BEFORE+'\n'+DISPATCH_BEFORE+'\n'

class Tests(unittest.TestCase):
    def test_geometry(self):
        out=rewrite(SOURCE)
        self.assertEqual(rewrite(out),out)
        self.assertEqual(out.count(TICK),1)
        self.assertIn(LABEL_TICK,out);self.assertNotIn(BEFORE,out)
        for bad in (SOURCE+SOURCE,SOURCE.replace(LABEL,''),SOURCE.replace(BEFORE,AFTER),SOURCE+TICK,out+TICK):
            with self.assertRaises(ValueError):rewrite(bad)
    def test_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/FILE;p.parent.mkdir(parents=True);p.write_text(FULL_SOURCE)
            self.assertTrue(apply(root));self.assertFalse(apply(root))
            p.write_text(FULL_SOURCE+TICK)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(p.read_text(),FULL_SOURCE+TICK)
            p.write_text(SOURCE)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(p.read_text(),SOURCE)
    def test_host_dispatch_has_no_implicit_guest_tick(self):
        patched=rewrite(FULL_SOURCE,require_dispatch=True)
        self.assertEqual(patched.count(DISPATCH_BEFORE),0)
        self.assertEqual(patched.count(DISPATCH_AFTER),2)
        self.assertEqual(rewrite(patched,require_dispatch=True),patched)
        self.assertIn(LABEL_TICK,patched)
        self.assertEqual(patched.count(TICK),1)
        for malformed in (FULL_SOURCE.replace(DISPATCH_BEFORE,'',1),
                          FULL_SOURCE.replace(DISPATCH_BEFORE,DISPATCH_AFTER,1),
                          patched+DISPATCH_BEFORE,
                          FULL_SOURCE.replace(DISPATCH_BEFORE,
                                              '    ++ctx.inst_count;\\n',1)):
            with self.assertRaises(ValueError):
                rewrite(malformed,require_dispatch=True)

    def test_dispatch_roundtrip_does_not_count_host_edges(self):
        cc = shutil.which('g++')
        if not cc:
            self.skipTest('GCC unavailable')
        # The earlier regression covered labels but not the generated host
        # run_game dispatch edges. Exercise both wrapper shapes, three genuine
        # native guest visits, and an RFI-style PC continuation with no
        # proprietary instructions or owner data.
        patched_emitter = rewrite(FULL_SOURCE, require_dispatch=True)
        self.assertEqual(patched_emitter.count(DISPATCH_AFTER), 2)
        self.assertNotIn(DISPATCH_BEFORE, patched_emitter)

        def source(patched):
            seam = DISPATCH_AFTER if patched else DISPATCH_BEFORE
            emitted = seam.partition('"')[2].rpartition('"')[0].replace('\\n', '\n')
            if not emitted.startswith('        uint32_t target = ctx.pc;\n'):
                raise AssertionError('unexpected dispatcher emitter seam')
            fragment = emitted + '100000) == 0) ++diagnostics;\n'
            return (
                '#include <cstdint>\n'
                'struct CPU { uint64_t inst_count=0; uint32_t pc=1, visits=0; };\n'
                'unsigned diagnostics=0;\n'
                'void first(CPU& c) { ++c.inst_count; c.pc=2; ++c.visits; }\n'
                'void second(CPU& c) { ++c.inst_count; c.pc=3; ++c.visits; }\n'
                'void rfi(CPU& c) { ++c.inst_count; c.pc=4; ++c.visits; }\n'
                'void unsplit(CPU& ctx) {\n'
                '  while(ctx.pc!=4) {\n' + fragment +
                '    switch(target) {case 1:first(ctx);break; case 2:second(ctx);break; '
                'case 3:rfi(ctx);break; default:return;}\n'
                '  }\n}\n'
                'void split(CPU& ctx) {\n'
                '  while(ctx.pc!=4) {\n' + fragment +
                '    if(target==1)first(ctx);else if(target==2)second(ctx);'
                'else if(target==3)rfi(ctx);else return;\n'
                '  }\n}\n'
                'int main() {CPU a,b;unsplit(a);split(b);\n'
                '  if(a.inst_count!=3||b.inst_count!=3||a.visits!=3||b.visits!=3||'
                'a.pc!=4||b.pc!=4||diagnostics)return 1;\n'
                '  return 0;\n}\n'
            )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for patched in (False, True):
                (root/'dispatch.cpp').write_text(source(patched), encoding='utf-8')
                subprocess.run([cc, '-std=c++20', '-Wall', '-Wextra', '-Werror',
                                '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                                str(root/'dispatch.cpp'), '-o', str(root/'dispatch')],
                               check=True, capture_output=True)
                result = subprocess.run([str(root/'dispatch')], capture_output=True)
                self.assertEqual(result.returncode, 0 if patched else 1,
                                 result.stderr.decode('utf-8', errors='replace'))

    def test_emitted_control_flow(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        # Compile a miniature emitter containing the real source seams.
        # It emits a synthetic loop and a resume switch, never game code.
        generator='''#include <iostream>
#include <iomanip>
struct Instruction{unsigned address;const char* body;unsigned opcode=0;};
void emit_instruction(std::ostream& out,const Instruction& inst,int){
'''+LABEL+'''
  out << inst.body << "\\n";
}
int main(){
  auto& out=std::cout;const int func=0;
  out << "#include <cstdint>\\nstruct CPU{uint64_t inst_count=0;unsigned ctr=0,r=0,pc=0;};\\nvoid run(CPU& ctx){\\nif(ctx.pc==1)goto loc_10;\\nif(ctx.pc==2)goto loc_18;\\n";
  Instruction instructions[]={{0xc,"ctx.ctr=3; ctx.r=0;"},{0x10,"++ctx.r;"},{0x14,"if(--ctx.ctr)goto loc_10;"},{0x18,"ctx.r+=2;"},{0x1c,"return;"}};
  for(const auto& inst:instructions){
'''+BEFORE+'''
  }
  out << "}\\nint main(){CPU a;run(a);if(a.inst_count!=9||a.r!=5)return 1;CPU b{100,2,8,1};run(b);if(b.inst_count!=106||b.r!=12)return 2;CPU c{40,0,9,2};run(c);if(c.inst_count!=42||c.r!=11)return 3;}\\n";
}
'''
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for patched in (False,True):
                (root/'gen.cpp').write_text(rewrite(generator) if patched else generator)
                subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(root/'gen.cpp'),'-o',str(root/'gen')],check=True,capture_output=True)
                (root/'native.cpp').write_bytes(subprocess.check_output([str(root/'gen')]))
                subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror','-Wno-unused-label','-fsanitize=address,undefined','-fno-pie','-no-pie',str(root/'native.cpp'),'-o',str(root/'native')],check=True,capture_output=True)
                rc=subprocess.run([str(root/'native')],capture_output=True).returncode
                self.assertEqual(rc,0 if patched else 1)
if __name__=='__main__':unittest.main()
