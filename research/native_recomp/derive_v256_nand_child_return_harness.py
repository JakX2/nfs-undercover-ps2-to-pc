#!/usr/bin/env python3
"""V256 continue original NAND child 0x8052FA60 to native BLR return.

V254 owner verified 16/16 that original translated nandOpenCallback
calls 0x8052FA60 with LR 0x8051E0B8. This stage executes that original
child and probes only for the natural return PC at the NAND callback,
using PowerPC runner's existing callback dispatch.
"""
import argparse
from pathlib import Path
from derive_v254_nand_first_child_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    V178_SCOPED as PREVIOUS_V178, CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v254_next_pc=addr;v254_next_lr=ctx.lr;
    v254_final_sc=sc;
    ++v254_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8052fa60u&&ctx.lr==0x8051e0b8u&&
          guest&&caller&&reply&&mapped&&frame&&coherent,
          "V256 original NAND child entry differs from verified V254");
    v254_next_pc=addr;v254_next_lr=ctx.lr;
    v254_final_sc=sc;
    ++v254_next_seen;
    v256_child_inst=ctx.inst_count;
    return; // execute original child 0x8052FA60 and its native BLR
  }'''
V178_CHILD='''    // Candidate-only: the authentic NAND callback called first,
    // then its original child 0x8052FA60. Historical V178 was designed
    // for the reduced NOP callback fixture, not this restored PPC body.
    if(v250_candidate_mode&&v252_nand_entry_seen==1u&&
       ((addr==0x8051e06cu&&ctx.lr==0x804f0f54u)||
        (v254_next_seen==1u&&addr==0x8052fa60u&&
         ctx.lr==0x8051e0b8u)))
      return;
    check(addr==0x80545100u&&ctx.lr==0x804f1e40u,
          "V178 owner-original SC reply callee differs from V177 proof");'''
CALLBACK_ANCHOR='''bool process_pending_callbacks(CPUContext& ctx){'''
CALLBACK='''bool process_pending_callbacks(CPUContext& ctx){
  // Read-only hook at the game-authentic child-to-NAND return.
  // The PowerPC AOT function must execute itself: this never copies
  // registers, edits PPC memory, forces a branch, or invents IOS replies.
  if(v250_candidate_mode&&v254_next_seen==1u&&v256_return_seen==0u&&
     ctx.pc==0x8051e0b8u&&ctx.inst_count>v256_child_inst){
    using I=undercover::wii::StmIos;
    const bool child=v254_next_pc==0x8052fa60u&&
          v254_next_lr==0x8051e0b8u;
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          ctx.inst_count>v256_child_inst;
    const bool frame=v250_initial_sp>=ctx.gpr[1]&&
          v250_initial_sp-ctx.gpr[1]>=16u;
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==I::Reply;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool pending=v183_second_phys==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    std::cout<<"V256_NAND_RETURN child="<<child
             <<" guest="<<guest<<" frame="<<frame
             <<" reply="<<reply<<" mapped="<<mapped
             <<" pending="<<pending<<" coherent="<<coherent
             <<" sc="<<sc<<std::endl;
    check(child&&guest&&frame&&reply&&mapped&&pending&&coherent,
          "V256 original Wii NAND child failed to return via genuine PowerPC");
    v256_return_sc=sc;
    ++v256_return_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CANDIDATE='''      if(v250_probe&&nwii::runtime::v256_return_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v254_next_seen==1u;
        const bool returned=nwii::runtime::v256_return_seen==1u&&
              c.pc==0x8051e0b8u&&!c.is_running&&
              c.inst_count>nwii::runtime::v256_child_inst;
        const bool memory=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v256_return_sc;
        std::cout<<"V256_NAND_GUEST callback="<<callback
                 <<" returned="<<returned<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&returned&&memory,
              "V256 NAND child return did not persist in guest context");
        continue; // owner-callback only; owner baseline V163 remains
      }'''

def derive(source:str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
            s.count(PREVIOUS_V178)!=1 or
            s.count(PREVIOUS_CANDIDATE)!=1 or
            s.count(CALLBACK_ANCHOR)!=1):
        raise ValueError("V256 owner-authenticated V254 child callback seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v256_return_seen=0u;
 static uint64_t v256_child_inst=0u;
 static uint32_t v256_return_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v256_return_seen=0u;
     nwii::runtime::v256_child_inst=0u;
     nwii::runtime::v256_return_sc=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,PREVIOUS_V178,V178_CHILD)
    s=once(s,CALLBACK_ANCHOR,CALLBACK)
    s=once(s,PREVIOUS_CANDIDATE,CANDIDATE)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
