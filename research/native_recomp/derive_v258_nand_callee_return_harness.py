#!/usr/bin/env python3
"""V258: execute authentic NAND callback successor 0x8051AD3C to PPC return.

V257 owner-original 16/16 observed entry 0x8051AD3C with LR 0x804F0F68,
after the verified NAND child returned. Execute the original translated
callee and stop only if the genuine CPU resumes at its saved return PC.
No guest-PC assignment, IOS spoof, memory edit, or host-return injection.
"""
import argparse
from pathlib import Path
from derive_v257_nand_postchild_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v256_nand_child_return_harness import V178_CHILD as PREVIOUS_V178
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v257_next_pc=addr;v257_next_lr=ctx.lr;v257_next_sc=sc;
    ++v257_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051ad3cu&&ctx.lr==0x804f0f68u&&
          guest&&caller&&code&&mapped&&reply&&coherent,
          "V258 owner-original NAND successor differs from V257");
    v257_next_pc=addr;v257_next_lr=ctx.lr;v257_next_sc=sc;
    ++v257_next_seen;
    v258_callee_inst=ctx.inst_count;
    return; // execute actual translated 0x8051AD3C PowerPC body
  }'''
V178_TAIL='''        (v254_next_seen==1u&&addr==0x8052fa60u&&
         ctx.lr==0x8051e0b8u)))'''
V178_TAIL_NEXT='''        (v254_next_seen==1u&&addr==0x8052fa60u&&
         ctx.lr==0x8051e0b8u)||
        (v257_next_seen==1u&&addr==0x8051ad3cu&&
         ctx.lr==0x804f0f68u)))'''
V178_NESTED='''    // This opt-in restored guest callback is beyond the reduced V178
    // callback fixture. Verify its first two owner-observed nested calls,
    // then trace only bounded, valid native guest calls in this phase.
    // The historical V178 assertion remains active in all other modes.
    if(v250_candidate_mode&&v257_next_seen==1u&&
       v258_return_seen==0u&&ctx.inst_count>v258_callee_inst){
      ++v258_nested_guest_calls;
      const bool code=ctx.pc==addr&&
            addr>=0x80000000u&&addr<0x80600000u&&
            (addr&3u)==0u;
      const bool caller=ctx.lr>=0x80000000u&&
            ctx.lr<0x80600000u&&(ctx.lr&3u)==0u;
      const bool regs=ctx.gpr[13]==v147_first_r13;
      const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
            (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
             ipc70_bus.external_irq_level());
      const bool first=v258_nested_guest_calls!=1u||
            (addr==0x805265acu&&ctx.lr==0x8051ad64u);
      const bool second=v258_nested_guest_calls!=2u||
            (addr==0x805265d4u&&ctx.lr==0x8051af08u);
      check(code&&caller&&regs&&coherent&&first&&second&&
            v258_nested_guest_calls<=12u,
            "V258 restored NAND nested call exceeds verified bounded phase");
      return; // instrumentation only; original AOT call still executes
    }
'''
V178_CHECK='''    check(addr==0x80545100u&&ctx.lr==0x804f1e40u,
          "V178 owner-original SC reply callee differs from V177 proof");'''
V178_DIAG='''    if(v250_candidate_mode&&v257_next_seen==1u&&
       v258_return_seen==0u&&ctx.inst_count>v258_callee_inst){
      const bool code=addr>=0x80000000u&&addr<0x80600000u&&
            (addr&3u)==0u;
      const bool caller=ctx.lr>=0x80000000u&&ctx.lr<0x80600000u&&
            (ctx.lr&3u)==0u;
      const bool regs=ctx.gpr[13]==v147_first_r13;
      std::cout<<"V258_NAND_DEP code="<<code
               <<" caller="<<caller<<" regs="<<regs
               <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
               <<std::dec<<std::endl;
    }
'''
CALLBACK_ANCHOR='''bool process_pending_callbacks(CPUContext& ctx){'''
RETURN_HOOK='''bool process_pending_callbacks(CPUContext& ctx){
  // Observe only an actual PowerPC return after original AOT execution.
  if(v250_candidate_mode&&v257_next_seen==1u&&
     v258_return_seen==0u&&ctx.pc==0x804f0f68u&&
     ctx.inst_count>v258_callee_inst){
    const bool guest=ctx.gpr[13]==v147_first_r13&&
          v257_next_pc==0x8051ad3cu&&
          v257_next_lr==0x804f0f68u;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    const bool pending=v183_second_phys==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    std::cout<<"V258_NAND_CALLEE_RETURN guest="<<guest
             <<" mapped="<<mapped<<" reply="<<reply
             <<" pending="<<pending<<" coherent="<<coherent
             <<" sc="<<sc<<std::endl;
    check(guest&&mapped&&coherent,
          "V258 original guest successor did not return via PPC");
    v258_return_sc=sc;
    ++v258_return_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
CANDIDATE='''      if(v250_probe&&nwii::runtime::v258_return_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v254_next_seen==1u&&
              nwii::runtime::v256_return_seen==1u&&
              nwii::runtime::v257_next_seen==1u;
        const bool returned=nwii::runtime::v258_return_seen==1u&&
              c.pc==0x804f0f68u&&!c.is_running&&
              c.inst_count>nwii::runtime::v258_callee_inst;
        const bool memory=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v258_return_sc;
        std::cout<<"V258_NAND_GUEST callback="<<callback
                 <<" returned="<<returned<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&returned&&memory,
              "V258 original NAND successor return did not persist in guest context");
        continue; // candidate only, preserve original V244 baseline
      }'''

def derive(source:str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(STOP)!=1 or
            PREVIOUS_V178.count(V178_TAIL)!=1 or
            s.count(PREVIOUS_V178)!=1 or
            s.count(PREVIOUS_OBSERVER)!=1 or
            s.count(PREVIOUS_CANDIDATE)!=1 or
            s.count(CALLBACK_ANCHOR)!=1):
        raise ValueError("V258 verified V257 original callee seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v258_return_seen=0u,v258_nested_guest_calls=0u;
 static uint64_t v258_callee_inst=0u;
 static uint32_t v258_return_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v258_return_seen=nwii::runtime::v258_nested_guest_calls=0u;
     nwii::runtime::v258_callee_inst=0u;
     nwii::runtime::v258_return_sc=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    v178=PREVIOUS_V178.replace(V178_TAIL,V178_TAIL_NEXT,1)
    if v178.count(V178_CHECK)!=1:
        raise ValueError("V258 inherited V178 native-call assertion changed")
    s=once(s,PREVIOUS_V178,v178.replace(V178_CHECK,V178_DIAG+V178_NESTED+V178_CHECK,1))
    s=once(s,CALLBACK_ANCHOR,RETURN_HOOK)
    s=once(s,PREVIOUS_CANDIDATE,CANDIDATE)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
