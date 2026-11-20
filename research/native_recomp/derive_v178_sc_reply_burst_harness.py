#!/usr/bin/env python3
"""V178 bounded original Wii SYSCONF reply call-chain and SC SDA observation.

V177 verified that genuine translated PPC called 0x80545100 from
0x804F1E40, with IPC Y1/Hollywood ACKed and SC r13-3176 still 1.
Execute the unchanged callee, then continue at most six further original
PowerPC function entries, stopping sooner upon an observed SDA transition.
This is a read-only instrumentation of actual call boundaries; no host
callback, IOS service, guest register write, manual return or readiness
value is injected. Report bounded original text addresses, never game bytes.
"""
import argparse
import re
from pathlib import Path
from derive_v177_sc_reply_next_harness import (
    derive as previous, STATE, RESET, TRACE_ANCHOR,
    OBSERVATION as PREVIOUS_OBSERVER, NEXT_TRIAL as PREVIOUS_TRIAL,
)

MAX_CALLS=6

STOP='''    v177_target_pc=addr;v177_target_lr=ctx.lr;
    ++v177_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x80545100u&&ctx.lr==0x804f1e40u,
          "V178 owner-original SC reply callee differs from V177 proof");
    const uint32_t v178_sc=ctx.gpr[13]-3176u;
    check(ctx.mmu.get_ptr(v178_sc)!=nullptr&&ctx.mmu.read8(v178_sc)==1u,
          "V178 inherited original SC SDA differs from verified V177");
    v178_start_inst=ctx.inst_count;
    v178_last_inst=ctx.inst_count;
    v178_status_before=ctx.mmu.read8(v178_sc);
    v177_target_pc=addr;v177_target_lr=ctx.lr;
    ++v177_next_seen;
    return; // execute original 0x80545100 and bounded native call chain
  }'''
OBSERVATION='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v177_next_seen==1u&&v178_burst_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v178_last_inst&&
          ctx.inst_count>v178_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    check(guest&&caller&&coherent&&mapped&&v178_calls<6u,
          "V178 native reply burst exceeded its authenticated guest call budget");
    v178_trace_pc[v178_calls]=addr;
    v178_trace_lr[v178_calls]=ctx.lr;
    ++v178_calls;
    v178_last_inst=ctx.inst_count;
    const bool changed=status!=v178_status_before;
    if(v178_calls<6u&&!changed)
      return; // continue original guest code without adding any operation
    for(unsigned i=0u;i<v178_calls;++i)
      std::cout<<"V178_SC_TRACE step="<<(i+1u)
               <<" pc="<<std::hex<<v178_trace_pc[i]
               <<" lr="<<v178_trace_lr[i]<<std::dec<<std::endl;
    std::cout<<"V178_SC_BURST calls="<<v178_calls
             <<" clean="<<clean<<" reply="<<reply
             <<" guest="<<guest<<" caller="<<caller
             <<" coherent="<<coherent<<" mapped="<<mapped
             <<" before="<<v178_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    v178_target_pc=addr;v178_target_lr=ctx.lr;
    v178_final_status=status;
    ++v178_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
# The V111 async-path observer remains true after its first completed
# IOS_OpenAsync entry. The later SC reply callee reuses the same allocator
# pathname-copy helper. Keep the initial V111 proof intact, but stop
# misclassifying second-phase genuine calls as the first pathname copy.
V111_ACTIVE='''     if(post110_next==1u&&post110_chosen==2u&&post111_wrapper==1u){'''
V111_SCOPED='''     if(post110_next==1u&&post110_chosen==2u&&post111_wrapper==1u&&
        post111_open==0u){'''

PAIR=re.compile(
    r'c\.pc==nwii::runtime::v177_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v177_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v178_burst_seen==1u&&
             nwii::runtime::v177_next_seen==1u&&
             nwii::runtime::v176_next_seen==1u&&
             nwii::runtime::v178_calls>=1u&&
             nwii::runtime::v178_calls<=6u&&
             c.pc==nwii::runtime::v178_target_pc&&
             c.lr==nwii::runtime::v178_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V178 original SC reply burst did not reach bounded native checkpoint");'''

def once(s: str, old: str, new: str)->str:
    n=s.count(old)
    if n!=1:
        raise ValueError(f"V178 fail-closed public C++ harness anchor count={n}: {old[:70]}")
    return s.replace(old,new,1)

def widen_prior(s: str)->str:
    replacement=('((c.pc==nwii::runtime::v177_target_pc&&'
                 'c.lr==nwii::runtime::v177_target_lr)||'
                 '(nwii::runtime::v178_burst_seen==1u&&'
                 'c.pc==nwii::runtime::v178_target_pc&&'
                 'c.lr==nwii::runtime::v178_target_lr))')
    updated,n=PAIR.subn(replacement,s)
    if not 7<=n<=78:
        raise ValueError(f"V178 original burst inherited PC/LR count changed: {n}")
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
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V178 earlier original native check changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>7000 or "v178_burst_seen==1u" not in updated[start:end]:
            raise ValueError(f"V178 old native check rejects bounded original guest path: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    s=once(s,V111_ACTIVE,V111_SCOPED)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V178 inherited original 0x80545100 guest checkpoint differs")
    s=once(s,STATE,STATE+'''
 static unsigned v178_calls=0,v178_burst_seen=0;
 static uint64_t v178_start_inst=0,v178_last_inst=0;
 static uint32_t v178_status_before=0,v178_final_status=0;
 static uint32_t v178_target_pc=0,v178_target_lr=0;
 static std::array<uint32_t,6> v178_trace_pc{},v178_trace_lr{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v178_calls=nwii::runtime::v178_burst_seen=0u;
     nwii::runtime::v178_start_inst=nwii::runtime::v178_last_inst=0u;
     nwii::runtime::v178_status_before=nwii::runtime::v178_final_status=0u;
     nwii::runtime::v178_target_pc=nwii::runtime::v178_target_lr=0u;
     nwii::runtime::v178_trace_pc.fill(0u);
     nwii::runtime::v178_trace_lr.fill(0u);''')
    s=once(s,STOP,CONTINUE)
    s=once(s,TRACE_ANCHOR,OBSERVATION)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
