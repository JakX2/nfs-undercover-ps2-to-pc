#!/usr/bin/env python3
"""V206: run the original PowerPC IPC handler after both genuine second-Y2 W1C writes.

V205 owner-original executed the PPCCTRL Y2 and Hollywood PPC_FLAG stores,
lowering the external interrupt while the second IOS completion remained
queued. Continue authentic guest execution until the first subsequent native
PowerPC function entry. Sample the bus, queue, IRQ coherence and SC byte
without scheduling any host reply or patching CPU/memory state.
"""
import argparse
from pathlib import Path
from derive_v205_sc_y2_flag_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER

STOP='''       ++v205_flag_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }'''
CONTINUE='''       ++v205_flag_seen;
       v206_after_flag_inst=ipc70_ram.cpu->inst_count;
       // Continue the original IRQ handler after its Hollywood W1C.
     }'''
OBSERVER='''  if(v196_live&&v205_flag_seen==1u&&v206_next_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&M::Y2)==0u)&&((*flag&H::IPC_PPC)==0u);
    const bool down=!ipc70_bus.external_irq_level();
    const bool queue=ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request();
    const bool guest=ctx.pc==addr&&ctx.gpr[13]==v202_first_r13&&
          v203_distinct_seen==1u&&v204_ack_seen==1u;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u&&(addr&3u)==0u;
    const bool stepped=ctx.inst_count>v206_after_flag_inst;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&B::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const bool sc=mapped&&ctx.mmu.read8(sc_addr)==1u;
    const bool ee=(ctx.msr&B::MSR_EE)!=0u;
    std::cout<<"V206_Y2_POST_FLAG call=1 clear="<<clear
             <<" down="<<down<<" queue="<<queue
             <<" guest="<<guest<<" caller="<<caller
             <<" stepped="<<stepped<<" coherent="<<coherent
             <<" mapped="<<mapped<<" sc="<<sc
             <<" ee="<<ee<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(clear&&down&&queue&&guest&&caller&&stepped&&
          coherent&&mapped&&sc,
          "V206 original post-Hollywood-ACK guest successor lost verified IRQ state");
    v206_next_pc=addr;v206_next_lr=ctx.lr;
    ++v206_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v196_handler_seen==1u&&
            nwii::runtime::v197_dispatch_seen==1u&&
            nwii::runtime::v198_time_seen==1u&&
            nwii::runtime::v199_disable_seen==1u&&
            nwii::runtime::v200_ipc_seen==1u&&
            nwii::runtime::v201_leaf_seen==1u&&
            nwii::runtime::v202_next_seen==1u&&
            nwii::runtime::v203_distinct_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_next_seen==1u&&
            !c.is_running&&c.pc==nwii::runtime::v206_next_pc&&
            c.lr==nwii::runtime::v206_next_lr&&
            c.pc>=0x80400000u&&c.pc<0x80600000u,
            "V206 original PowerPC IRQ handler did not reach post-ACK native call");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V206 original second Y2 Hollywood flag checkpoint changed")
    s=once(s,STATE,STATE+'''
 static unsigned v206_next_seen=0u;
 static uint64_t v206_after_flag_inst=0u;
 static uint32_t v206_next_pc=0u,v206_next_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v206_next_seen=0u;
     nwii::runtime::v206_after_flag_inst=0u;
     nwii::runtime::v206_next_pc=nwii::runtime::v206_next_lr=0u;''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
