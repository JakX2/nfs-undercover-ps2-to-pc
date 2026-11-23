#!/usr/bin/env python3
"""V393: first original post-cache non-cache callee's next PowerPC guest call.

V392 observes authentic Wii NAND reply-handler call entries after two
guest W1Cs and repeated cache invalidation. It stops at the first
reply-handler-owned non-cache guest callee or a bounded 24-call budget.

This optional next stage continues the observed non-cache callee ONLY
when V392 independently authenticated that exact original function
entry. The next naturally called translated PowerPC function is
classified against known OS context, cache and ISFS callback targets.
No guest function address, CPU register, IOS reply or callback is
fabricated. The observation does not imply callback execution.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v392_kind=0u,v392_calls=0u,v392_caches=0u;"
STATE_NEW="""static unsigned v392_kind=0u,v392_calls=0u,v392_caches=0u;
static unsigned v393_next_seen=0u;
static uint64_t v393_start_inst=0u;
static uint32_t v393_next_pc=0u,v393_next_lr=0u;"""
STOP="""      check(verified,"V392 NAND original post-cache successor not authenticated");
      ctx.is_running=false;throw ExceptionStop{};
    }"""
CONTINUE="""      check(verified,"V392 NAND original post-cache successor not authenticated");
      if(v392_kind==1u){
        v393_start_inst=ctx.inst_count;
        return; // execute exactly the observed original non-cache callee
      }
      ctx.is_running=false;throw ExceptionStop{};
    }"""
RESET="nwii::runtime::v392_next_lr=0u;"
PREVIOUS='''  check(v392_completed,
        "V392 original NAND post-cache chain did not reach bounded guest call");'''
MARKER="V393_NAND_NEXT_CALL guest="
TRIAL="V393_NAND_NEXT_TRIAL first="
TRACE=r"""
  // V393: first genuine AOT guest call after an owner-authenticated
  // non-cache reply-handler callee, never the 24-call capped fallback.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v392_kind==1u&&v393_next_seen==0u&&
     ctx.pc==addr&&addr>=0x80400000u&&addr<0x80600000u&&
     (addr&3u)==0u&&ctx.inst_count>v393_start_inst&&
     ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&(ctx.lr&3u)==0u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctrl.has_value()&&flag.has_value()&&
         ((*ctrl&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&
         !ipc70_bus.external_irq_level();
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool from_reply=ctx.lr>=0x805190c0u&&
         ctx.lr<0x80519318u;
    const bool clear_context=addr==0x80522af4u;
    const bool set_context=addr==0x805228ccu;
    const bool cache=addr==0x80522294u;
    const bool isfs=addr==0x804f0e04u;
    const bool guest=ctx.inst_count>v393_start_inst&&
         v392_kind==1u&&v392_next_pc!=0u&&
         v392_next_pc!=0x80522294u;
    const bool verified=guest&&clear&&registered&&masked;
    std::cout<<"V393_NAND_NEXT_CALL guest="<<unsigned(guest)
             <<" clear="<<unsigned(clear)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" reply="<<unsigned(from_reply)
             <<" clearctx="<<unsigned(clear_context)
             <<" setctx="<<unsigned(set_context)
             <<" cache="<<unsigned(cache)
             <<" isfs="<<unsigned(isfs)<<std::endl;
    check(verified,
          "V393 native NAND reply path lost original guest frame after cache");
    v393_next_pc=addr;v393_next_lr=ctx.lr;
    ++v393_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
TRIAL_PROOF=r"""  const bool v393_completed=v392_completed&&
       nwii::runtime::v392_kind==1u&&
       nwii::runtime::v393_next_seen==1u&&
       nwii::runtime::v393_next_pc!=0u&&
       c.pc==nwii::runtime::v393_next_pc&&
       c.lr==nwii::runtime::v393_next_lr;
  std::cout<<"V393_NAND_NEXT_TRIAL first="<<unsigned(
                nwii::runtime::v392_kind==1u)
           <<" next="<<unsigned(nwii::runtime::v393_next_seen==1u)
           <<" completed="<<unsigned(v393_completed)<<std::endl;
  check(v393_completed,
        "V393 original non-cache NAND callee did not reach next guest function");"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or source.count(RESET)!=1 or
        source.count(PREVIOUS)!=1 or
        source.count("V392_NAND_POST_CACHE_EVENT kind=")!=1 or
        source.count("V392_NAND_POST_CACHE_TRIAL kind=")!=1 or
        source.count("V391_NAND_POST_ACK_EVENT kind=")!=1 or
        source.count("V390_NAND_POST_ACK guest=")!=1 or
        source.count("V389_NAND_FLAG_ACK before=")!=1 or
        MARKER in source or TRIAL in source or "v393_next_seen" in source):
        raise ValueError("V393 original NAND V392 guest successor seam changed")
    s=source.replace(STATE_OLD,STATE_NEW,1)
    s=s.replace(STOP,CONTINUE,1)
    s=s.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v393_next_seen=0u;\n"+
        "  nwii::runtime::v393_start_inst=0u;\n"+
        "  nwii::runtime::v393_next_pc=0u;\n"+
        "  nwii::runtime::v393_next_lr=0u;",1)
    s=s.replace(HEAD,HEAD+TRACE,1)
    old="nwii::runtime::v392_kind!=0u&&\n         c.pc==nwii::runtime::v392_next_pc&&\n         c.lr==nwii::runtime::v392_next_lr"
    later="nwii::runtime::v393_next_seen==1u&&\n         c.pc==nwii::runtime::v393_next_pc&&\n         c.lr==nwii::runtime::v393_next_lr"
    # Older completion proofs retain their own checkpoints and accept
    # only the subsequent original registered guest-stop witness.
    for begin,end in (
        ("const bool v390_completed=", 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
        ("const bool v391_completed=", 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
    ):
        pos=s.index(begin);stop=s.index(end,pos)
        block=s[pos:stop]
        if block.count(old)!=1:
            raise ValueError("V393 preceding NAND guest completion proof moved")
        block=block.replace(old,"(("+old+")||\n        ("+later+"))",1)
        s=s[:pos]+block+s[stop:]
    begin=s.index("const bool v392_completed=")
    end=s.index('std::cout<<"V392_NAND_POST_CACHE_TRIAL',begin)
    block=s[begin:end]
    oldstop="c.pc==nwii::runtime::v392_next_pc&&\n       c.lr==nwii::runtime::v392_next_lr;"
    if block.count(oldstop)!=1:
        raise ValueError("V393 V392 real successor current PC check moved")
    block=block.replace(oldstop,
        "((c.pc==nwii::runtime::v392_next_pc&&\n"+
        "         c.lr==nwii::runtime::v392_next_lr)||\n"+
        "        ("+later+"));",1)
    s=s[:begin]+block+s[end:]
    s=s.replace(PREVIOUS,PREVIOUS+"\n"+TRIAL_PROOF,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or
        STOP in s or s.count(CONTINUE)!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V393 guest post-cache continuation not uniquely installed")
    return s

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prior_private_harness",type=Path)
    parser.add_argument("next_private_harness",type=Path)
    args=parser.parse_args()
    try:
        if args.next_private_harness.exists() or args.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        transformed=patch(args.prior_private_harness.read_text(encoding="utf-8"))
        with args.next_private_harness.open("x",encoding="utf-8") as out:
            out.write(transformed)
    except (OSError,ValueError):
        print("V393_NAND_GUEST_NEXT_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V393_NAND_GUEST_NEXT_ROUTE installed=1 original_guest=1 no_forced_callback=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
