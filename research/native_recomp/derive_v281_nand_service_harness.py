#!/usr/bin/env python3
"""V281 read-only original Wii NAND guarded-source entry census.

Compose verified V278 native derivation in a child Python process.
Observe only authentic 0x8051E150 entries after NAND callback begins.
No guest code, registers, IPC requests, IOS responses or status modified.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
GLOBAL="static unsigned v278_entries=0u,v278_pre=0u,v278_post=0u;"
TRACE="void trace_call(uint32_t addr, CPUContext&ctx){"
RESET="nwii::runtime::v278_entries=0u;"
FRONTIER="    if(v260_post_calls==64u){"

OBSERVER="""void trace_call(uint32_t addr, CPUContext&ctx){
  // V281: inspect original NAND-child service call only in the
  // restored authentic callback path, before and after V259 IPC reentry.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     addr==0x8051e150u){
    const bool guest=ctx.pc==addr&&
          ctx.gpr[13]==v147_first_r13;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool child=ctx.lr==0x8052fb10u;
    const unsigned phase=(v259_ipc_seen==1u)?1u:0u;
    ++v281_entries;
    if(phase==1u)++v281_post;else ++v281_pre;
    if(child)++v281_child;
    check(guest&&mapped&&v281_entries<=256u,
          "V281 native NAND service entry ABI differs");
    std::cout<<"V281_SERVICE_ENTRY n="<<v281_entries
             <<" phase="<<phase
             <<" child="<<unsigned(child)
             <<" sc="<<sc
             <<" guest="<<unsigned(guest)
             <<" inst="<<ctx.inst_count<<std::endl;
  }
"""

def only(source:str,anchor:str,repl:str)->str:
    if source.count(anchor)!=1:
        raise ValueError("V281 verified V278 native harness seam changed")
    return source.replace(anchor,repl,1)

def patch(source:str)->str:
    source=only(source,GLOBAL,GLOBAL+"""
static unsigned v281_entries=0u,v281_pre=0u,v281_post=0u,v281_child=0u;""")
    source=only(source,TRACE,OBSERVER)
    source=only(source,RESET,RESET+"""
     nwii::runtime::v281_entries=nwii::runtime::v281_pre=
       nwii::runtime::v281_post=nwii::runtime::v281_child=0u;""")
    source=only(source,FRONTIER,FRONTIER+"""
      std::cout<<"V281_SERVICE_WINDOW pre="<<v281_pre
               <<" post="<<v281_post
               <<" child="<<v281_child
               <<" entries="<<v281_entries<<std::endl;""")
    return source

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v281-guest-") as td:
        prev=Path(td)/"v278.cpp"
        result=subprocess.run(
            [sys.executable,str(HERE/"derive_v278_fca4_entry_harness.py"),
             str(a.source),str(prev)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if result.returncode:
            raise ValueError("V281 inherited V278 source derivation failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(prev.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
