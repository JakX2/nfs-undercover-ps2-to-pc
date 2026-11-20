#!/usr/bin/env python3
"""V153 bridge owner-original SC interrupt ACK to existing post-IRQ IOS reply step.

V152 proved the original guest calls 0x80529434 from 0x80526CB0 after the IPC
handler executes its control/status W1C writes. V77's already-tested owner
harness has a post-ACK, explicit host IOS service step at precisely that
original call boundary. Allow V77 to perform that one step, then verify the
actual native IOS reply wire and fresh Broadway interrupt.

This does not execute Starlet ARM code, force SC readiness or resume the
original async callback. It also stops before running 0x80529434's body.
"""
import argparse
from pathlib import Path
from derive_v152_sc_post_helper_harness import (
    derive as previous,
    STATE, RESET, OBSERVER, NEXT_TRIAL as TRIAL,
)

NEXT_OBSERVER = OBSERVER.replace(
    '''     ++v152_next_seen;
     ctx.is_running=false;throw ExceptionStop{};
   }''',
    '''     const bool route=addr==POST_OWNER&&ctx.lr==0x80526cb0u&&
                      irq76_ipc==1u&&ack77_reply==0u;
     check(route,"V153 original SC IRQ did not reach authenticated post-ACK yield call");
     ++v152_next_seen;
     ++v153_bridge_seen;
     // Fall through to the inherited V77 handler. Its single native IOS
     // tick is allowed only after authentic Broadway W1C completion.
   }''',
)

NEXT_TRIAL = '''       using V153Bus=undercover::wii::IosBus;
       using V153Mail=undercover::wii::IpcMailbox;
       using V153Irq=undercover::wii::HollywoodIrq;
       using V153Ios=undercover::wii::StmIos;
       const auto v153_ctrl=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Mail::PPCCTRL);
       const auto v153_arm=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Mail::ARMMSG);
       const auto v153_flags=nwii::runtime::ipc70_bus.read32(
             V153Bus::IPC+V153Irq::PPC_FLAG);
       const bool v153_bridge=nwii::runtime::v153_bridge_seen==1u&&
             nwii::runtime::v152_next_seen==1u&&
             nwii::runtime::ack77_reply==1u&&c.pc==POST_OWNER&&
             c.lr==0x80526cb0u&&!c.is_running;
       const bool v153_wire=nwii::runtime::ipc70_ram.read32(
             nwii::runtime::submit72_phys)==V153Ios::Reply&&
             nwii::runtime::ipc70_ram.read32(
             nwii::runtime::submit72_phys+4u)==0u&&
             nwii::runtime::ipc70_ram.read32(
             nwii::runtime::submit72_phys+8u)==V153Ios::Open&&
             v153_arm.has_value()&&*v153_arm==nwii::runtime::submit72_phys;
       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             ((*v153_ctrl&V153Mail::Y1)!=0u)&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);
       const bool v153_queue=nwii::runtime::ipc70_bus.services().queued_replies()==0u;
       const bool v153_irq=nwii::runtime::ipc70_bus.external_irq_level()&&
             !nwii::runtime::ipc70_bus.external_exception_pending(c.msr)&&
             (c.msr&V153Bus::MSR_EE)==0u;
       std::cout<<"V153_SC_REPLY bridge="<<v153_bridge
                <<" wire="<<v153_wire<<" mail="<<v153_mail
                <<" drained="<<v153_queue<<" irq="<<v153_irq<<std::endl;
       check(v153_bridge&&v153_wire&&v153_mail&&v153_queue&&v153_irq&&
             nwii::runtime::v149_ack_seen==1u&&
             nwii::runtime::v150_flag_seen==1u&&
             nwii::runtime::v151_next_seen==1u,
             "V153 owner-original SC ACK to native IOS reply integration failed");'''

def once(source: str, old: str, new: str) -> str:
    count=source.count(old)
    if count!=1:
        raise ValueError("V153 original-free source anchor count differs: "+str(count))
    return source.replace(old,new,1)

def derive(source: str) -> str:
    if NEXT_OBSERVER==OBSERVER:
        raise ValueError("V153 observer transformation failed closed")
    s=previous(source)
    s=once(s,STATE,STATE+"\n static unsigned v153_bridge_seen=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v153_bridge_seen=0u;")
    s=once(s,OBSERVER,NEXT_OBSERVER)
    s=once(s,TRIAL,TRIAL.replace(
        '''             nwii::runtime::v152_next_seen==1u&&!c.is_running,''',
        '''             nwii::runtime::v152_next_seen==1u&&
             nwii::runtime::v153_bridge_seen==1u&&!c.is_running,''',1).replace(
        "V152 original post-IRQ helper did not execute until next native guest call",
        "V153 original SC IRQ did not reach authenticated V77 reply handoff",1)
        +"\n"+NEXT_TRIAL)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
