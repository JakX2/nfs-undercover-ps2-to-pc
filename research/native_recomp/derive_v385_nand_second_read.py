#!/usr/bin/env python3
"""V385: execute original NAND reply-handler first PPC read to second read.

V384 owner lane observes the first original IpcReplyHandler PPCCTRL reader,
0x8051905C with LR 0x805190E8. The earlier V224 SC Y1 path proved a second
call of the same original Wii reader at LR=0x805190FC. Authenticate this
independently on NAND without fabricating IOS replies, MMIO ACK, context
state or return values. The Y1 and Hollywood flags remain guest-owned.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v384_read_seen=0u;'
STATE_NEW='''static unsigned v384_read_seen=0u;
static unsigned v385_second_seen=0u;
static uint64_t v385_first_read_inst=0u;'''
STOP='''    ++v384_read_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    ++v384_read_seen;
    v385_first_read_inst=ctx.inst_count;
    return; // execute original PPC reader and resume IpcReplyHandler
  }'''
MARKER='V385_NAND_SECOND_READ caller='
TRIAL='V385_NAND_SECOND_READ_TRIAL first='
TRACE=r"""
  // V385: second original PPC register read call, now from LR 0x805190FC.
  if(v377_live&&v384_read_seen==1u&&v385_second_seen==0u&&
     addr==0x8051905cu&&ctx.pc==addr&&ctx.lr==0x805190fcu){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool caller=ctx.pc==addr&&ctx.lr==0x805190fcu&&
         v383_reply_seen==1u&&v384_read_seen==1u;
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v385_first_read_inst;
    std::cout<<"V385_NAND_SECOND_READ caller="<<unsigned(caller)
             <<" irq="<<unsigned(irq)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<std::endl;
    check(caller&&irq&&registered&&masked&&advanced,
          "V385 original NAND reply handler never issued second guest PPC read");
    ++v385_second_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or
        source.count('V384_NAND_REPLY_READ caller=')!=1 or
        source.count('V384_NAND_REPLY_READ_TRIAL reply=')!=1 or
        source.count('const bool v384_completed=')!=1 or
        source.count('nwii::runtime::v384_reply_inst=0u;')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V385 authenticated V384 original reply read seam changed')
    out=source.replace(STATE_OLD,STATE_NEW,1)
    reset='nwii::runtime::v384_reply_inst=0u;'
    out=out.replace(
        reset,
        reset+'\n'+
        '  nwii::runtime::v385_second_seen=0u;\n'+
        '  nwii::runtime::v385_first_read_inst=0u;',
        1
    )
    out=out.replace(STOP,CONTINUE,1)
    out=out.replace(HEAD,HEAD+TRACE,1)
    tail='  continue; // finish this authenticated NAND-only bounded trial'
    if out.count(tail)!=1:
        raise ValueError('V385 authenticated NAND trial end moved')
    check=(
        '  const bool v385_completed=v384_completed&&\n'
        '       nwii::runtime::v385_second_seen==1u&&\n'
        '       c.pc==0x8051905cu&&c.lr==0x805190fcu;\n'
        '  std::cout<<"V385_NAND_SECOND_READ_TRIAL first="<<unsigned(\n'
        '               nwii::runtime::v384_read_seen==1u)\n'
        '           <<" second="<<unsigned(nwii::runtime::v385_second_seen==1u)\n'
        '           <<" completed="<<unsigned(v385_completed)<<std::endl;\n'
        '  check(v385_completed,\n'
        '        "V385 original NAND IpcReplyHandler second reader not entered");\n'
        +tail
    )
    out=out.replace(tail,check,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL)!=1 or
        out.count(STOP)!=0 or out.count(CONTINUE)!=1 or
        out.count('V384_NAND_REPLY_READ caller=')!=1):
        raise ValueError('V385 original Nintendo NAND read observer invalid')
    return out

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
    except (ValueError,OSError):
        print('V385_NAND_SECOND_READ_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V385_NAND_SECOND_READ_ROUTE installed=1 original_guest=1 no_forced_ack=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
