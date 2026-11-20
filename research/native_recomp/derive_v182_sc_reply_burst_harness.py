#!/usr/bin/env python3
"""V182 bound eight genuine native Wii calls after the verified SC allocator.

V181 owner-original confirmed a second 0x8051AD38 call from LR 0x80519874
and successor 0x8051AB34 preserving LR 0x80519874. Resume the original
translated callee and monitor at most eight further PPC text entries,
stopping early only on an observed real SC status transition.
Read-only observation: no synthetic callback, guest register/memory writes,
host IOS pump, forced return, or status fabrication.
"""
import argparse
import re
from pathlib import Path
from derive_v181_sc_reply_next_harness import (
    derive as previous, STATE, RESET, FOLLOWUP as PREVIOUS_FOLLOWUP,
    NEXT_TRIAL as PREVIOUS_TRIAL, OBSERVER_HEADER, once,
)

MAX_CALLS=8
# V182 owner original reached the inherited V112 async cache-syscall
# assertion after V181's second allocator call. Preserve its assertion and
# record only bounded phase/counter/address fields before attempting to scope.
V112_SYSCALL_GUARD='''check(order&&count,"V112 original IOS_OpenAsync native cache syscall differs");'''
V182_V112_TELEMETRY='''{ // Observe late repeated syscall without changing the original V112 guard.
      const bool late=v181_next_seen==1u&&v182_burst_seen==0u;
      if(late){
        std::cout<<"V182_V112_DEP phase="<<late
                 <<" op="<<(post111_open==1u)
                 <<" flush="<<post112_flush<<" sc="<<post112_sc
                 <<" vector="<<post112_vector
                 <<" order="<<order<<" count="<<count
                 <<" calls="<<v182_calls
                 <<" pc="<<std::hex<<ctx.pc<<" lr="<<ctx.lr
                 <<std::dec<<std::endl;
      }
      check(order&&count,"V112 original IOS_OpenAsync native cache syscall differs");
    }'''


STOP='''    v181_target_pc=addr;v181_target_lr=ctx.lr;
    ++v181_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051ab34u&&ctx.lr==0x80519874u&&
          clean&&reply&&queue&&guest&&caller&&coherent&&mapped&&
          v181_status_before==1u&&status==1u&&!changed,
          "V182 owner-original repeated allocator successor differs from V181");
    v182_start_inst=ctx.inst_count;
    v182_last_inst=ctx.inst_count;
    v182_status_before=status;
    v181_target_pc=addr;v181_target_lr=ctx.lr;
    ++v181_next_seen;
    return; // execute authentic 0x8051AB34 and its native callees
  }'''
OBSERVER='''  if(v181_next_seen==1u&&v182_burst_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v182_last_inst&&
          ctx.inst_count>v182_start_inst&&ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    check(guest&&caller&&coherent&&mapped&&v182_calls<8u,
          "V182 authenticated native SC reply call budget or CPU state invalid");
    v182_trace_pc[v182_calls]=addr;
    v182_trace_lr[v182_calls]=ctx.lr;
    ++v182_calls;
    v182_last_inst=ctx.inst_count;
    const bool changed=status!=v182_status_before;
    if(v182_calls<8u&&!changed)
      return; // continue unmodified original guest execution
    for(unsigned i=0u;i<v182_calls;++i)
      std::cout<<"V182_SC_TRACE step="<<(i+1u)
               <<" pc="<<std::hex<<v182_trace_pc[i]
               <<" lr="<<v182_trace_lr[i]<<std::dec<<std::endl;
    std::cout<<"V182_SC_BURST calls="<<v182_calls
             <<" clean="<<clean<<" reply="<<reply
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v182_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    v182_target_pc=addr;v182_target_lr=ctx.lr;
    v182_final_status=status;
    ++v182_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v181_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v181_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v182_burst_seen==1u&&
             nwii::runtime::v181_next_seen==1u&&
             nwii::runtime::v180_next_seen==1u&&
             nwii::runtime::v178_burst_seen==1u&&
             nwii::runtime::v182_calls>=1u&&
             nwii::runtime::v182_calls<=8u&&
             c.pc==nwii::runtime::v182_target_pc&&
             c.lr==nwii::runtime::v182_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V182 original SC reply call burst did not reach authenticated native stop");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v181_target_pc&&'
                 'c.lr==nwii::runtime::v181_target_lr)||'
                 '(nwii::runtime::v182_burst_seen==1u&&'
                 'c.pc==nwii::runtime::v182_target_pc&&'
                 'c.lr==nwii::runtime::v182_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=144:
        raise ValueError(f"V182 inherited native PC/LR endpoint count changed: {count}")
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
        "V179 original SC reply continuation did not enter next PPC callee",
        "V180 original SC reply successor did not reach another native function",
        "V181 original SC reply successor did not reach another native function",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V182 inherited native call milestone differs: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>11000 or "v182_burst_seen==1u" not in updated[start:end]:
            raise ValueError(f"V182 prior validated guest check rejects new stop: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    s=once(s,V112_SYSCALL_GUARD,V182_V112_TELEMETRY)
    if PREVIOUS_FOLLOWUP.count(STOP)!=1:
        raise ValueError("V182 authenticated V181 owner stop differs")
    s=once(s,STATE,STATE+'''
 static unsigned v182_calls=0u,v182_burst_seen=0u;
 static uint64_t v182_start_inst=0u,v182_last_inst=0u;
 static uint32_t v182_status_before=0u,v182_final_status=0u;
 static uint32_t v182_target_pc=0u,v182_target_lr=0u;
 static std::array<uint32_t,8> v182_trace_pc{},v182_trace_lr{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v182_calls=nwii::runtime::v182_burst_seen=0u;
     nwii::runtime::v182_start_inst=nwii::runtime::v182_last_inst=0u;
     nwii::runtime::v182_status_before=nwii::runtime::v182_final_status=0u;
     nwii::runtime::v182_target_pc=nwii::runtime::v182_target_lr=0u;
     nwii::runtime::v182_trace_pc.fill(0u);
     nwii::runtime::v182_trace_lr.fill(0u);''')
    s=once(s,PREVIOUS_FOLLOWUP,PREVIOUS_FOLLOWUP.replace(STOP,CONTINUE,1))
    s=once(s,OBSERVER_HEADER,OBSERVER_HEADER+'\n'+OBSERVER)
    s=once(s,PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+NEXT_TRIAL)
    return widen_prior(s)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
