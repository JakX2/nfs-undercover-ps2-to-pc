#!/usr/bin/env python3
"""V380: execute NAND Y1 original OSGetTime and IRQ-dispatch scheduler call.

The authenticated V379 owner run proved 13 original dispatcher-to-OSGetTime
trials. Prior V219 demonstrated the next genuine Wii dispatcher call at
0x805293F8 with LR 0x80526C98 in a different IRQ context. Verify that
same call, if reached on the authenticated NAND Y1 branch. No fabricated
clock, IOS completion, guest frame or branch.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
OLD_STOP='''    ++v379_time_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
NEW_STOP='''    ++v379_time_seen;
    v380_time_inst=ctx.inst_count;
    return; // original OSGetTime AOT body and authentic dispatcher successor
  }'''
STATE_OLD='static unsigned v379_time_seen=0u;'
STATE_ADD='''static unsigned v379_time_seen=0u;
static unsigned v380_scheduler_seen=0u;
static uint64_t v380_time_inst=0u;'''
MARKER='V380_NAND_SCHED_ENTRY guest='
TRIAL='V380_NAND_SCHED_TRIAL time='
TRACE=r"""
  // V380: observe real IRQ dispatcher's OSDisableScheduler call.
  if(v377_live&&v379_time_seen==1u&&v380_scheduler_seen==0u&&
     addr==0x805293f8u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq=ctl.has_value()&&flag.has_value()&&
         ((*ctl&M::Y1)!=0u)&&((*ctl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool guest=ctx.pc==addr&&ctx.lr==0x80526c98u&&
         v377_vector_seen==1u&&v377_handler_seen==1u&&
         v378_dispatch_seen==1u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v380_time_inst;
    const bool original_sda=ctx.gpr[13]!=0u&&
         (ctx.gpr[13]&3u)==0u&&
         ctx.mmu.get_ptr(ctx.gpr[13])!=nullptr;
    std::cout<<"V380_NAND_SCHED_ENTRY guest="<<unsigned(guest)
             <<" irq="<<unsigned(irq)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<" sda="<<unsigned(original_sda)
             <<std::endl;
    check(guest&&irq&&masked&&advanced&&original_sda,
          "V380 original NAND Y1 dispatcher failed to enter OSDisableScheduler");
    ++v380_scheduler_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(OLD_STOP)!=1 or
        source.count(STATE_OLD)!=1 or
        source.count('V379_NAND_TIME_ENTRY guest=')!=1 or
        source.count('V379_NAND_TIME_TRIAL dispatch=')!=1 or
        source.count('const bool v379_completed=')!=1 or
        source.count('nwii::runtime::v379_dispatch_inst=0u;')!=1 or
        source.count('V378_NAND_DISPATCH_ENTRY route=')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V380 authenticated V379 NAND frontier changed')
    output=source.replace(STATE_OLD,STATE_ADD,1)
    reset='nwii::runtime::v379_dispatch_inst=0u;'
    output=output.replace(
        reset,
        reset+'\n'+
        '  nwii::runtime::v380_scheduler_seen=0u;\n'+
        '  nwii::runtime::v380_time_inst=0u;',
        1
    )
    output=output.replace(OLD_STOP,NEW_STOP,1)
    output=output.replace(HEAD,HEAD+TRACE,1)
    v377_old='(c.pc==0x80526ce0u||c.pc==0x80526a3cu||c.pc==0x8052a824u);'
    v377_new='(c.pc==0x80526ce0u||c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u);'
    if output.count(v377_old)!=1:
        raise ValueError('V380 V377 retired stop PC gate changed')
    output=output.replace(v377_old,v377_new,1)
    v378_old='(c.pc==0x80526a3cu||c.pc==0x8052a824u);'
    v378_new='(c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u);'
    if output.count(v378_old)!=1:
        raise ValueError('V380 V378 retired stop PC gate changed')
    output=output.replace(v378_old,v378_new,1)
    start=output.index('const bool v379_completed=')
    end=output.index('std::cout<<"V379_NAND_TIME_TRIAL',start)
    candidate=output[start:end]
    v379_old='c.pc==0x8052a824u;'
    v379_new='(c.pc==0x8052a824u||c.pc==0x805293f8u);'
    if candidate.count(v379_old)!=1:
        raise ValueError('V380 prior timebase completion gate changed')
    output=output[:start]+candidate.replace(v379_old,v379_new,1)+output[end:]
    old_continue='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(old_continue)!=1:
        raise ValueError('V380 authentic bounded trial loop moved')
    trial=(
        '  const bool v380_completed=v379_completed&&\n'
        '       nwii::runtime::v380_scheduler_seen==1u&&\n'
        '       c.pc==0x805293f8u;\n'
        '  std::cout<<"V380_NAND_SCHED_TRIAL time="<<unsigned(\n'
        '               nwii::runtime::v379_time_seen==1u)\n'
        '           <<" scheduler="<<unsigned(nwii::runtime::v380_scheduler_seen==1u)\n'
        '           <<" completed="<<unsigned(v380_completed)<<std::endl;\n'
        '  check(v380_completed,\n'
        '        "V380 original NAND dispatcher did not enter genuine OS scheduler helper");\n'
        +old_continue
    )
    output=output.replace(old_continue,trial,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(NEW_STOP)!=1 or output.count(OLD_STOP)!=0 or
        output.count('V379_NAND_TIME_ENTRY guest=')!=1 or
        output.count('V378_NAND_DISPATCH_ENTRY route=')!=1):
        raise ValueError('V380 observer not unique or original trace altered')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('previous_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        transformed=patch(a.previous_private_harness.read_text(encoding='utf-8'))
        with a.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(transformed)
    except (ValueError,OSError):
        print('V380_NAND_SCHED_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V380_NAND_SCHED_ROUTE installed=1 original_guest=1 no_synthetic_clock=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
