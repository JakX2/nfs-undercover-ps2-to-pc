#!/usr/bin/env python3
"""V172 observe original PowerPC Y1 write-one-to-clear, not a fabricated ACK.

V171 verified the SC reply processor's original PPCCTRL write helper
0x8051906C, LR 0x8051910C, while Y1/IPC remain asserted and status=1.
Execute its unchanged PPC instruction body. The existing Broadway native
bus performs the actual guest MMIO write. Observe the post-write control,
Hollywood latch and SYSCONF reply in that same hardware hook.
"""
import argparse
import re
from pathlib import Path
from derive_v171_sc_reply_distinct_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    ++v171_distinct_seen;
    v171_target_pc=addr;v171_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051906cu&&ctx.lr==0x8051910cu,
          "V172 original SC Y1 reply PPCCTRL writer callsite differs from V171");
    v172_writes_before=mmio_writes.size();
    ++v171_distinct_seen;
    v171_target_pc=addr;v171_target_lr=ctx.lr;
    return; // execute original guest PPCCTRL writer, no host W1C synthesis
  }'''
MMIO_ANCHOR='''     check(ipc70_bus.write32(addr,value),"native bus rejected original ACK MMIO write");
     mmio_writes.emplace_back(addr,value);'''
MMIO_OBSERVER='''     check(ipc70_bus.write32(addr,value),"native bus rejected original ACK MMIO write");
     mmio_writes.emplace_back(addr,value);
     if(v171_distinct_seen==1u&&v172_ack_seen==0u&&
        (addr==B::IPC+M::PPCCTRL||addr==B::MIRROR+M::PPCCTRL)){
       using IOS=undercover::wii::StmIos;
       const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
       const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
       const auto arm=ipc70_bus.read32(B::IPC+M::ARMMSG);
       const bool w1c=(value&M::Y1)!=0u&&control.has_value()&&
             ((*control&M::Y1)==0u)&&((*control&M::Y2)==0u);
       const bool flag_up=flag.has_value()&&
             ((*flag&H::IPC_PPC)!=0u);
       const bool irq=ipc70_bus.external_irq_level();
       const bool wire=arm.has_value()&&*arm==v153_phys;
       const bool reply=ipc70_ram.valid(v153_phys,64u)&&
             ipc70_ram.read32(v153_phys)==IOS::Reply&&
             ipc70_ram.read32(v153_phys+4u)==v153_fd;
       const bool guest=ipc70_ram.cpu!=nullptr&&
             ipc70_ram.cpu->lr==0x8051910cu&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u&&
             ipc70_ram.cpu->gpr[13]==v147_first_r13;
       const bool wrote=mmio_writes.size()>v172_writes_before;
       const uint32_t sda=guest?ipc70_ram.cpu->gpr[13]-3176u:0u;
       const bool mapped=guest&&ipc70_ram.cpu->mmu.get_ptr(sda)!=nullptr;
       const uint32_t status=mapped?ipc70_ram.cpu->mmu.read8(sda):0u;
       std::cout<<"V172_SC_Y1_ACK w1c="<<w1c
                <<" flag="<<flag_up<<" irq="<<irq
                <<" wire="<<wire<<" reply="<<reply
                <<" guest="<<guest<<" wrote="<<wrote
                <<" mapped="<<mapped<<" status="<<status
                <<" pc="<<std::hex
                <<(ipc70_ram.cpu?ipc70_ram.cpu->pc:0u)
                <<" lr="<<(ipc70_ram.cpu?ipc70_ram.cpu->lr:0u)
                <<std::dec<<std::endl;
       check(w1c&&flag_up&&irq&&wire&&reply&&guest&&wrote&&mapped,
             "V172 original SC Y1 reply did not perform authentic PPCCTRL W1C");
       v172_stop_pc=ipc70_ram.cpu->pc;
       v172_stop_lr=ipc70_ram.cpu->lr;
       ++v172_ack_seen;
       ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
     }'''
NEXT_TRIAL='''       check(nwii::runtime::v172_ack_seen==1u&&
             nwii::runtime::v171_distinct_seen==1u&&
             nwii::runtime::v170_next_seen==1u&&
             nwii::runtime::v169_next_seen==1u&&
             c.pc==nwii::runtime::v172_stop_pc&&
             c.lr==nwii::runtime::v172_stop_lr&&
             c.lr==0x8051910cu&&
             !c.is_running,
             "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code");'''
# The earlier V153 checkpoint proved the SC reply was published with Y1
# asserted. After this milestone's real guest write-one-to-clear, the same
# end-of-trial snapshot must permit Y1=0 ONLY with authenticated V172 ACK.
# Hollywood PPC_FLAG remains separately asserted here.
V153_MAIL_OLD='''       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             ((*v153_ctrl&V153Mail::Y1)!=0u)&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);'''
V153_MAIL_NEW='''       const bool v153_mail=v153_ctrl.has_value()&&v153_flags.has_value()&&
             (((*v153_ctrl&V153Mail::Y1)!=0u)||
              (nwii::runtime::v172_ack_seen==1u&&
               ((*v153_ctrl&V153Mail::Y1)==0u)))&&
             ((*v153_ctrl&V153Mail::Y2)==0u)&&
             ((*v153_flags&V153Irq::IPC_PPC)!=0u);'''

PAIR=re.compile(
    r'c\.pc==nwii::runtime::v171_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v171_target_lr')

def widen_prior_pc_gates(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v171_target_pc&&'
                 'c.lr==nwii::runtime::v171_target_lr)||'
                 '(nwii::runtime::v172_ack_seen==1u&&'
                 'c.pc==nwii::runtime::v172_stop_pc&&'
                 'c.lr==nwii::runtime::v172_stop_lr))')
    updated,count=PAIR.subn(replacement,s)
    if not 7<=count<=24:
        raise ValueError(f"V172 expected 7..24 inherited PC/LR endpoints, got {count}")
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
            raise ValueError(f"V172 inherited trial assertion label changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        segment=updated[start:end]
        if start<0 or end-start>2900 or "v172_ack_seen==1u" not in segment:
            raise ValueError(f"V172 authentic guest ACK not admitted by old gate: {label}")
    return updated

def once(s: str,old: str,new: str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V172 original-free source anchor count={count}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V172 inherited genuine PPCCTRL writer entry changed")
    s=once(s,STATE,STATE+'''
 static unsigned v172_ack_seen=0;
 static size_t v172_writes_before=0;
 static uint32_t v172_stop_pc=0,v172_stop_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v172_ack_seen=0u;
     nwii::runtime::v172_writes_before=0u;
     nwii::runtime::v172_stop_pc=nwii::runtime::v172_stop_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,MMIO_ANCHOR,MMIO_OBSERVER)
    s=once(s,V153_MAIL_OLD,V153_MAIL_NEW)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior_pc_gates(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
