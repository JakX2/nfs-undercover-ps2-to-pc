#!/usr/bin/env python3
"""V172 verify original SC Y1 reply IPC PPCCTRL write-one-to-clear.

V171 authenticated a distinct Wii register-write helper 0x8051906C from
reply-processor LR 0x8051910C. Execute that translated original function,
observe its *actual* Broadway PPCCTRL MMIO store and assert Y1 is cleared
by native W1C semantics. The independent Hollywood PPC_FLAG latch should
remain asserted until guest code acknowledges it separately.
This script only adds after-the-fact assertions and bounded public markers:
no forced register value, guest branch, fake ACK, IOS tick, or callback.
"""
import argparse
import re
from pathlib import Path
from derive_v171_sc_reply_distinct_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL,
)
MMIO_ANCHOR='''     check(ipc70_bus.write32(addr,value),"native bus rejected original ACK MMIO write");
     mmio_writes.emplace_back(addr,value);'''

STOP='''    ++v171_distinct_seen;
    v171_target_pc=addr;v171_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051906cu&&ctx.lr==0x8051910cu,
          "V172 original Y1 reply register writer callsite differs from V171");
    ++v171_distinct_seen;
    return; // run actual Wii PPC IPC control-store helper
  }'''

ACK='''     if(v171_distinct_seen==1u&&v172_y1_ack_seen==0u&&
        (addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)){
       const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const auto flag=ipc70_bus.read32(B::IPC+undercover::wii::HollywoodIrq::PPC_FLAG);
       const bool write=(value&M::Y1)!=0u;
       const bool cleared=control.has_value()&&((*control&M::Y1)==0u);
       const bool latched=flag.has_value()&&
             ((*flag&undercover::wii::HollywoodIrq::IPC_PPC)!=0u)&&
             ipc70_bus.external_irq_level();
       const bool guest=ipc70_ram.cpu!=nullptr&&
             ipc70_ram.cpu->lr==0x8051910cu&&
             ipc70_ram.cpu->gpr[13]==v147_first_r13;
       const bool reply=ipc70_ram.valid(v153_phys,64u)&&
             ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply&&
             ipc70_ram.read32(v153_phys+4u)==v153_fd;
       const uint32_t sc_addr=ipc70_ram.cpu?
             ipc70_ram.cpu->gpr[13]-3176u:0u;
       const bool mapped=guest&&ipc70_ram.cpu->mmu.get_ptr(sc_addr)!=nullptr;
       const uint32_t status=mapped?ipc70_ram.cpu->mmu.read8(sc_addr):0u;
       std::cout<<"V172_SC_REPLY_Y1_ACK write="<<write
                <<" cleared="<<cleared<<" latched="<<latched
                <<" guest="<<guest<<" reply="<<reply
                <<" mapped="<<mapped<<" status="<<status<<std::endl;
       check(write&&cleared&&latched&&guest&&reply&&mapped,
             "V172 original Wii reply IPC write did not perform Y1 W1C");
       ++v172_y1_ack_seen;
       ipc70_ram.cpu->is_running=false;
       throw ExceptionStop{};
     }
'''
# The existing original PPC MMIO callback has an original first-IRQ W1C
# observer. Do not displace it, only add a second-phase observation before
# its final return. Reject ambiguous or duplicated writer callback shapes.
def add_ack_observer(s: str)->str:
    # Later milestones appended authentic IRQ checks inside this writer
    # callback, so the *entire* V149 MMIO block is no longer verbatim.
    # This two-line bus-write anchor stays unique across all successors.
    if s.count(MMIO_ANCHOR)!=1:
        raise ValueError("V172 original Broadway MMIO bus write anchor differs")
    return s.replace(MMIO_ANCHOR,MMIO_ANCHOR+"\n"+ACK.rstrip("\n"),1)

# V153 originally proves the reply became pending at a *previous* original
# guest checkpoint. Its end-of-trial Y1=1 assertion is no longer current
# after the *original* guest clears Y1 in V172. Retain the earlier strict
# branch before this authenticated checkpoint, and permit Y1=0 only once
# this derivation has independently observed the real W1C write.
V153_MAIL_OLD='''       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             ((*v153_ctrl&V153Mail::Y1)!=0u)&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);'''
V153_MAIL_NEW='''       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             (((*v153_ctrl&V153Mail::Y1)!=0u)||
              (nwii::runtime::v172_y1_ack_seen==1u&&
               ((*v153_ctrl&V153Mail::Y1)==0u)))&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);'''

PAIR=re.compile(
    r'c\.pc==nwii::runtime::v171_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v171_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v172_y1_ack_seen==1u&&
             nwii::runtime::v171_distinct_seen==1u&&
             nwii::runtime::v170_next_seen==1u&&
             nwii::runtime::v169_next_seen==1u&&
             c.lr==0x8051910cu&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V172 original SC Y1 reply PPCCTRL write did not acknowledge Y1");'''

def extend_earlier_gates(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v171_target_pc&&'
                 'c.lr==nwii::runtime::v171_target_lr)||'
                 '(nwii::runtime::v172_y1_ack_seen==1u&&'
                 'c.pc>=0x80400000u&&c.pc<0x80600000u&&'
                 'c.lr==0x8051910cu))')
    updated,count=PAIR.subn(replacement,s)
    if not 6<=count<=24:
        raise ValueError(f"V172 expected 6..24 inherited guest PC/LR guards, found {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
        "V171 original SC reply processor did not reach distinct native callee",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V172 previous original-path assertion changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        snippet=updated[start:end]
        if start<0 or end-start>3400 or "v172_y1_ack_seen==1u" not in snippet:
            raise ValueError(f"V172 earlier original-path terminal condition incomplete: {label}")
    return updated

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V172 original-free anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V172 inherited V171 register write entry checkpoint differs")
    s=once(s,STATE,STATE+"\n static unsigned v172_y1_ack_seen=0;")
    s=once(s,RESET,RESET+"\n     nwii::runtime::v172_y1_ack_seen=0u;")
    s=once(s,STOP,CONTINUE)
    s=add_ack_observer(s)
    s=once(s,V153_MAIL_OLD,V153_MAIL_NEW)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return extend_earlier_gates(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
