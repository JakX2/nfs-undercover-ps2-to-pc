#!/usr/bin/env python3
"""V173 execute original SYSCONF Y1 reply processor beyond its real W1C.

V172 authenticated an original PPCCTRL Y1 guest write from 0x8051906C,
LR 0x8051910C, with Hollywood PPC_FLAG still asserted and SDA status 1.
Do not simulate the next action. Permit the original generated PPC store to
return naturally, then capture the first *actual* subsequent guest function
entry with its CPU/link state, mailbox and status byte. No IOS ticks, guest
register edits, manual W1C, extra guest instruction or callback is injected.
"""
import argparse
import re
from pathlib import Path
from derive_v172_sc_y1_ack_harness import (
    derive as previous, STATE, RESET,
    MMIO_OBSERVER as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
    TRACE_ANCHOR, V153_MAIL_NEW as V172_V153_MAIL,
)

STOP='''       v172_stop_pc=ipc70_ram.cpu->pc;
       v172_stop_lr=ipc70_ram.cpu->lr;
       ++v172_ack_seen;
       ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
     }'''
CONTINUE='''       v173_start_inst=ipc70_ram.cpu->inst_count;
       v173_mmio_after_y1=mmio_writes.size();
       v172_stop_pc=ipc70_ram.cpu->pc;
       v172_stop_lr=ipc70_ram.cpu->lr;
       ++v172_ack_seen;
       // Return to the *original* translated PPCCTRL writer's instructions.
     }'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v172_ack_seen==1u&&v173_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool y1clear=ctrl.has_value()&&((*ctrl&Mail::Y1)==0u);
    const bool flagup=flag.has_value()&&((*flag&Irq::IPC_PPC)!=0u);
    unsigned original_flag_w1c=0u;
    for(size_t i=v173_mmio_after_y1;i<mmio_writes.size();++i){
      const auto& write=mmio_writes[i];
      if((write.first==Bus::IPC+Irq::PPC_FLAG||
          write.first==Bus::MIRROR+Irq::PPC_FLAG)&&
         (write.second&Irq::IPC_PPC)!=0u)
        ++original_flag_w1c;
    }
    const bool flag_ack=original_flag_w1c==1u&&
          !flagup&&!ipc70_bus.external_irq_level();
    const bool wire=arm.has_value()&&*arm==v153_phys;
    const bool reply=ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v173_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x805190c0u&&ctx.lr<0x805194c4u&&
          !(ctx.lr&3u);
    const bool masked=(ctx.msr&Bus::MSR_EE)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (!masked&&ipc70_bus.external_irq_level());
    const uint32_t sda=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sda)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sda):0u;
    const bool write=addr==0x8051906cu;
    const bool read=addr==0x8051905cu;
    std::cout<<"V173_SC_AFTER_Y1_ACK y1clear="<<y1clear
             <<" flag="<<flagup<<" wire="<<wire<<" reply="<<reply
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" status="<<status<<" read="<<read<<" write="<<write
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    std::cout<<"V173_SC_HW_FLAG_W1C guest=1 count="<<original_flag_w1c
             <<" cleared="<<(!flagup)
             <<" irq_down="<<(!ipc70_bus.external_irq_level())<<std::endl;
    check(flag_ack,
          "V173 original SC reply did not clear Hollywood IPC latch via guest W1C");
    check(y1clear&&guest&&caller&&coherent&&mapped,
          "V173 original guest Y1 W1C did not resume to valid PPC callee");
    ++v173_flag_ack_seen;
    v173_target_pc=addr;v173_target_lr=ctx.lr;
    ++v173_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v172_stop_pc&&'
    r'\s*c\.lr==nwii::runtime::v172_stop_lr')
NEXT_TRIAL='''       check(nwii::runtime::v173_flag_ack_seen==1u&&
             nwii::runtime::v173_next_seen==1u&&
             nwii::runtime::v172_ack_seen==1u&&
             nwii::runtime::v171_distinct_seen==1u&&
             nwii::runtime::v170_next_seen==1u&&
             c.pc==nwii::runtime::v173_target_pc&&
             c.lr==nwii::runtime::v173_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V173 original SYSCONF Y1 reply W1C did not advance to next guest call");'''
V172_FINAL_END='''             c.pc==nwii::runtime::v172_stop_pc&&
             c.lr==nwii::runtime::v172_stop_lr&&
             c.lr==0x8051910cu&&
             !c.is_running,'''
V173_FINAL_END='''             (((c.pc==nwii::runtime::v172_stop_pc&&
               c.lr==nwii::runtime::v172_stop_lr)&&
               c.lr==0x8051910cu)||
              (nwii::runtime::v173_next_seen==1u&&
               c.pc==nwii::runtime::v173_target_pc&&
               c.lr==nwii::runtime::v173_target_lr))&&
             !c.is_running,'''
V172_FINAL_EXTENDED='''             ((c.pc==nwii::runtime::v172_stop_pc&&c.lr==nwii::runtime::v172_stop_lr)||(nwii::runtime::v173_next_seen==1u&&c.pc==nwii::runtime::v173_target_pc&&c.lr==nwii::runtime::v173_target_lr))&&
             c.lr==0x8051910cu&&
             !c.is_running,'''

# The V153 snapshot was taken while the *second* reply interrupt was
# pending. At the newer V173 stop, authentic guest code has acknowledged both
# Y1 (V172) and Hollywood PPC_FLAG (V173). Only the observed guest W1C
# authorizes relaxing the later snapshot; the earlier original checkpoint
# still demands the asserted interrupt.
V173_V153_MAIL=V172_V153_MAIL.replace(
    '''             ((*v153_flags&V153Irq::IPC_PPC)!=0u);''',
    '''             (((*v153_flags&V153Irq::IPC_PPC)!=0u)||
              (nwii::runtime::v173_flag_ack_seen==1u&&
               ((*v153_flags&V153Irq::IPC_PPC)==0u)));''')
V153_IRQ_OLD='''       const bool v153_irq=nwii::runtime::ipc70_bus.external_irq_level()&&
             !nwii::runtime::ipc70_bus.external_exception_pending(c.msr)&&
             (c.msr&V153Bus::MSR_EE)==0u;'''
V153_IRQ_NEW='''       const bool v153_irq=
             (nwii::runtime::ipc70_bus.external_irq_level()||
              (nwii::runtime::v173_flag_ack_seen==1u&&
               !nwii::runtime::ipc70_bus.external_irq_level()))&&
             !nwii::runtime::ipc70_bus.external_exception_pending(c.msr)&&
             (c.msr&V153Bus::MSR_EE)==0u;'''

def widen_prior_gates(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v172_stop_pc&&'
                 'c.lr==nwii::runtime::v172_stop_lr)||'
                 '(nwii::runtime::v173_next_seen==1u&&'
                 'c.pc==nwii::runtime::v173_target_pc&&'
                 'c.lr==nwii::runtime::v173_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 7<=n<=28:
        raise ValueError(f"V173 expected 7..28 original guest PC/LR gates, got {n}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
        "V171 original SC reply processor did not reach distinct native callee",
        "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V173 prior state assertion label missing: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        check=updated[start:end]
        if start<0 or end-start>3500 or "v173_next_seen==1u" not in check:
            raise ValueError(f"V173 earlier guest check did not retain next PC: {label}")
    return updated

def once(s: str,old: str,new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V173 original-free source anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or PREVIOUS_TRIAL.count(V172_FINAL_END)!=1:
        raise ValueError("V173 inherited authentic PPCCTRL Y1 ACK boundary differs")
    s=once(s,STATE,STATE+'''
 static unsigned v173_next_seen=0,v173_flag_ack_seen=0;
 static uint64_t v173_start_inst=0;
 static size_t v173_mmio_after_y1=0;
 static uint32_t v173_target_pc=0,v173_target_lr=0;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v173_next_seen=nwii::runtime::v173_flag_ack_seen=0u;
     nwii::runtime::v173_start_inst=0u;
     nwii::runtime::v173_mmio_after_y1=0u;
     nwii::runtime::v173_target_pc=nwii::runtime::v173_target_lr=0u;''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    if V173_V153_MAIL==V172_V153_MAIL:
        raise ValueError("V173 V153 Hollywood latch assertion anchor changed")
    s=once(s,V172_V153_MAIL,V173_V153_MAIL)
    s=once(s,V153_IRQ_OLD,V153_IRQ_NEW)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    s=widen_prior_gates(s)
    return once(s,V172_FINAL_EXTENDED,V173_FINAL_END)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
