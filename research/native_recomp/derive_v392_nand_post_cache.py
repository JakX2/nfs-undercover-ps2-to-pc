#!/usr/bin/env python3
"""V392: bounded original NAND reply flow beyond repeated post-ACK cache calls.

V390 authenticated the first DCInvalidateRange guest call after original
PPCCTRL.Y1 and Hollywood PPC_FLAG W1Cs. V391 authenticated the NEXT
reply-handler-owned call, also a cache call in retained original samples.

Continue that already-called original guest function without restarting an
interrupted native MMIO operation. Traverse at most 24 additional genuine
translated function entries, stopping at the first reply-handler-owned
NON-cache callee or the fixed budget. Identify OS context/callback targets
only as classifications. Never force a guest callee, response or callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v391_kind=0u,v391_calls=0u;"
STATE_NEW="""static unsigned v391_kind=0u,v391_calls=0u;
static unsigned v392_kind=0u,v392_calls=0u,v392_caches=0u;
static uint64_t v392_start_inst=0u;
static uint32_t v392_next_pc=0u,v392_next_lr=0u;"""
STOP="""      check(valid,"V391 original NAND reply successor boundary not verified");
      ctx.is_running=false;throw ExceptionStop{};
    }"""
CONTINUE="""      check(valid,"V391 original NAND reply successor boundary not verified");
      if(v391_kind==1u){
        v392_start_inst=ctx.inst_count;
        return; // execute authentic post-ACK original guest callee
      }
      ctx.is_running=false;throw ExceptionStop{};
    }"""
RESET="nwii::runtime::v391_next_lr=0u;"
PREVIOUS='''  check(v391_completed,
        "V391 original NAND post-ACK call trace did not reach real boundary");'''
MARKER="V392_NAND_POST_CACHE_EVENT kind="
TRIAL="V392_NAND_POST_CACHE_TRIAL kind="
TRACE=r"""
  // First non-cache reply-owner call, or a hard 24-call original PPC bound.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v391_kind==1u&&v392_kind==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&(addr&3u)==0u&&
     ctx.inst_count>v392_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&
         !ipc70_bus.external_irq_level();
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool owner=ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&
         (ctx.lr&3u)==0u;
    const bool cache=addr==0x80522294u;
    const bool context=addr==0x80522af4u||addr==0x805228ccu;
    const bool callback=addr==0x804f0e04u;
    const bool guest=ctx.inst_count>v392_start_inst&&
         v391_next_pc!=0u&&v390_call_seen==1u&&v391_kind==1u;
    check(guest&&clear&&masked&&registered,
          "V392 native NAND post-cache call chain lost guest context or cleared IRQ");
    ++v392_calls;
    if(cache)++v392_caches;
    if((owner&&!cache)||v392_calls==24u){
      const bool bounded=!(owner&&!cache)&&v392_calls==24u;
      const bool verified=guest&&clear&&masked&&registered&&
           ((owner&&!cache)||bounded);
      v392_kind=(owner&&!cache)?1u:2u;
      v392_next_pc=addr;v392_next_lr=ctx.lr;
      std::cout<<"V392_NAND_POST_CACHE_EVENT kind="<<v392_kind
               <<" verified="<<unsigned(verified)
               <<" owner="<<unsigned(owner)
               <<" cache="<<unsigned(cache)
               <<" context="<<unsigned(context)
               <<" callback="<<unsigned(callback)
               <<" bounded="<<unsigned(bounded)
               <<" caches="<<v392_caches<<std::endl;
      check(verified,"V392 NAND original post-cache successor not authenticated");
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
"""
TRIAL_PROOF=r"""  const bool v392_completed=v391_completed&&
       (nwii::runtime::v392_kind==1u||
        (nwii::runtime::v392_kind==2u&&nwii::runtime::v392_calls==24u))&&
       nwii::runtime::v392_next_pc!=0u&&
       c.pc==nwii::runtime::v392_next_pc&&
       c.lr==nwii::runtime::v392_next_lr;
  std::cout<<"V392_NAND_POST_CACHE_TRIAL kind="<<nwii::runtime::v392_kind
           <<" stopped="<<unsigned(!c.is_running)
           <<" completed="<<unsigned(v392_completed)<<std::endl;
  check(v392_completed,
        "V392 original NAND post-cache chain did not reach bounded guest call");"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or source.count(RESET)!=1 or
        source.count(PREVIOUS)!=1 or
        source.count("V391_NAND_POST_ACK_EVENT kind=")!=1 or
        source.count("V391_NAND_POST_ACK_TRIAL kind=")!=1 or
        source.count("V390_NAND_POST_ACK guest=")!=1 or
        source.count("V389_NAND_FLAG_ACK before=")!=1 or
        MARKER in source or TRIAL in source or "v392_kind" in source):
        raise ValueError("V392 original NAND repeated cache successor source seam changed")
    s=source.replace(STATE_OLD,STATE_NEW,1)
    s=s.replace(STOP,CONTINUE,1)
    s=s.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v392_kind=0u;\n"+
        "  nwii::runtime::v392_calls=0u;\n"+
        "  nwii::runtime::v392_caches=0u;\n"+
        "  nwii::runtime::v392_start_inst=0u;\n"+
        "  nwii::runtime::v392_next_pc=0u;\n"+
        "  nwii::runtime::v392_next_lr=0u;",1)
    s=s.replace(HEAD,HEAD+TRACE,1)
    # Permit earlier V390 and V391 evidence checks to terminate at the
    # strictly later real original guest stop. No prior marker is erased.
    earlier="(nwii::runtime::v391_kind!=0u&&\n         c.pc==nwii::runtime::v391_next_pc&&\n         c.lr==nwii::runtime::v391_next_lr)"
    later="nwii::runtime::v392_kind!=0u&&\n         c.pc==nwii::runtime::v392_next_pc&&\n         c.lr==nwii::runtime::v392_next_lr"
    start=s.index("const bool v390_completed=")
    end=s.index('std::cout<<"V390_NAND_POST_ACK_TRIAL',start)
    span=s[start:end]
    if span.count(earlier)!=1:raise ValueError("V392 earlier V390 owner call geometry changed")
    # Preserve GCC -Wparentheses correctness: group each complete
    # authenticated stop alternative, not just its PC/LR subexpression.
    s=s[:start]+span.replace(earlier,"("+earlier+"||\n        ("+later+"))",1)+s[end:]
    start=s.index("const bool v391_completed=")
    end=s.index('std::cout<<"V391_NAND_POST_ACK_TRIAL',start)
    span=s[start:end]
    earlier2="c.pc==nwii::runtime::v391_next_pc&&\n       c.lr==nwii::runtime::v391_next_lr;"
    if span.count(earlier2)!=1:raise ValueError("V392 V391 owner call geometry changed")
    s=s[:start]+span.replace(earlier2,
        "(("+earlier2[:-1]+")||\n       ("+later+"));",1)+s[end:]
    s=s.replace(PREVIOUS,PREVIOUS+"\n"+TRIAL_PROOF,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or STOP in s or
        s.count(CONTINUE)!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V392 original guest post-cache observer not unique")
    return s

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        with a.next_private_harness.open("x",encoding="utf-8") as out:
            out.write(patch(a.prior_private_harness.read_text(encoding="utf-8")))
    except (ValueError,OSError):
        print("V392_NAND_POST_CACHE_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V392_NAND_POST_CACHE_ROUTE installed=1 original_guest=1 cap=24 no_fabricated_callback=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
