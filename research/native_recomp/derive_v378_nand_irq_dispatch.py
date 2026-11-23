#!/usr/bin/env python3
"""V378: execute original NAND Y1 OS exception handler to genuine dispatcher.

V377 owner-original proved 13 complete retained vector -> handler-entry
trials (no source-derived handler code published). Continue the installed
original Wii OS exception-handler body from 0x80526CE0 until the genuine
0x80526A3C IRQ dispatcher call and authenticate the saved PPC frame.
The earlier SC/Y2 trial proofs remain unchanged outside NAND mode.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from derive_v377_nand_vector_handler import STATE,TRACE,HEAD

V377_HANDLER='V377_NAND_HANDLER_ENTRY vector='
V377_TRIAL='V377_NAND_HANDLER_TRIAL stopped='
MARKER='V378_NAND_DISPATCH_ENTRY route='
TRIAL='V378_NAND_DISPATCH_TRIAL handler='
STATE_ADD=r"""
static unsigned v378_dispatch_seen=0u;
static uint64_t v378_handler_inst=0u;
"""
OLD_STOP='''      ++v377_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }'''
NEW_STOP='''      ++v377_handler_seen;
      v378_handler_inst=ctx.inst_count;
      return; // execute original translated Wii exception-handler body
    }'''
DISPATCH=r"""
  // V378: genuine guest OS exception-handler call to IRQ dispatcher.
  if(v377_live&&v377_handler_seen==1u&&v378_dispatch_seen==0u&&
     addr==0x80526a3cu){
    const uint32_t frame=ctx.gpr[4];
    const bool mapped=frame!=0u&&(frame&7u)==0u&&
         frame<=0xfffffe60u&&ctx.mmu.get_ptr(frame)!=nullptr&&
         ctx.mmu.get_ptr(frame+415u)!=nullptr;
    const bool route=ctx.pc==addr&&ctx.gpr[3]==4u&&mapped&&
         v377_vector_seen==1u;
    bool regs=route;
    if(route){
      for(unsigned i=6u;i<32u;++i)
        regs=regs&&ctx.mmu.read32(frame+4u*i)==v377_gprs[i];
    }
    const bool status=route&&
         ctx.mmu.read32(frame+408u)==v377_resume&&
         ctx.mmu.read32(frame+412u)==v377_srr1&&
         ctx.mmu.read32(frame+132u)==v377_lr&&
         ctx.mmu.read32(frame+136u)==v377_ctr&&
         ctx.mmu.read32(frame+140u)==v377_xer;
    const auto ctrl=ipc70_bus.read32(undercover::wii::IosBus::IPC+
                                    undercover::wii::IpcMailbox::PPCCTRL);
    const bool y1=ctrl.has_value()&&
         ((*ctrl&undercover::wii::IpcMailbox::Y1)!=0u)&&
         ((*ctrl&undercover::wii::IpcMailbox::Y2)==0u)&&
         ipc70_bus.external_irq_level();
    const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool advanced=ctx.inst_count>v378_handler_inst;
    std::cout<<"V378_NAND_DISPATCH_ENTRY route="<<unsigned(route)
             <<" regs="<<unsigned(regs)
             <<" status="<<unsigned(status)
             <<" masked="<<unsigned(masked)
             <<" y1="<<unsigned(y1)
             <<" advanced="<<unsigned(advanced)
             <<std::endl;
    check(route&&regs&&status&&masked&&y1&&advanced,
          "V378 original NAND Y1 OS handler failed to dispatch saved guest context");
    ++v378_dispatch_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""

def patch(source:str)->str:
    if (source.count(STATE+HEAD+TRACE)!=1 or
        source.count(OLD_STOP)!=1 or
        source.count(V377_HANDLER)!=1 or
        source.count(V377_TRIAL)!=1 or
        source.count('const bool v377_completed=')!=1 or
        MARKER in source or TRIAL in source):
        raise ValueError('V378 authenticated V377 host/native handler boundary changed')
    rewritten_trace=TRACE.replace(OLD_STOP,NEW_STOP,1)+DISPATCH
    output=source.replace(STATE+HEAD+TRACE,
                          STATE+STATE_ADD+HEAD+rewritten_trace,1)
    start=output.index('const bool v377_completed=')
    end=output.index('std::cout<<"V377_NAND_HANDLER_TRIAL',start)
    candidate=output[start:end]
    old_tail='!c.is_running&&c.pc==0x80526ce0u;'
    if candidate.count(old_tail)!=1:
        raise ValueError('V378 authenticated former handler-only completion moved')
    new_tail=('!c.is_running&&\n'
              '             (c.pc==0x80526ce0u||c.pc==0x80526a3cu);')
    output=output[:start]+candidate.replace(old_tail,new_tail,1)+output[end:]
    marker='        "V377 original NAND vector never reached actual Wii handler entry");'
    continue_line='  continue; // finish this authenticated NAND-only bounded trial'
    if output.count(marker)!=1 or output.count(continue_line)!=1:
        raise ValueError('V378 NAND trial check or loop completion changed')
    insert=(
      '  const bool v378_completed=v377_completed&&\n'
      '       nwii::runtime::v378_dispatch_seen==1u&&\n'
      '       c.pc==0x80526a3cu;\n'
      '  std::cout<<"V378_NAND_DISPATCH_TRIAL handler="<<unsigned(\n'
      '               nwii::runtime::v377_handler_seen==1u)\n'
      '           <<" dispatch="<<unsigned(nwii::runtime::v378_dispatch_seen==1u)\n'
      '           <<" completed="<<unsigned(v378_completed)<<std::endl;\n'
      '  check(v378_completed,\n'
      '        "V378 original NAND OS handler did not reach translated IRQ dispatcher");\n'
    )
    # Preserve both the historical V160 assertion and the V377 handler
    # proof, and require a *separate* V378 dispatcher before continuing.
    output=output.replace(continue_line,insert+continue_line,1)
    if (output.count(MARKER)!=1 or output.count(TRIAL)!=1 or
        output.count(V377_HANDLER)!=1 or output.count(V377_TRIAL)!=1 or
        output.count('V160 did not execute original SC Y1 exception vector to handler')!=1 or
        output.count('v378_dispatch_seen==1u')<2):
        raise ValueError('V378 handler/dispatcher observation was not unique')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_harness',type=Path)
    p.add_argument('new_private_harness',type=Path)
    args=p.parse_args()
    try:
        if args.new_private_harness.exists() or args.new_private_harness.is_symlink():
            raise ValueError('output_exists')
        source=args.prior_private_harness.read_text(encoding='utf-8')
        transformed=patch(source)
        with args.new_private_harness.open('x',encoding='utf-8') as out:
            out.write(transformed)
    except (ValueError,OSError):
        print('V378_NAND_DISPATCH_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V378_NAND_DISPATCH_ROUTE installed=1 original_guest=1 handler_body=1 sc_oracle_preserved=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
