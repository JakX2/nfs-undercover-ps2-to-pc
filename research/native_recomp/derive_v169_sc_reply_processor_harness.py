#!/usr/bin/env python3
"""V169 execute original Y1 reply processor, report its next real PPC call.

The owner-original V168 16/16 proof reached 0x805190C0 (LR 0x80519354)
from the second SC reply IRQ's registered handler. The original PPC callee
is executed unchanged. We observe the next guest function, the real mailbox
and the existing SDA status byte, not a forced callback/ACK or return.
"""
import argparse
import re
from pathlib import Path
from derive_v168_sc_reply_read_next_harness import (
    derive as previous, STATE, RESET, OBSERVATION as PREVIOUS_OBSERVER,
    TRACE_ANCHOR, NEXT_TRIAL as PREVIOUS_TRIAL,
)

STOP='''    v168_target_pc=addr;v168_target_lr=ctx.lr;
    ++v168_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x805190c0u&&ctx.lr==0x80519354u,
          "V169 original SC reply processor entry differs from V168 native trace");
    v169_start_inst=ctx.inst_count;
    v168_target_pc=addr;v168_target_lr=ctx.lr;
    ++v168_next_seen;
    return; // execute original Wii reply processor code, not a synthetic callback
  }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v168_next_seen==1u&&v169_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool y1=ctrl.has_value()&&((*ctrl&Mail::Y1)!=0u);
    const bool flag_up=flag.has_value()&&((*flag&Irq::IPC_PPC)!=0u);
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool wire=arm.has_value()&&*arm==v153_phys;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v169_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u);
    const bool ready=ipc70_bus.external_exception_pending(ctx.msr);
    const bool coherent=ready==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sda=ctx.gpr[13]-3176u;
    const bool sda_mapped=ctx.mmu.get_ptr(sda)!=nullptr;
    const uint32_t sc_byte=sda_mapped?ctx.mmu.read8(sda):0u;
    const bool read=addr==0x8051905cu;
    const bool write=addr==0x8051906cu;
    std::cout<<"V169_SC_REPLY_NEXT guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<sda_mapped
             <<" y1="<<y1<<" flag="<<flag_up<<" reply="<<reply
             <<" wire="<<wire<<" ready="<<ready<<" status="<<sc_byte
             <<" read="<<read<<" write="<<write
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&sda_mapped,
          "V169 original SC reply processor did not reach valid guest call");
    ++v169_next_seen;
    v169_target_pc=addr;v169_target_lr=ctx.lr;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
OLD_V79='''         if(addr==POST_OWNER){'''
SCOPED_V79='''         if(addr==POST_OWNER&&v168_next_seen==0u){'''
NEXT_TRIAL='''       check(nwii::runtime::v169_next_seen==1u&&
             nwii::runtime::v168_next_seen==1u&&
             nwii::runtime::v167_next_seen==1u&&
             nwii::runtime::v166_next_seen==1u&&
             c.pc==nwii::runtime::v169_target_pc&&
             c.lr==nwii::runtime::v169_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V169 original SC reply processor did not reach next guest call");'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v168_target_pc&&'
    r'(?P<space>\s+)c\.lr==nwii::runtime::v168_target_lr')

def extend_old_trial_endpoints(s: str)->str:
    """Widen only V168's previously authenticated terminal PC/LR comparisons.

    The previous milestones' state, IRQ, thread and exact trial-count checks
    remain intact. V169 may terminate one original guest call later.
    """
    replacement=('((c.pc==nwii::runtime::v168_target_pc&&'
                 'c.lr==nwii::runtime::v168_target_lr)||'
                 '(nwii::runtime::v169_next_seen==1u&&'
                 'c.pc==nwii::runtime::v169_target_pc&&'
                 'c.lr==nwii::runtime::v169_target_lr))')
    updated,count=PAIR.subn(replacement,s)
    if not 4<=count<=12:
        raise ValueError(f"V169 expected 4..12 inherited end-conditions, saw {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V169 prior original-game trial label differs: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        check=updated[start:end]
        if start<0 or end-start>1700 or "v169_next_seen==1u" not in check:
            raise ValueError(f"V169 prior strict trial was not extended: {label}")
    return updated

def once(s: str,old: str,new: str)->str:
    count=s.count(old)
    if count!=1:
        raise ValueError(f"V169 original-free source anchor count={count}: {old[:72]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V169 V168 original reply-processor boundary differs")
    s=once(s,STATE,STATE+'''
 static unsigned v169_next_seen=0;
 static uint64_t v169_start_inst=0;
 static uint32_t v169_target_pc=0,v169_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v169_next_seen=0u;
     nwii::runtime::v169_start_inst=0u;
     nwii::runtime::v169_target_pc=nwii::runtime::v169_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    s=once(s,OLD_V79,SCOPED_V79)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return extend_old_trial_endpoints(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
