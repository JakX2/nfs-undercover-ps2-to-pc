#!/usr/bin/env python3
"""V382: follow original NAND Y1 registered IPC handler to guest helper.

This is deliberately a bounded *next-call* observation, not a claim that an
IOS reply or NAND callback has completed. V381 authenticates the guest
slot-27 IPC handler at 0x80519318. Run its translated PowerPC body until the
first naturally linked original guest call within that handler, and report
whether it matches prior Wii IPC MMIO/cache helpers. Do not synthesize calls,
registers, hardware completion or results.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v381_ipc_seen=0u;'
STATE_NEW='''static unsigned v381_ipc_seen=0u;
static unsigned v382_next_seen=0u;
static uint64_t v382_ipc_inst=0u;
static uint32_t v382_next_pc=0u;'''
STOP='''    ++v381_ipc_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v381_ipc_seen;
    v382_ipc_inst=ctx.inst_count;
    return; // execute original registered Wii IPCInterruptHandler
  }'''
MARKER='V382_NAND_IPC_NEXT guest='
TRIAL='V382_NAND_IPC_TRIAL ipc='
TRACE=r"""
  // V382: the first original translated call with LR inside IPC handler.
  if(v377_live&&v381_ipc_seen==1u&&v382_next_seen==0u&&
     addr>=0x80400000u&&addr<0x80600000u&&
     ctx.pc==addr&&ctx.lr>=0x80519318u&&
     ctx.lr<0x805194c4u&&(ctx.lr&3u)==0u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool signal=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool table=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr;
    const bool registered=table&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool guest=ctx.pc==addr&&
         ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u&&
         v377_vector_seen==1u&&v381_ipc_seen==1u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v382_ipc_inst;
    // Classify, never require, the prior V221 native MMIO/cache callsites.
    const bool known=addr==0x8051905cu||addr==0x8051906cu||
                     addr==0x8051b060u;
    std::cout<<"V382_NAND_IPC_NEXT guest="<<unsigned(guest)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<" known="<<unsigned(known)
             <<" signal="<<unsigned(signal)
             <<std::endl;
    check(guest&&registered&&masked&&advanced,
          "V382 original NAND registered IPC handler did not reach guest helper");
    v382_next_pc=addr;
    ++v382_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or
        source.count('V381_NAND_IPC_ENTRY registered=')!=1 or
        source.count('V381_NAND_IPC_TRIAL scheduler=')!=1 or
        source.count('const bool v381_completed=')!=1 or
        source.count('nwii::runtime::v381_scheduler_inst=0u;')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V382 original NAND IPC entry instrumentation changed')
    output=source.replace(STATE_OLD,STATE_NEW,1)
    reset='nwii::runtime::v381_scheduler_inst=0u;'
    output=output.replace(
        reset,reset+'\n'+
        '  nwii::runtime::v382_next_seen=0u;\n'+
        '  nwii::runtime::v382_ipc_inst=0u;\n'+
        '  nwii::runtime::v382_next_pc=0u;',1
    )
    output=output.replace(STOP,CONTINUE,1)
    output=output.replace(HEAD,HEAD+TRACE,1)
    old_pc='||c.pc==0x80519318u);'
    guard='(nwii::runtime::v382_next_seen==1u&&c.pc==nwii::runtime::v382_next_pc)'
    if output.count(old_pc)!=4:
        raise ValueError('V382 prior vector/handler/IRQ/time stopping PC gates changed')
    output=output.replace(old_pc,'||c.pc==0x80519318u||'+guard+');')
    start=output.index('const bool v381_completed=')
    end=output.index('std::cout<<"V381_NAND_IPC_TRIAL',start)
    prev=output[start:end]
    old='c.pc==0x80519318u;'
    new='(c.pc==0x80519318u||'+guard+');'
    if prev.count(old)!=1:
        raise ValueError('V382 prior authenticated IPC handler trial gate changed')
    output=output[:start]+prev.replace(old,new,1)+output[end:]
    end_trial='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(end_trial)!=1:
        raise ValueError('V382 bounded NAND trial loop changed')
    new_trial=(
        '  const bool v382_completed=v381_completed&&\n'
        '       nwii::runtime::v382_next_seen==1u&&\n'
        '       c.pc==nwii::runtime::v382_next_pc;\n'
        '  std::cout<<"V382_NAND_IPC_TRIAL ipc="<<unsigned(\n'
        '               nwii::runtime::v381_ipc_seen==1u)\n'
        '           <<" next="<<unsigned(nwii::runtime::v382_next_seen==1u)\n'
        '           <<" completed="<<unsigned(v382_completed)<<std::endl;\n'
        '  check(v382_completed,\n'
        '        "V382 registered Wii IPC handler never called original guest helper");\n'
        +end_trial
    )
    output=output.replace(end_trial,new_trial,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(STOP)!=0 or output.count(CONTINUE)!=1 or
        output.count('V381_NAND_IPC_ENTRY registered=')!=1):
        raise ValueError('V382 guest source injection not reversible or unique')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('previous_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    args=p.parse_args()
    try:
        if args.next_private_harness.exists() or args.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        with args.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(patch(args.previous_private_harness.read_text(encoding='utf-8')))
    except (ValueError,OSError):
        print('V382_NAND_IPC_NEXT_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V382_NAND_IPC_NEXT_ROUTE installed=1 original_guest=1 classify_only=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
