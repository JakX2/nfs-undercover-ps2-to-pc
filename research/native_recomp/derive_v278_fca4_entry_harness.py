#!/usr/bin/env python3
"""V278: original Wii NAND status-writer entry census, no guest modification.

Derive the proven V269 native harness in a child Python process. Inject
read-only callback-entry observations for original PC 0x8052FCA4,
bounded to 16 owner trials and their authentic 64-call frontiers.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
GLOBAL="static bool v269_watch_armed=false;"
TRACE="void trace_call(uint32_t addr, CPUContext&ctx){"
RESET="nwii::runtime::v259_ipc_seen=0u;"
FRONTIER="    if(v260_post_calls==64u){"

OBSERVER="""void trace_call(uint32_t addr, CPUContext&ctx){
  // V278: the original NAND child calls this original status writer.
  // Observe only genuine translated guest entries; no register or
  // original byte is modified by this observer.
  if(v250_candidate_mode&&addr==0x8052fca4u){
    const bool guest=ctx.pc==addr&&
          ctx.gpr[13]==v147_first_r13;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(scaddr):0u;
    const bool from_child=ctx.lr>=0x8052fa60u&&ctx.lr<0x8052fb30u;
    const unsigned phase=(v259_ipc_seen==1u)?1u:0u;
    ++v278_entries;
    if(phase==1u)++v278_post;else ++v278_pre;
    check(guest&&mapped&&v278_entries<=256u,
          "V278 original Wii SC callback entry or memory invalid");
    std::cout<<"V278_FCA4_ENTRY n="<<v278_entries
             <<" phase="<<phase
             <<" cb="<<unsigned(v250_cb_seen==1u)
             <<" nand="<<unsigned(v250_nand_seen==1u)
             <<" child="<<unsigned(from_child)
             <<" sc="<<status
             <<" guest="<<unsigned(guest)
             <<" inst="<<ctx.inst_count<<std::endl;
  }
"""

def only(source:str,anchor:str,replacement:str)->str:
    if source.count(anchor)!=1:
        raise ValueError("V278 authenticated V269 native harness seam changed")
    return source.replace(anchor,replacement,1)

def patch(source:str)->str:
    source=only(source,GLOBAL,GLOBAL+"""
static unsigned v278_entries=0u,v278_pre=0u,v278_post=0u;""")
    source=only(source,TRACE,OBSERVER)
    source=only(source,RESET,RESET+"""
     nwii::runtime::v278_entries=0u;
     nwii::runtime::v278_pre=nwii::runtime::v278_post=0u;""")
    source=only(source,FRONTIER,FRONTIER+"""
      std::cout<<"V278_SC_CALL_WINDOW pre="<<v278_pre
               <<" post="<<v278_post
               <<" events="<<v278_entries<<std::endl;""")
    return source

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v278-guest-") as td:
        parent=Path(td)/"v269.cpp"
        result=subprocess.run(
            [sys.executable,str(HERE/"derive_v269_sc_write_harness.py"),
             str(a.source),str(parent)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if result.returncode:
            raise ValueError("V278 inherited V269 source generation failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(parent.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
