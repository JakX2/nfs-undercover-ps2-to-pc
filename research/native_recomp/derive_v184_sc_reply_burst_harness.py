#!/usr/bin/env python3
"""V184 resume the V183 original Wii SC post-reply function at 0x8051AD3C.

V183 owner-original CI verified eight guest calls, last PC 0x8051AD3C and
LR 0x805192C8. Continue actual PPC code for up to six guest call entries,
stopping earlier if the original SC byte changes. Observe the second IOS
request and IRQ semantics without injecting callbacks or changing guest state.
No game assets, original binary bytes or derived translated code are exported.
"""
import argparse
import re
from pathlib import Path
from derive_v183_sc_reply_burst_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, OBSERVER_HEADER, once,
)

MAX_CALLS=6
STOP='''    v183_target_pc=addr;v183_target_lr=ctx.lr;
    v183_final_status=status;
    ++v183_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051ad3cu&&ctx.lr==0x805192c8u&&
          v183_calls==8u&&v183_status_before==1u&&
          clean&&reply&&queue&&guest&&caller&&coherent&&mapped&&
          status==1u&&!changed,
          "V184 original V183 final callee differs from verified guest frontier");
    const auto v184_ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const bool v184_req=v183_second_msg==1u&&v183_second_phys!=0u&&
          ipc70_ram.valid(v183_second_phys,64u);
    const bool v184_cmd=v183_second_cmd>=IOS::Open&&v183_second_cmd<=IOS::Ioctlv;
    const bool v184_x1=v184_ctrl.has_value()&&((*v184_ctrl&Mail::X1)!=0u);
    std::cout<<"V184_IPC_ENTRY phase=1 msg="<<v184_req
             <<" ctrl="<<(v183_second_ctrl==1u)
             <<" x1="<<v184_x1<<" known="<<v184_cmd
             <<" calls="<<v183_calls<<std::endl;
    check(v184_req&&v184_cmd&&v183_second_ctrl<=1u,
          "V184 original post-reply request absent before next native callee");
    v184_start_inst=ctx.inst_count;
    v184_last_inst=ctx.inst_count;
    v184_status_before=status;
    v183_target_pc=addr;v183_target_lr=ctx.lr;
    v183_final_status=status;
    ++v183_burst_seen;
    return; // execute original Wii 0x8051AD3C guest callee
  }'''
OBSERVER='''  if(v183_burst_seen==1u&&v184_burst_seen==0u&&
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
    const bool guest=ctx.pc==addr&&ctx.inst_count>v184_last_inst&&
          ctx.inst_count>v184_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    check(guest&&caller&&coherent&&mapped&&v184_calls<6u,
          "V184 native SC reply followup exceeded bounded original guest call budget");
    v184_trace_pc[v184_calls]=addr;
    v184_trace_lr[v184_calls]=ctx.lr;
    ++v184_calls;
    v184_last_inst=ctx.inst_count;
    const bool changed=status!=v184_status_before;
    if(v184_calls<6u&&!changed)
      return; // execute next original guest call without new host operations
    for(unsigned i=0u;i<v184_calls;++i)
      std::cout<<"V184_SC_TRACE step="<<(i+1u)
               <<" pc="<<std::hex<<v184_trace_pc[i]
               <<" lr="<<v184_trace_lr[i]<<std::dec<<std::endl;
    const auto final_ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const bool request=final_ctrl.has_value()&&
          ((*final_ctrl&Mail::X1)!=0u);
    std::cout<<"V184_SC_BURST calls="<<v184_calls
             <<" clean="<<clean<<" reply="<<reply
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" submitted="<<request
             <<" before="<<v184_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    v184_target_pc=addr;v184_target_lr=ctx.lr;
    v184_final_status=status;
    ++v184_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v183_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v183_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v184_burst_seen==1u&&
             nwii::runtime::v183_burst_seen==1u&&
             nwii::runtime::v183_calls==8u&&
             nwii::runtime::v182_burst_seen==1u&&
             nwii::runtime::v184_calls>=1u&&
             nwii::runtime::v184_calls<=6u&&
             c.pc==nwii::runtime::v184_target_pc&&
             c.lr==nwii::runtime::v184_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V184 original SC reply continuation did not enter bounded native call");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v183_target_pc&&'
                 'c.lr==nwii::runtime::v183_target_lr)||'
                 '(nwii::runtime::v184_burst_seen==1u&&'
                 'c.pc==nwii::runtime::v184_target_pc&&'
                 'c.lr==nwii::runtime::v184_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=180:
        raise ValueError(f"V184 original-free prior native PC/LR count differs: {count}")
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
        "V182 original SC reply call burst did not reach authenticated native stop",
        "V183 original SC reply IPC followup did not reach bounded guest call",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V184 prior original assertion missing or duplicated: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>14000 or "v184_burst_seen==1u" not in updated[start:end]:
            raise ValueError(f"V184 prior original guest proof rejects authenticated continuation: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V184 V183 original call frontier differs from authenticated guest PC/LR")
    s=once(s,STATE,STATE+'''
 static unsigned v184_calls=0u,v184_burst_seen=0u;
 static uint64_t v184_start_inst=0u,v184_last_inst=0u;
 static uint32_t v184_status_before=0u,v184_final_status=0u;
 static uint32_t v184_target_pc=0u,v184_target_lr=0u;
 static std::array<uint32_t,6> v184_trace_pc{},v184_trace_lr{};''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v184_calls=nwii::runtime::v184_burst_seen=0u;
     nwii::runtime::v184_start_inst=nwii::runtime::v184_last_inst=0u;
     nwii::runtime::v184_status_before=nwii::runtime::v184_final_status=0u;
     nwii::runtime::v184_target_pc=nwii::runtime::v184_target_lr=0u;
     nwii::runtime::v184_trace_pc.fill(0u);
     nwii::runtime::v184_trace_lr.fill(0u);''')
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,CONTINUE,1))
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
