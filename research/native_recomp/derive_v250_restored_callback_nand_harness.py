#!/usr/bin/env python3
"""V250 candidate-only authentic first callback -> NAND bctrl checkpoint.

Accept owner-callback only as an explicit extra test mode. The existing
verified 'owner' mode still executes all V244 assertions unmodified.
At the original first _isfsFuncCb entry, record only public ABI shape.
Execute the restored translated PPC until genuine NAND callback entry
with the expected 16-byte callback frame, CTR and linked LR.
No guest register writes, forced branch, synthetic IOS replies or
proprietary code/bytes are committed.
"""
import argparse
from pathlib import Path
from derive_v194_osrestore_next_harness import STATE, RESET, once

OWNER='''  const bool owner=std::string(argv[2])=="owner";'''
OWNER_NEW='''  const bool v250_probe=std::string(argv[2])=="owner-callback";
  const bool owner=v250_probe||std::string(argv[2])=="owner";
  nwii::runtime::v250_candidate_mode=v250_probe;'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''  // V250 candidate-only read-only probe: the authentic restored
  // _isfsFuncCb must execute its 16-byte PPC stack prologue and bctrl.
  if(v250_candidate_mode&&v250_cb_seen==0u&&ctx.pc==addr&&
     addr==0x804f0e04u&&v183_second_phys==0u){
    v250_initial_sp=ctx.gpr[1];v250_initial_r3=ctx.gpr[3];
    v250_userdata=ctx.gpr[4];v250_initial_inst=ctx.inst_count;
    ++v250_cb_seen;
    const bool first_reply=v153_phys!=0u&&
          ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    std::cout<<"V250_CB_BEGIN candidate=1 reply="<<first_reply
             <<" captured=1"<<std::endl;
  }
  if(v250_candidate_mode&&v250_cb_seen==1u&&v250_nand_seen==0u&&
     ctx.pc==addr&&addr==0x8051e06cu){
    const bool auth=v244_cb_seen==1u&&v244_cb_registered&&
          v244_cb_abi&&v244_nested_target==addr;
    const bool frame=v250_initial_sp>=ctx.gpr[1]&&
          v250_initial_sp-ctx.gpr[1]==16u;
    const bool link=ctx.lr==0x804f0f54u;
    const bool ctr=ctx.ctr==addr;
    const bool abi=ctx.gpr[3]==v250_initial_r3;
    const bool mapped=v250_userdata<=0xfffffef8u&&
          ctx.mmu.get_ptr(v250_userdata+260u)!=nullptr&&
          ctx.mmu.get_ptr(v250_userdata+263u)!=nullptr;
    const bool userdata=mapped&&
          ctx.gpr[4]==ctx.mmu.read32(v250_userdata+260u);
    const bool progressed=ctx.inst_count>v250_initial_inst;
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    std::cout<<"V250_NAND_BCTRL auth="<<auth<<" frame16="<<frame
             <<" link="<<link<<" ctr="<<ctr<<" abi="<<abi
             <<" userdata="<<userdata<<" progressed="<<progressed
             <<" reply="<<reply<<std::endl;
    check(auth&&frame&&link&&ctr&&abi&&userdata&&progressed&&reply,
          "V250 restored original callback did not enter NAND via genuine bctrl");
    ++v250_nand_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
POST='''      check(exception_stop,"exception initialization did not reach exact test-only syscall");'''
CHECK='''      if(v250_probe){
        check(nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              c.pc==0x8051e06cu&&!c.is_running,
              "V250 original restored callback NAND checkpoint missing");
        std::cout<<"V250_TRIAL_PASS trial="<<trial+1u<<std::endl;
        continue; // only candidate mode skips V244's unrelated later stop
      }
'''

def derive(source:str)->str:
    s=source
    if s.count(OWNER)!=1 or s.count(TRACE_ANCHOR)!=1 or s.count(POST)!=1:
        raise ValueError("V250 authenticated public harness owner/probe seam changed")
    if "V244 original callback nested link provenance missing" not in s:
        raise ValueError("V250 requires owner-verified V244 callback harness")
    s=once(s,STATE,STATE+'''
 static bool v250_candidate_mode=false;
 static unsigned v250_cb_seen=0u,v250_nand_seen=0u;
 static uint32_t v250_initial_sp=0u,v250_initial_r3=0u,v250_userdata=0u;
 static uint64_t v250_initial_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v250_cb_seen=nwii::runtime::v250_nand_seen=0u;
     nwii::runtime::v250_initial_sp=nwii::runtime::v250_initial_r3=
          nwii::runtime::v250_userdata=0u;
     nwii::runtime::v250_initial_inst=0u;''')
    s=once(s,OWNER,OWNER_NEW)
    s=once(s,TRACE_ANCHOR,TRACE_ANCHOR+"\n"+OBSERVER)
    s=once(s,POST,POST+"\n"+CHECK)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
