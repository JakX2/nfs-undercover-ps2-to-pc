#!/usr/bin/env python3
"""V383: execute first original NAND IPC hardware read into IpcReplyHandler.

V382 observes the first genuine translated callee after registered guest
IPCInterruptHandler entry. The earlier V222 SC/Y1 run found an IPC PPCCTRL
reader at 0x8051905C followed by IpcReplyHandler 0x805190C0. Require those
exact original calls afresh in the NAND path. Execute original PPC, preserve
actual Y1 hardware and IOS response, and stop before the original reply-
handler body. Do not imply completion of the NAND callback or guest boot.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
HEAD='void trace_call(uint32_t addr, CPUContext&ctx){'
STATE_OLD='static unsigned v382_next_seen=0u;'
STATE_NEW='''static unsigned v382_next_seen=0u;
static unsigned v383_reply_seen=0u;
static uint64_t v383_read_inst=0u;'''
STOP='''    v382_next_pc=addr;
    ++v382_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
CONTINUE='''    v382_next_pc=addr;
    ++v382_next_seen;
    v383_read_inst=ctx.inst_count;
    return; // execute original Wii PPC IPC register read helper
  }'''
MARKER='V383_NAND_REPLY_ENTRY read='
TRIAL='V383_NAND_REPLY_TRIAL next='
TRACE=r"""
  // V383: guest IpcReplyHandler entry after unchanged IPC register read.
  if(v377_live&&v382_next_seen==1u&&v383_reply_seen==0u&&
     addr==0x805190c0u&&ctx.pc==addr){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool irq=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
         ((*flag&H::IPC_PPC)!=0u)&&ipc70_bus.external_irq_level();
    const bool read=v382_next_pc==0x8051905cu&&
         v382_next_seen==1u&&v381_ipc_seen==1u;
    const bool caller=ctx.lr==0x80519354u&&
         ctx.pc==addr&&ctx.ctr!=0u;
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v383_read_inst;
    std::cout<<"V383_NAND_REPLY_ENTRY read="<<unsigned(read)
             <<" caller="<<unsigned(caller)
             <<" registered="<<unsigned(registered)
             <<" irq="<<unsigned(irq)
             <<" masked="<<unsigned(masked)
             <<" advanced="<<unsigned(advanced)
             <<std::endl;
    check(read&&caller&&registered&&irq&&masked&&advanced,
          "V383 original NAND IPC read did not enter authentic IpcReplyHandler");
    ++v383_reply_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or
        source.count('V382_NAND_IPC_NEXT guest=')!=1 or
        source.count('V382_NAND_IPC_TRIAL ipc=')!=1 or
        source.count('const bool v382_completed=')!=1 or
        source.count('nwii::runtime::v382_next_pc=0u;')!=1 or
        source.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V383 authenticated V382 original IPC helper seam changed')
    output=source.replace(STATE_OLD,STATE_NEW,1)
    reset='nwii::runtime::v382_next_pc=0u;'
    output=output.replace(
        reset,
        reset+'\n'+
        '  nwii::runtime::v383_reply_seen=0u;\n'+
        '  nwii::runtime::v383_read_inst=0u;',
        1
    )
    output=output.replace(STOP,CONTINUE,1)
    output=output.replace(HEAD,HEAD+TRACE,1)
    old_guard='(nwii::runtime::v382_next_seen==1u&&c.pc==nwii::runtime::v382_next_pc)'
    reply_guard='(nwii::runtime::v383_reply_seen==1u&&c.pc==0x805190c0u)'
    new_guard='(nwii::runtime::v382_next_seen==1u&&('\
        'c.pc==nwii::runtime::v382_next_pc||'+reply_guard+'))'
    if output.count(old_guard)!=5:
        raise ValueError('V383 original vector-through-IPC PC proof gates changed')
    output=output.replace(old_guard,new_guard)
    start=output.index('const bool v382_completed=')
    end=output.index('std::cout<<"V382_NAND_IPC_TRIAL',start)
    old='c.pc==nwii::runtime::v382_next_pc;'
    new='(c.pc==nwii::runtime::v382_next_pc||'+reply_guard+');'
    trial=output[start:end]
    if trial.count(old)!=1:
        raise ValueError('V383 V382 first IPC callee completion gate moved')
    output=output[:start]+trial.replace(old,new,1)+output[end:]
    tail='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(tail)!=1:
        raise ValueError('V383 NAND trial completion moved')
    addition=(
        '  const bool v383_completed=v382_completed&&\n'
        '       nwii::runtime::v383_reply_seen==1u&&\n'
        '       c.pc==0x805190c0u;\n'
        '  std::cout<<"V383_NAND_REPLY_TRIAL next="<<unsigned(\n'
        '               nwii::runtime::v382_next_seen==1u)\n'
        '           <<" reply="<<unsigned(nwii::runtime::v383_reply_seen==1u)\n'
        '           <<" completed="<<unsigned(v383_completed)<<std::endl;\n'
        '  check(v383_completed,\n'
        '        "V383 original NAND Y1 IPC read did not call IpcReplyHandler");\n'
        +tail
    )
    output=output.replace(tail,addition,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(STOP)!=0 or output.count(CONTINUE)!=1 or
        output.count('V382_NAND_IPC_NEXT guest=')!=1):
        raise ValueError('V383 NAND IpcReplyHandler source insertion invalid')
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
    except (ValueError,OSError):
        print('V383_NAND_REPLY_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V383_NAND_REPLY_ROUTE installed=1 original_guest=1 no_fabricated_reply=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
