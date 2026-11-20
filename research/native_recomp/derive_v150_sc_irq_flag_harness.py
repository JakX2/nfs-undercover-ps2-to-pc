#!/usr/bin/env python3
"""V150 run authentic Wii SC interrupt from PPCCTRL Y2 ACK to Hollywood flag W1C.

V149's original MMIO PPCCTRL write executes and is checked but no longer stops
the test. Only the next original Hollywood IPC interrupt-flag write, handled by
the same unchanged native bus, can finish this owner-private checkpoint.
The guest code, IOS reply queue and SC status byte are not altered by hooks.
"""
import argparse
from pathlib import Path
from derive_v149_sc_ipc_ack_harness import derive as previous, NEXT_TRIAL as TRIAL
from derive_v147_sc_ipc_next_harness import V146_OBSERVER

STATE="static unsigned v149_helper_seen=0,v149_ack_seen=0;"
RESET="nwii::runtime::v149_helper_seen=nwii::runtime::v149_ack_seen=0u;"
V146_ONCE='''   if(v141_live&&v145_ipc_seen==1u&&v146_leaf_seen==0u&&
      (addr==0x8051905cu||addr==0x8051906cu||addr==0x8051b060u)){'''
MMIO_STOP='''       ++v149_ack_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
     return;'''
MMIO_CONTINUE='''       ++v149_ack_seen;
     }
     if(v141_live&&v149_ack_seen==1u&&v150_flag_seen==0u&&
        (addr==B::IPC+H::PPC_FLAG||addr==B::MIRROR+H::PPC_FLAG)){
       const auto flags=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
       const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const bool w1c=(value&H::IPC_PPC)!=0u&&flags.has_value()&&
                      ((*flags&H::IPC_PPC)==0u);
       const bool ctrl_clear=ctrl.has_value()&&((*ctrl&M::Y2)==0u);
       const bool irq_down=!ipc70_bus.external_irq_level();
       const bool queued=ipc70_bus.services().queued_replies()==1u;
       const bool guest=ipc70_ram.cpu!=nullptr&&
                        (ipc70_ram.cpu->msr&0x8000u)==0u;
       std::cout<<"V150_SC_IRQ_CLEAR write=1 w1c="<<w1c
                <<" ctrl="<<ctrl_clear<<" irq_down="<<irq_down
                <<" queued="<<queued<<" guest="<<guest<<std::endl;
       check(w1c&&ctrl_clear&&irq_down&&queued&&guest,
             "V150 original SC IPC Hollywood flag W1C did not lower IRQ");
       ++v150_flag_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
     return;'''
NEXT_TRIAL='''       check(v141_stopped&&nwii::runtime::v141_vector_seen==1u&&
             nwii::runtime::v141_handler_seen==1u&&
             nwii::runtime::v142_dispatch_seen==1u&&
             nwii::runtime::v143_time_seen==1u&&
             nwii::runtime::v144_disable_seen==1u&&
             nwii::runtime::v145_ipc_seen==1u&&
             nwii::runtime::v146_leaf_seen==1u&&
             nwii::runtime::v147_next_seen==1u&&
             nwii::runtime::v148_distinct_seen==1u&&
             nwii::runtime::v149_helper_seen==1u&&
             nwii::runtime::v149_ack_seen==1u&&
             nwii::runtime::v150_flag_seen==1u&&!c.is_running,
             "V150 original SC IRQ failed to clear Hollywood IPC interrupt flag");'''

def once(s:str,old:str,new:str)->str:
    n=s.count(old)
    if n!=1:raise ValueError(f"V150 source-only anchor count={n}: {old[:75]}")
    return s.replace(old,new,1)

def derive(source:str)->str:
    s=previous(source)
    s=once(s,STATE,STATE+"\n static unsigned v150_flag_seen=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v150_flag_seen=0u;")
    # V146 is the first IPC handler leaf observer, not a general helper gate:
    # later legitimate leaf calls must not reenter its one-time assertion.
    s=once(s,V146_OBSERVER,V146_ONCE)
    s=once(s,MMIO_STOP,MMIO_CONTINUE)
    s=once(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
