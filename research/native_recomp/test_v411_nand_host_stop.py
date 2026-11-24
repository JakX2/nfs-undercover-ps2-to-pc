#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v411_nand_host_stop import patch,ARM,RESET
from analyze_v411_nand_host_stop import inspect
SOURCE=r'''
// V410_NAND_GUEST_RUN_EXIT calls=
// V405_NAND_SECOND_HALF tail_calls=
struct CPU{bool is_running=true;};
struct ExceptionStop{};
namespace nwii::runtime{unsigned v405_tail_calls=0u;}
void reset(){
  nwii::runtime::v405_tail_calls=0u;
}
void guest(CPU& ctx,unsigned v396_calls){
    if(v396_calls>48u&&v396_calls<=96u){
      const char* s="ctx.is_running=false"; (void)s;
      const char* raw=R"foo(ctx.is_running=false)foo"; (void)raw;
      // ctx.is_running=false;
      /* ctx.is_running=false; */
      if(ctx.is_running)ctx.is_running=false;
      if(ctx.is_running){ctx.is_running = false;throw ExceptionStop{};}
    }
}
int main(){CPU c;reset();guest(c,50u);return c.is_running?1:0;}
'''
class Tests(unittest.TestCase):
    def test_assignment_semantics_and_lexical_exclusions(self):
        out,n=patch(SOURCE)
        self.assertEqual(n,2)
        self.assertIn('ctx.is_running=::v411_note_host_stop(1u,0u)',out)
        self.assertIn('ctx.is_running = ::v411_note_host_stop(2u,1u)',out)
        self.assertIn('R"foo(ctx.is_running=false)foo"',out)
        self.assertIn('// ctx.is_running=false;',out)
        self.assertIn('/* ctx.is_running=false; */',out)
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ unavailable')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.cpp';exe=Path(td)/'fixture'
            p.write_text(out,encoding='utf-8')
            b=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(b.returncode,0,b.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0)
            self.assertEqual(r.stderr,'V411_HOST_STOP event=1 site=1 throws=0\n')
    def test_fail_closed(self):
        for anchor in (ARM,RESET,'V410_NAND_GUEST_RUN_EXIT calls=','V405_NAND_SECOND_HALF tail_calls='):
            with self.assertRaises(ValueError):patch(SOURCE.replace(anchor,'missing'))
        with self.assertRaises(ValueError):patch(patch(SOURCE)[0])
    def test_census_is_not_boot_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'log'
            p.write_text('SECRET\nV411_HOST_STOP event=1 site=151 throws=1\n')
            s=inspect(p,134)
            self.assertIn('events=1 first_site=151 last_site=151 adjacent_throw=1 classified=1 boot_verified=0',s)
            self.assertNotIn('SECRET',s)
            p.write_text('V411_HOST_STOP event=2 site=151 throws=1\n')
            self.assertIn('classified=0',inspect(p,134))
if __name__=='__main__':unittest.main()
