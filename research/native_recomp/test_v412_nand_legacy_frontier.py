#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v412_nand_legacy_frontier import patch,RESUME,STOP

FILL='void spare{0}(CPU& ctx){{ctx.is_running=false;}}\n'
SOURCE=r'''#include <iostream>
struct CPU{bool is_running=true; unsigned lr=1;};
struct ExceptionStop{};
// V410_NAND_GUEST_RUN_EXIT calls=
// V405_NAND_SECOND_HALF tail_calls=
// if(owned||v396_calls==96u){
'''+''.join(FILL.format(i) for i in range(11))+r'''
void guest(CPU& ctx,bool auth,unsigned v396_calls){
  bool v250_candidate_mode=auth,v388_active=true,v389_after_y1=true;
  unsigned v250_nand_seen=1,v389_flag_seen=1,v395_next_seen=1;
  unsigned v260_post_calls=63,v260_frontier_seen=0;
  unsigned v260_frontier_pc=0,v260_frontier_lr=0,addr=7;
  if(v260_frontier_seen==0){
    ++v260_post_calls;
    // V260 post-IPC original guest bounded call context invalid
    if(v260_post_calls==64u){
      v260_frontier_pc=addr;
      v260_frontier_lr=ctx.lr;
      ++v260_frontier_seen;
      std::cout<<"V260_CALL_FRONTIER guest="<<v260_frontier_seen
               <<v260_frontier_pc<<v260_frontier_lr<<std::endl;
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
}
'''+''.join(FILL.format(i) for i in range(11,18))+r'''
int main(){
  for(unsigned n: {49u,50u,95u,96u})for(bool auth:{false,true}){
    CPU c;bool stopped=false;
    try{guest(c,auth,n);}catch(const ExceptionStop&){stopped=true;}
    const bool expected=!(auth&&n>=50u&&n<96u);
    if(stopped!=expected||c.is_running==expected)return 1;
  }
  return 0;
}
'''
class Tests(unittest.TestCase):
    def test_exact_reversible_scope(self):
        out=patch(SOURCE)
        self.assertEqual(out.replace(RESUME,STOP,1),SOURCE)
        self.assertEqual(out.count('V412_LEGACY_FRONTIER continued=1'),1)
        self.assertIn('++v260_frontier_seen;',out)
    def test_reject_changed_site_and_missing_witness(self):
        variants=(SOURCE.replace(FILL.format(0),''),
                  SOURCE.replace(FILL.format(0),'',1)+FILL.format(99),
                  SOURCE.replace('++v260_frontier_seen;',''),
                  SOURCE.replace('ctx.is_running=false;throw ExceptionStop{};',
                                 'ctx.is_running=false;return;',1),
                  patch(SOURCE))
        for v in variants:
            with self.assertRaises(ValueError):patch(v)
    def test_cpp_original_stop_and_scoped_continuation(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ unavailable')
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'fixture.cpp';exe=Path(td)/'fixture'
            src.write_text(patch(SOURCE),encoding='utf-8')
            b=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(b.returncode,0,b.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0)
            self.assertEqual(r.stdout.count('V412_LEGACY_FRONTIER continued=1'),2)
if __name__=='__main__':unittest.main()
