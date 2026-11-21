#!/usr/bin/env python3
"""V185 execute authentic Wii IPC Y1 reader from verified V184 guest frontier.

The V184 owner-original milestone reached guest PC 0x8051905C with LR
0x8051935C, after a second IOS_Open was submitted and acknowledged.
Continue the translated reader and monitor the first real subsequent PPC
call and the existing native IOS bus state without fabricating any reply.
Original game code and owner binaries remain private.
"""
import argparse
import re
from pathlib import Path
from derive_v184_sc_reply_burst_harness import (
    derive as previous, STATE, RESET, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_TRIAL as PREVIOUS_TRIAL, OBSERVER_HEADER, once,
)

STOP='''    v184_target_pc=addr;v184_target_lr=ctx.lr;
    v184_final_status=status;
    ++v184_burst_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    check(addr==0x8051905cu&&ctx.lr==0x8051935cu&&
          v184_calls==6u&&v184_status_before==1u&&
          clean&&reply&&queue&&guest&&caller&&coherent&&mapped&&
          status==1u&&!changed,
          "V185 verified V184 native IPC read entry differs");
    const auto v185_c=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const bool v185_req=v183_second_msg==1u&&v183_second_ctrl==1u&&
          v183_second_phys!=0u&&ipc70_ram.valid(v183_second_phys,64u);
    const bool v185_x1=v185_c.has_value()&&((*v185_c&Mail::X1)!=0u);
    const bool v185_y1=v185_c.has_value()&&((*v185_c&Mail::Y1)!=0u);
    const bool v185_y2=v185_c.has_value()&&((*v185_c&Mail::Y2)!=0u);
    const bool v185_pending=v185_req&&ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool v185_done=v185_req&&ipc70_ram.read32(v183_second_phys)==IOS::Reply;
    std::cout<<"V185_IPC_ENTRY phase=1 request="<<v185_req
             <<" x1="<<v185_x1<<" y1="<<v185_y1<<" y2="<<v185_y2
             <<" open="<<v185_pending<<" replied="<<v185_done
             <<" status="<<status<<std::endl;
    check(v185_req,
          "V185 original second IOS_Open request absent at authenticated reader");
    v185_start_inst=ctx.inst_count;
    v185_status_before=status;
    v184_target_pc=addr;v184_target_lr=ctx.lr;
    v184_final_status=status;
    ++v184_burst_seen;
    return; // execute real original 0x8051905C PPC read helper
  }'''
OBSERVER='''  if(v184_burst_seen==1u&&v185_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u){
    using Bus=undercover::wii::IosBus;
    using Mail=undercover::wii::IpcMailbox;
    using Irq=undercover::wii::HollywoodIrq;
    using IOS=undercover::wii::StmIos;
    const auto ctrl=ipc70_bus.read32(Bus::IPC+Mail::PPCCTRL);
    const auto flag=ipc70_bus.read32(Bus::IPC+Irq::PPC_FLAG);
    const bool clean=ctrl.has_value()&&flag.has_value()&&
          ((*ctrl&Mail::Y1)==0u)&&((*ctrl&Mail::Y2)==0u)&&
          ((*flag&Irq::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool x1=ctrl.has_value()&&((*ctrl&Mail::X1)!=0u);
    const bool request=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Open;
    const bool replied=ipc70_ram.valid(v183_second_phys,64u)&&
          ipc70_ram.read32(v183_second_phys)==IOS::Reply;
    const bool queue=ipc70_bus.services().queued_replies()==0u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v185_start_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          (ctx.lr&3u)==0u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&Bus::MSR_EE)!=0u)&&ipc70_bus.external_irq_level());
    const uint32_t sc_addr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(sc_addr)!=nullptr;
    const uint32_t status=mapped?ctx.mmu.read8(sc_addr):0u;
    const bool changed=mapped&&status!=v185_status_before;
    std::cout<<"V185_SC_NEXT clean="<<clean<<" x1="<<x1
             <<" request="<<request<<" replied="<<replied
             <<" queue="<<queue<<" guest="<<guest
             <<" caller="<<caller<<" coherent="<<coherent
             <<" mapped="<<mapped<<" before="<<v185_status_before
             <<" status="<<status<<" changed="<<changed
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr<<std::dec<<std::endl;
    check(guest&&caller&&coherent&&mapped,
          "V185 native SC reply reader did not reach authentic next guest function");
    v185_target_pc=addr;v185_target_lr=ctx.lr;
    ++v185_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
PAIR=re.compile(
    r'c\.pc==nwii::runtime::v184_target_pc&&'
    r'\s*c\.lr==nwii::runtime::v184_target_lr')
NEXT_TRIAL='''       check(nwii::runtime::v185_next_seen==1u&&
             nwii::runtime::v184_burst_seen==1u&&
             nwii::runtime::v184_calls==6u&&
             nwii::runtime::v183_burst_seen==1u&&
             c.pc==nwii::runtime::v185_target_pc&&
             c.lr==nwii::runtime::v185_target_lr&&
             c.pc>=0x80400000u&&c.pc<0x80600000u&&
             !c.is_running,
             "V185 original IPC Y1 reader did not reach authentic native successor");'''

def widen_prior(source: str)->str:
    replacement=('((c.pc==nwii::runtime::v184_target_pc&&'
                 'c.lr==nwii::runtime::v184_target_lr)||'
                 '(nwii::runtime::v185_next_seen==1u&&'
                 'c.pc==nwii::runtime::v185_target_pc&&'
                 'c.lr==nwii::runtime::v185_target_lr))')
    updated,count=PAIR.subn(replacement,source)
    if not 7<=count<=200:
        raise ValueError(f"V185 inherited native PC/LR endpoint count changed: {count}")
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
        "V184 original SC reply continuation did not enter bounded native call",
    ):
        marker='"'+label+'");'
        if updated.count(marker)!=1:
            raise ValueError(f"V185 inherited original native milestone changed: {label}")
        end=updated.index(marker)
        start=updated.rfind("check(",0,end)
        if start<0 or end-start>15000 or "v185_next_seen==1u" not in updated[start:end]:
            raise ValueError(f"V185 earlier native check rejects authenticated guest continuation: {label}")
    return updated

def derive(source: str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1:
        raise ValueError("V185 prior original V184 guest entry no longer matches owner trace")
    s=once(s,STATE,STATE+'''
 static unsigned v185_next_seen=0u;
 static uint64_t v185_start_inst=0u;
 static uint32_t v185_status_before=0u;
 static uint32_t v185_target_pc=0u,v185_target_lr=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v185_next_seen=0u;
     nwii::runtime::v185_start_inst=0u;
     nwii::runtime::v185_status_before=0u;
     nwii::runtime::v185_target_pc=nwii::runtime::v185_target_lr=0u;''')
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
