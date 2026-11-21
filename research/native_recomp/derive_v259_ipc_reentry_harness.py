#!/usr/bin/env python3
"""V259: original restored NAND callback reaches genuine IPC call boundary.

V258 owner saw 0x8051906C called from 0x805192EC during the restored NAND
successor, before a 32-call observation ceiling. Capture that exact original
PowerPC entry, not a synthetic MMIO write or successful IOS response.
"""
import argparse
from pathlib import Path
from derive_v258_nand_callee_return_harness import (
    derive as previous, CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  // The original NAND callback now enters the original IPC-side helper.
  // Record only a guest function entry, not an alleged IPC submission.
  if(v250_candidate_mode&&v257_next_seen==1u&&
     v258_return_seen==0u&&v259_ipc_seen==0u&&
     ctx.inst_count>v258_callee_inst&&
     addr==0x8051906cu&&ctx.lr==0x805192ecu){
    const bool guest=ctx.pc==addr&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr==0x805192ecu&&
          (ctx.lr&3u)==0u;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool reply=v153_phys!=0u&&
          ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    const bool second=v183_second_phys!=0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    std::cout<<"V259_IPC_REENTRY guest="<<guest
             <<" caller="<<caller<<" mapped="<<mapped
             <<" coherent="<<coherent<<" reply="<<reply
             <<" second="<<second<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&mapped&&coherent,
          "V259 original NAND IPC reentry ABI or IRQ state differs");
    ++v259_ipc_seen;
    v259_ipc_sc=sc;
    v259_ipc_inst=ctx.inst_count;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CANDIDATE='''      if(v250_probe&&nwii::runtime::v259_ipc_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&
              nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v254_next_seen==1u&&
              nwii::runtime::v256_return_seen==1u&&
              nwii::runtime::v257_next_seen==1u;
        const bool reentry=c.pc==0x8051906cu&&
              c.lr==0x805192ecu&&!c.is_running&&
              c.inst_count==nwii::runtime::v259_ipc_inst;
        const bool memory=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v259_ipc_sc;
        std::cout<<"V259_NAND_GUEST callback="<<callback
                 <<" reentry="<<reentry<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&reentry&&memory,
              "V259 original IPC reentry did not persist in guest context");
        continue; // candidate only; baseline V244 owner path unchanged
      }'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(TRACE_ANCHOR)!=1 or s.count(PREVIOUS_CANDIDATE)!=1:
        raise ValueError("V259 inherited V258 callback and guest source seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v259_ipc_seen=0u;
 static uint64_t v259_ipc_inst=0u;
 static uint32_t v259_ipc_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v259_ipc_seen=0u;
     nwii::runtime::v259_ipc_inst=0u;
     nwii::runtime::v259_ipc_sc=0u;''')
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
