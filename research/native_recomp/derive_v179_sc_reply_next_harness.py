#!/usr/bin/env python3
"""V179 resume verified V178 original PPC 0x8051982C and trace the next call.

V178 ran six consecutive original Wii guest callees and stopped before the
original 0x8051982C body, returning from 0x804F1ECC. This derived test owns
only instrumentation. Never inject guest state, synthetic callbacks, or IOS
completion, and never publish original game bytes.
"""
import argparse
import re
from pathlib import Path
from derive_v178_sc_reply_burst_harness import (
    derive as previous, STATE, RESET, OBSERVATION as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, once,
)

STOP='''    v178_target_pc=addr;v178_target_lr=ctx.lr;
    v178_final_status=status;
    ++v178_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051982cu&&ctx.lr==0x804f1eccu&&
          v178_calls==6u&&v178_status_before==1u&&
          status==1u&&!changed,
          "V179 authenticated V178 sixth guest callee differs");
    v179_start_inst=ctx.inst_count;
    v179_status_before=status;
    v178_target_pc=addr;v178_target_lr=ctx.lr;
    v178_final_status=status;
    ++v178_burst_seen;
    return; // execute the authentic 0x8051982C PowerPC body
  }'''
OBSERVER_HEADER='void trace_call(uint32_t addr, CPUContext&ctx){'
FOLLOWUP='''  if(v178_burst_seen==1u&&v179_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const auto arm=ipc70_bus.read32(Bus::IPC+Mail::ARMMSG);
    const bool clean=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)==0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool reply=arm.has_value()&&*arm==v153_phys&&
          ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==IOS::Reply&&
          ipc70_ram.read32(v153_phys+4u)==v153_fd;
    const bool queue=ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v179_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=v179_status_before;
    std::cout<<"V179_SC_NEXT clean="<<clean<<" reply="<<reply
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v179_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V179 original SYSCONF reply callee did not enter authentic next function");
    v179_target_pc=addr;v179_target_lr=ctx.lr;
    ++v179_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v178_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v178_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v179_next_seen==1u&&
             nwii::runtime::v178_burst_seen==1u&&
             nwii::runtime::v178_calls==6u&&
             nwii::runtime::v177_next_seen==1u&&
             c.pc==nwii::runtime::v179_target_pc&&
             c.lr==nwii::runtime::v179_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V179 original SC reply continuation did not enter next PPC callee");'''

def widen_prior(source: str)->str:
    repl=('((c.pc==nwii::runtime::v178_target_pc&&'
          'c.lr==nwii::runtime::v178_target_lr)||'
          '(nwii::runtime::v179_next_seen==1u&&'
          'c.pc==nwii::runtime::v179_target_pc&&'
          'c.lr==nwii::runtime::v179_target_lr))')
    output,count=PAIR.subn(repl,source)
    if not 7<=count<=96:
        raise ValueError(f"V179 inherited native endpoint gate count changed: {count}")
    for label in (
        "V166 second SC reply nested interrupt restore did not reach real guest call",
        "V167 original SC reply IPC handler did not reach first real guest leaf",
        "V168 original SC Y1 register read did not reach second guest leaf",
        "V169 original SC reply processor did not reach next guest call",
        "V170 original SC Y1 reply read did not reach next native function",
        "V171 original SC reply processor did not reach distinct native callee",
        "V172 original SC Y1 reply PPCCTRL ACK was not performed by game code",
        "V173 original SYSCONF Y1 reply W1C did not advance to next guest call",
        "V174 original Wii SC reply follow-up did not call next native helper",
        "V175 original SC reply successor did not reach new PPC callee",
        "V176 original SC reply callback frontier did not enter next guest function",
        "V177 original SC reply handler callee did not enter subsequent native function",
        "V178 original SC reply burst did not reach bounded native checkpoint",
    ):
        marker='"'+label+'");'
        if output.count(marker)!=1:
            raise ValueError(f"V179 original prior assertion changed: {label}")
        end=output.index(marker)
        start=output.rfind("check(",0,end)
        if start<0 or end-start>9000 or "v179_next_seen==1u" not in output[start:end]:
            raise ValueError(f"V179 prior owner-original check rejects new guest stop: {label}")
    return output

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V179 original V178 observer checkpoint guard changed")
    if PREVIOUS_OBSERVER.count(OBSERVER_HEADER)!=1:
        raise ValueError("V179 original V178 guest observer header changed")
    s=once(s,STATE,STATE+'''
 static unsigned v179_next_seen=0u;
 static uint64_t v179_start_inst=0u;
 static uint32_t v179_status_before=0u;
 static uint32_t v179_target_pc=0u,v179_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v179_next_seen=0u;
     nwii::runtime::v179_start_inst=0u;
     nwii::runtime::v179_status_before=0u;
     nwii::runtime::v179_target_pc=nwii::runtime::v179_target_lr=0u;''')
    updated_observer=PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1)
    updated_observer=updated_observer.replace(
        OBSERVER_HEADER,OBSERVER_HEADER+'\n'+FOLLOWUP,1)
    s=once(s,PREVIOUS_OBSERVER,updated_observer)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
