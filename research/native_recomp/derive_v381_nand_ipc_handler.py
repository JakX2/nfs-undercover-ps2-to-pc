#!/usr/bin/env python3
"""V381: authenticate original NAND Y1 IRQ -> registered IPC handler.

After V380's OSDisableScheduler guest checkpoint, run its original PPC
instructions until the Wii dispatcher invokes the *registered* slot-27 IPC
handler at 0x80519318. Prior V200/V220 confirmed the original call ABI
for distinct SC/Y2 interrupts. For NAND, independently verify live Y1
hardware, installed IRQ registration and guest-saved exception frame;
do not assume any SC-specific IOS_Open reply code or fabricate a callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v380_scheduler_seen=0u;'
STATE_NEW='''static unsigned v380_scheduler_seen=0u;
static unsigned v381_ipc_seen=0u;
static uint64_t v381_scheduler_inst=0u;'''
STOP='''    ++v380_scheduler_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v380_scheduler_seen;
    v381_scheduler_inst=ctx.inst_count;
    return; // execute original OSDisableScheduler and IRQ handler dispatch
  }'''
MARKER='V381_NAND_IPC_ENTRY registered='
TRIAL='V381_NAND_IPC_TRIAL scheduler='
TRACE=r"""
  // V381: first original guest IPC handler from NAND Y1 slot 27.
  if(v377_live&&v380_scheduler_seen==1u&&v381_ipc_seen==0u&&
     addr==0x80519318u&&ctx.pc==addr){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool y1=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const uint32_t frame=ctx.gpr[4];
    const bool mapped=frame!=0u&&(frame&7u)==0u&&
         frame<=0xfffffe60u&&ctx.mmu.get_ptr(frame)!=nullptr&&
         ctx.mmu.get_ptr(frame+415u)!=nullptr;
    const bool table=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr;
    const bool registered=table&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr;
    const bool context=mapped&&
         ctx.mmu.read32(frame+408u)==v377_resume&&
         ctx.mmu.read32(frame+412u)==v377_srr1&&
         ctx.mmu.read32(frame+132u)==v377_lr&&
         ctx.mmu.read32(frame+136u)==v377_ctr&&
         ctx.mmu.read32(frame+140u)==v377_xer;
    const bool abi=ctx.gpr[3]==27u&&ctx.ctr==addr&&
         ctx.lr==0x80526cacu&&
         v377_vector_seen==1u&&v377_handler_seen==1u&&
         v378_dispatch_seen==1u&&v379_time_seen==1u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v381_scheduler_inst;
    std::cout<<"V381_NAND_IPC_ENTRY registered="<<unsigned(registered)
             <<" context="<<unsigned(context)
             <<" abi="<<unsigned(abi)
             <<" y1="<<unsigned(y1)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<std::endl;
    check(registered&&context&&abi&&y1&&masked&&advanced,
          "V381 original NAND Y1 did not dispatch registered Wii IPC handler");
    ++v381_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or
        source.count('V380_NAND_SCHED_ENTRY guest=')!=1 or
        source.count('V380_NAND_SCHED_TRIAL time=')!=1 or
        source.count('const bool v380_completed=')!=1 or
        source.count('nwii::runtime::v380_time_inst=0u;')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V381 authenticated original NAND scheduler seam changed')
    output=source.replace(STATE_OLD,STATE_NEW,1)
    reset='nwii::runtime::v380_time_inst=0u;'
    output=output.replace(
        reset,
        reset+'\n'+
        '  nwii::runtime::v381_ipc_seen=0u;\n'+
        '  nwii::runtime::v381_scheduler_inst=0u;',
        1
    )
    output=output.replace(STOP,CONTINUE,1)
    output=output.replace(HEAD,HEAD+TRACE,1)
    pc_pairs=(
      ('(c.pc==0x80526ce0u||c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u);',
       '(c.pc==0x80526ce0u||c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u||c.pc==0x80519318u);'),
      ('(c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u);',
       '(c.pc==0x80526a3cu||c.pc==0x8052a824u||c.pc==0x805293f8u||c.pc==0x80519318u);'),
      ('(c.pc==0x8052a824u||c.pc==0x805293f8u);',
       '(c.pc==0x8052a824u||c.pc==0x805293f8u||c.pc==0x80519318u);')
    )
    for old,new in pc_pairs:
        if output.count(old)!=1:
            raise ValueError('V381 inherited original guest success PC geometry differs')
        output=output.replace(old,new,1)
    start=output.index('const bool v380_completed=')
    end=output.index('std::cout<<"V380_NAND_SCHED_TRIAL',start)
    segment=output[start:end]
    old='c.pc==0x805293f8u;'
    new='(c.pc==0x805293f8u||c.pc==0x80519318u);'
    if segment.count(old)!=1:
        raise ValueError('V381 V380 scheduler-trial completion geometry changed')
    output=output[:start]+segment.replace(old,new,1)+output[end:]
    old_continue='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(old_continue)!=1:
        raise ValueError('V381 owner trial stop moved')
    new_trial=(
        '  const bool v381_completed=v380_completed&&\n'
        '       nwii::runtime::v381_ipc_seen==1u&&\n'
        '       c.pc==0x80519318u;\n'
        '  std::cout<<"V381_NAND_IPC_TRIAL scheduler="<<unsigned(\n'
        '               nwii::runtime::v380_scheduler_seen==1u)\n'
        '           <<" ipc="<<unsigned(nwii::runtime::v381_ipc_seen==1u)\n'
        '           <<" completed="<<unsigned(v381_completed)<<std::endl;\n'
        '  check(v381_completed,\n'
        '        "V381 original NAND interrupt never reached registered IPC handler");\n'
        +old_continue
    )
    output=output.replace(old_continue,new_trial,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(STOP)!=0 or output.count(CONTINUE)!=1 or
        output.count('V380_NAND_SCHED_ENTRY guest=')!=1 or
        output.count('V379_NAND_TIME_ENTRY guest=')!=1):
        raise ValueError('V381 transformation not unique or guest trace changed')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    args=p.parse_args()
    try:
        if args.next_private_harness.exists() or args.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        generated=patch(args.prior_private_harness.read_text(encoding='utf-8'))
        with args.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(generated)
    except (ValueError,OSError):
        print('V381_NAND_IPC_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V381_NAND_IPC_ROUTE installed=1 original_guest=1 irq_slot=27 no_synthetic_reply=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
