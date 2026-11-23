#!/usr/bin/env python3
"""V384: run original NAND IpcReplyHandler to its first guest PPCCTRL read.

V383 tests genuine IPCInterruptHandler -> IpcReplyHandler at 0x805190C0.
Earlier V223 observed its original hardware read call at 0x8051905C,
LR=0x805190E8. Require that call independently on the real NAND Y1
interrupt without injecting an IOS reply, ACK, memory patch or callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v383_reply_seen=0u;'
STATE_NEW='''static unsigned v383_reply_seen=0u;
static unsigned v384_read_seen=0u;
static uint64_t v384_reply_inst=0u;'''
STOP='''    ++v383_reply_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v383_reply_seen;
    v384_reply_inst=ctx.inst_count;
    return; // execute authentic translated guest IpcReplyHandler
  }'''
MARKER='V384_NAND_REPLY_READ caller='
TRIAL='V384_NAND_REPLY_READ_TRIAL reply='
TRACE=r"""
  // V384: first authentic PPC register-read guest call by reply handler.
  if(v377_live&&v383_reply_seen==1u&&v384_read_seen==0u&&
     addr==0x8051905cu&&ctx.pc==addr){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool caller=ctx.lr==0x805190e8u&&
         v383_reply_seen==1u&&v382_next_seen==1u&&
         v382_next_pc==0x8051905cu;
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v384_reply_inst;
    std::cout<<"V384_NAND_REPLY_READ caller="<<unsigned(caller)
             <<" irq="<<unsigned(irq)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<std::endl;
    check(caller&&irq&&registered&&masked&&advanced,
          "V384 original NAND IpcReplyHandler did not call PPCCTRL reader");
    ++v384_read_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or
        source.count('V383_NAND_REPLY_ENTRY read=')!=1 or
        source.count('V383_NAND_REPLY_TRIAL next=')!=1 or
        source.count('const bool v383_completed=')!=1 or
        source.count('nwii::runtime::v383_read_inst=0u;')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V384 original NAND IpcReplyHandler source seam changed')
    output=source.replace(STATE_OLD,STATE_NEW,1)
    reset='nwii::runtime::v383_read_inst=0u;'
    output=output.replace(
        reset,
        reset+'\n'+
        '  nwii::runtime::v384_read_seen=0u;\n'+
        '  nwii::runtime::v384_reply_inst=0u;',
        1
    )
    output=output.replace(STOP,CONTINUE,1)
    output=output.replace(HEAD,HEAD+TRACE,1)
    old='(nwii::runtime::v383_reply_seen==1u&&c.pc==0x805190c0u)'
    next='(nwii::runtime::v384_read_seen==1u&&c.pc==0x8051905cu)'
    new='(nwii::runtime::v383_reply_seen==1u&&(c.pc==0x805190c0u||'+next+'))'
    if output.count(old)!=6:
        raise ValueError('V384 inherited original IPC handler PC gates changed')
    output=output.replace(old,new)
    start=output.index('const bool v383_completed=')
    end=output.index('std::cout<<"V383_NAND_REPLY_TRIAL',start)
    segment=output[start:end]
    oldpc='c.pc==0x805190c0u;'
    newpc='(c.pc==0x805190c0u||'+next+');'
    if segment.count(oldpc)!=1:
        raise ValueError('V384 prior IpcReplyHandler entry trial PC moved')
    output=output[:start]+segment.replace(oldpc,newpc,1)+output[end:]
    tail='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(tail)!=1:
        raise ValueError('V384 original bounded NAND trial moved')
    addition=(
        '  const bool v384_completed=v383_completed&&\n'
        '       nwii::runtime::v384_read_seen==1u&&\n'
        '       c.pc==0x8051905cu;\n'
        '  std::cout<<"V384_NAND_REPLY_READ_TRIAL reply="<<unsigned(\n'
        '               nwii::runtime::v383_reply_seen==1u)\n'
        '           <<" reader="<<unsigned(nwii::runtime::v384_read_seen==1u)\n'
        '           <<" completed="<<unsigned(v384_completed)<<std::endl;\n'
        '  check(v384_completed,\n'
        '        "V384 original NAND reply handler did not call guest PPCCTRL read");\n'
        +tail
    )
    output=output.replace(tail,addition,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(STOP)!=0 or output.count(CONTINUE)!=1 or
        output.count('V383_NAND_REPLY_ENTRY read=')!=1):
        raise ValueError('V384 original Nintendo IPC read observer invalid')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('previous_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        with a.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(patch(a.previous_private_harness.read_text(encoding='utf-8')))
    except (OSError,ValueError):
        print('V384_NAND_REPLY_READ_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V384_NAND_REPLY_READ_ROUTE installed=1 original_guest=1 no_forced_reply=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
