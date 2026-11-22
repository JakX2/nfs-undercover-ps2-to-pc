#!/usr/bin/env python3
"""V269 read-only guest SYSCONF MMU pre-store watch over verified V260 window."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
GLOBAL="uint32_t g_watch_addr=0;"
WATCH="void watch_hit(uint32_t,uint32_t,int){}"
ARM="""    v259_ipc_inst=ctx.inst_count;
    return; // V260: execute genuine 0x8051906C guest body after entry"""
RESET="nwii::runtime::v259_ipc_seen=0u;"
FRONTIER="    if(v260_post_calls==64u){"

WATCHER="""void watch_hit(uint32_t addr,uint32_t value,int width){
  // This callback fires BEFORE the guest MMU byte store.
  if(!v250_candidate_mode||!v269_watch_armed||
     v259_ipc_seen!=1u||width!=8||g_watch_addr==0u)return;
  if((addr&0x3fffffffu)!=(g_watch_addr&0x3fffffffu))return;
  CPUContext* cpu=ipc70_ram.cpu;
  if(!cpu||cpu->inst_count<=v259_ipc_inst)return;
  const bool guest=cpu->gpr[13]==v147_first_r13&&
          cpu->inst_count>v259_ipc_inst;
  const uint32_t prior=cpu->mmu.read8(g_watch_addr);
  ++v269_write_seq;
  check(v269_write_seq<=512u&&guest,
        "V269 bounded authentic SC status write context invalid");
  std::cout<<"V269_SC_WRITE n="<<v269_write_seq
           <<" before="<<prior<<" next="<<(value&255u)
           <<" width="<<width<<" guest="<<guest
           <<" inst="<<cpu->inst_count<<std::endl;
}"""

def replace_one(source,old,new):
    if source.count(old)!=1:
        raise ValueError("V269 owner-verified native harness anchor changed")
    return source.replace(old,new,1)

def patch(source:str)->str:
    source=replace_one(source,GLOBAL,GLOBAL+"""
static bool v269_watch_armed=false;
static unsigned v269_write_seq=0u;""")
    source=replace_one(source,WATCH,WATCHER)
    source=replace_one(source,ARM,ARM.replace(
        "    return;","    g_watch_addr=scaddr;\n    v269_watch_armed=true;v269_write_seq=0u;\n    return;"))
    source=replace_one(source,RESET,RESET+"""
     nwii::runtime::v269_watch_armed=false;
     nwii::runtime::v269_write_seq=0u;
     nwii::runtime::g_watch_addr=0u;""")
    source=replace_one(source,FRONTIER,FRONTIER+"""
      g_watch_addr=0u;v269_watch_armed=false;""")
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v269-guest-") as td:
        intermediate=Path(td)/"v262.cpp"
        proc=subprocess.run(
            [sys.executable,str(HERE/"derive_v262_ipc_state_harness.py"),
             str(a.source),str(intermediate)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if proc.returncode:
            raise ValueError("V269 V262 native source derivation failed")
        data=patch(intermediate.read_text(encoding="utf-8"))
        with a.output.open("x",encoding="utf-8") as out:
            out.write(data)
    return 0

if __name__=="__main__":
    sys.exit(main())
