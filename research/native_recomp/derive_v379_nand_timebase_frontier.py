#!/usr/bin/env python3
"""V379: follow real NAND Y1 IRQ dispatcher to original Wii timebase.

V378 tests the original OS exception handler -> 0x80526A3C dispatcher.
V198 independently verified that the original guest dispatcher calls
OSGetTime at 0x8052A824 with caller LR=0x80526C84 in an earlier IOS phase.
Resume the authenticated NAND dispatcher, observe that original guest
call if it occurs, then stop before its body. No synthetic timer values,
guest PC/register writes or IOS request servicing are introduced here.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
OLD_STOP='''    ++v378_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
NEW_STOP='''    ++v378_dispatch_seen;
    v379_dispatch_inst=ctx.inst_count;
    return; // execute original Wii IRQ dispatcher
  }'''
STATE_OLD='static unsigned v378_dispatch_seen=0u;'
STATE_ADD='''static unsigned v378_dispatch_seen=0u;
static unsigned v379_time_seen=0u;
static uint64_t v379_dispatch_inst=0u;'''
MARKER='V379_NAND_TIME_ENTRY guest='
TRIAL='V379_NAND_TIME_TRIAL dispatch='
TRACE=r"""
  // V379: first authentic original dispatcher OSGetTime call after Y1.
  if(v377_live&&v378_dispatch_seen==1u&&v379_time_seen==0u&&
     addr==0x8052a824u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool signal=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool guest=ctx.pc==addr&&ctx.lr==0x80526c84u&&
         v377_vector_seen==1u&&v377_handler_seen==1u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool progressed=ctx.inst_count>v379_dispatch_inst;
    const bool resume=v377_resume!=0u&&(v377_resume&3u)==0u&&
         (v377_srr1&B::MSR_EE)!=0u;
    std::cout<<"V379_NAND_TIME_ENTRY guest="<<unsigned(guest)
             <<" signal="<<unsigned(signal)
             <<" masked="<<unsigned(masked)
             <<" progressed="<<unsigned(progressed)
             <<" resume="<<unsigned(resume)
             <<std::endl;
    check(guest&&signal&&masked&&progressed&&resume,
          "V379 authentic NAND IRQ dispatcher lost original OSGetTime ABI");
    ++v379_time_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(OLD_STOP)!=1 or
        source.count(STATE_OLD)!=1 or
        source.count('V378_NAND_DISPATCH_ENTRY route=')!=1 or
        source.count('V378_NAND_DISPATCH_TRIAL handler=')!=1 or
        source.count('const bool v378_completed=')!=1 or
        source.count('V377_NAND_HANDLER_TRIAL stopped=')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V379 original NAND dispatcher source seam changed')
    staged=source.replace(STATE_OLD,STATE_ADD,1)
    staged=staged.replace(OLD_STOP,NEW_STOP,1)
    staged=staged.replace(HEAD,HEAD+TRACE,1)
    old_v377='(c.pc==0x80526ce0u||c.pc==0x80526a3cu);'
    new_v377='(c.pc==0x80526ce0u||c.pc==0x80526a3cu||c.pc==0x8052a824u);'
    if staged.count(old_v377)!=1:
        raise ValueError('V379 V377 previous stopping PC gate moved')
    staged=staged.replace(old_v377,new_v377,1)
    start=staged.index('const bool v378_completed=')
    end=staged.index('std::cout<<"V378_NAND_DISPATCH_TRIAL',start)
    candidate=staged[start:end]
    old_dispatch='c.pc==0x80526a3cu;'
    new_dispatch='(c.pc==0x80526a3cu||c.pc==0x8052a824u);'
    if candidate.count(old_dispatch)!=1:
        raise ValueError('V379 previous V378 dispatcher completion gate moved')
    staged=staged[:start]+candidate.replace(old_dispatch,new_dispatch,1)+staged[end:]
    old_trial='  continue; // finish this authenticated NAND-only bounded trial'
    if staged.count(old_trial)!=1:
        raise ValueError('V379 original trial loop completion changed')
    new_trial=(
        '  const bool v379_completed=v378_completed&&\n'
        '       nwii::runtime::v379_time_seen==1u&&\n'
        '       c.pc==0x8052a824u;\n'
        '  std::cout<<"V379_NAND_TIME_TRIAL dispatch="<<unsigned(\n'
        '               nwii::runtime::v378_dispatch_seen==1u)\n'
        '           <<" time="<<unsigned(nwii::runtime::v379_time_seen==1u)\n'
        '           <<" completed="<<unsigned(v379_completed)<<std::endl;\n'
        '  check(v379_completed,\n'
        '        "V379 authentic NAND IRQ dispatcher did not call original OSGetTime");\n'
        +old_trial
    )
    staged=staged.replace(old_trial,new_trial,1)
    if (staged.count(MARKER)!=1 or staged.count(TRIAL)!=1 or
        staged.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        staged.count('V378_NAND_DISPATCH_ENTRY route=')!=1 or
        staged.count('V377_NAND_HANDLER_ENTRY vector=')!=1):
        raise ValueError('V379 original guest evidence not unique')
    return staged

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prior_private_harness',type=Path)
    parser.add_argument('next_private_harness',type=Path)
    args=parser.parse_args()
    try:
        if args.next_private_harness.exists() or args.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        staged=patch(args.prior_private_harness.read_text(encoding='utf-8'))
        with args.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(staged)
    except (OSError,ValueError):
        print('V379_NAND_TIME_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V379_NAND_TIME_ROUTE installed=1 original_guest=1 no_synthetic_time=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
