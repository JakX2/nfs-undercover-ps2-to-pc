#!/usr/bin/env python3
"""V149 execute authentic SC IPC PPCCTRL W1C, not a synthetic acknowledgment.

After V148 reaches 0x8051906C from original callsite 0x80519380, the
original PPC control-write leaf executes. The existing native Wii bus handles
its exact MMIO write. This source-only observer examines the *result* and
stops only after the real write; no guest code or synthetic status is patched.
The later Hollywood IRQ latch and IOS reply remain separately pending.
"""
import argparse
from pathlib import Path
from derive_v148_sc_ipc_distinct_harness import derive as previous, NEXT_TRIAL as TRIAL

STATE="static unsigned v148_more_reads=0,v148_distinct_seen=0;"
RESET="nwii::runtime::v148_more_reads=nwii::runtime::v148_distinct_seen=0u;"
STOP='''     ++v148_distinct_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }'''
CONTINUE='''     check(addr==0x8051906cu&&ctx.lr==0x80519380u,
           "V149 authenticated SC IPC PPCCTRL writer callsite differs");
     ++v148_distinct_seen;++v149_helper_seen;
     return;
   }'''
# V118 monitors the original SC X1 submission. Once that genuine request
# was submitted (post118_x1 == 1), the same hardware writer is reused by the
# later SC IRQ. Do not reinterpret its Y2 W1C as a second X1 submission.
V118_OLD='''   if(post117_send==1u){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;'''
V118_NEW='''   if(post117_send==1u&&post118_x1==0u){
     using B=undercover::wii::IosBus;using M=undercover::wii::IpcMailbox;
     using I=undercover::wii::StmIos;'''
MMIO_OLD='''     check(ipc70_bus.write32(addr,value),"native bus rejected original ACK MMIO write");
     mmio_writes.emplace_back(addr,value);return;'''
MMIO_NEW='''     check(ipc70_bus.write32(addr,value),"native bus rejected original ACK MMIO write");
     mmio_writes.emplace_back(addr,value);
     if(v141_live&&v149_helper_seen==1u&&v149_ack_seen==0u&&
        (addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)){
       const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const bool w1c=(value&M::Y2)!=0u&&control.has_value()&&
                      ((*control&M::Y2)==0u);
       const bool queued=ipc70_bus.services().queued_replies()==1u;
       const bool irq=ipc70_bus.external_irq_level();
       const bool guest=ipc70_ram.cpu!=nullptr&&
                         (ipc70_ram.cpu->msr&0x8000u)==0u&&
                         ipc70_ram.cpu->lr==0x80519380u;
       std::cout<<"V149_SC_IPC_ACK write=1 w1c="<<w1c
                <<" queued="<<queued<<" irq="<<irq
                <<" guest="<<guest<<std::endl;
       check(w1c&&queued&&irq&&guest,
             "V149 original SC PPCCTRL W1C did not preserve pending reply/IRQ");
       ++v149_ack_seen;
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
             nwii::runtime::v149_ack_seen==1u&&!c.is_running,
             "V149 original SC IRQ failed to write PPCCTRL Y2 acknowledgment");'''

def once(s:str,old:str,new:str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V149 owner-native derivation anchor count={n}: {old[:72]}")
    return s.replace(old,new,1)

def derive(source:str)->str:
    s=previous(source)
    s=once(s,STATE,STATE+'''
 static unsigned v149_helper_seen=0,v149_ack_seen=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v149_helper_seen=nwii::runtime::v149_ack_seen=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,V118_OLD,V118_NEW)
    s=once(s,MMIO_OLD,MMIO_NEW)
    s=once(s,TRIAL,NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
