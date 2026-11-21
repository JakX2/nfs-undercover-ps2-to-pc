#!/usr/bin/env python3
"""V257: resume original NAND callback after the verified child BLR.

V256 owner-native proved sixteen genuine child-to-callback returns at
0x8051E0B8. This opt-in candidate-only stage executes past that return and
captures the first subsequent translated PowerPC function entry, without
patching guest PC, registers, memory, IOS responses, or game instructions.
The original baseline owner path and prior tests remain separate.
"""
import argparse
from pathlib import Path
from derive_v256_nand_child_return_harness import (
    derive as previous, CALLBACK as PREVIOUS_CALLBACK,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v256_return_sc=sc;
    ++v256_return_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v256_return_sc=sc;
    ++v256_return_seen;
    v257_return_inst=ctx.inst_count;
    return false; // do not substitute an IRQ or change guest CPU state
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  // One bounded native guest successor after the owner-verified NAND BLR.
  if(v250_candidate_mode&&v256_return_seen==1u&&
     v257_next_seen==0u&&ctx.pc==addr){
    const bool guest=ctx.inst_count>v257_return_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80000000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool code=addr>=0x80000000u&&addr<0x80600000u&&
          (addr&3u)==0u;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    std::cout<<"V257_NAND_NEXT guest="<<guest
             <<" caller="<<caller<<" code="<<code
             <<" mapped="<<mapped<<" reply="<<reply
             <<" coherent="<<coherent<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&code&&mapped&&coherent,
          "V257 original callback did not reach a valid PowerPC successor");
    v257_next_pc=addr;v257_next_lr=ctx.lr;v257_next_sc=sc;
    ++v257_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CANDIDATE='''      if(v250_probe&&nwii::runtime::v257_next_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v254_next_seen==1u&&
              nwii::runtime::v256_return_seen==1u;
        const bool next=nwii::runtime::v257_next_seen==1u&&
              c.pc==nwii::runtime::v257_next_pc&&
              c.lr==nwii::runtime::v257_next_lr&&
              c.inst_count>nwii::runtime::v257_return_inst&&
              !c.is_running;
        const bool memory=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v257_next_sc;
        std::cout<<"V257_NAND_GUEST callback="<<callback
                 <<" next="<<next<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&next&&memory,
              "V257 NAND postchild continuation did not persist in guest context");
        continue; // isolated candidate mode; owner V244 baseline untouched
      }'''

def derive(source:str)->str:
    s=previous(source)
    if (PREVIOUS_CALLBACK.count(STOP)!=1 or
            s.count(PREVIOUS_CALLBACK)!=1 or
            s.count(PREVIOUS_CANDIDATE)!=1 or
            s.count(TRACE_ANCHOR)!=1):
        raise ValueError("V257 verified V256 callback/owner seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v257_next_seen=0u;
 static uint64_t v257_return_inst=0u;
 static uint32_t v257_next_pc=0u,v257_next_lr=0u,v257_next_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v257_next_seen=0u;
     nwii::runtime::v257_return_inst=0u;
     nwii::runtime::v257_next_pc=nwii::runtime::v257_next_lr=
         nwii::runtime::v257_next_sc=0u;''')
    s=once(s,PREVIOUS_CALLBACK,PREVIOUS_CALLBACK.replace(STOP,CONTINUE,1))
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,PREVIOUS_CANDIDATE,CANDIDATE)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
