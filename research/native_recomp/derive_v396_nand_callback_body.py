#!/usr/bin/env python3
"""V396 candidate: execute naturally selected original ISFS callback AOT body.

V395 observes the first original _isfsFuncCb nested guest callee. Unlike
the earlier V250 callback path, its concrete address is *not* assumed to
be 0x8051E06C. Continue only when its actual guest callback-table
selection and userdata agree, then classify the next original function
entry with a strict 24-call cap. The callback return/result remains
unverified. Never set a PC, CTR, status, register, memory or IOS reply.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v395_next_seen=0u;"
STATE_NEW="""static unsigned v395_next_seen=0u;
static unsigned v396_kind=0u,v396_calls=0u;
static uint64_t v396_start_inst=0u;
static uint32_t v396_stop_pc=0u,v396_stop_lr=0u;"""
STOP="""    v395_next_pc=addr;v395_next_lr=ctx.lr;
    ++v395_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }"""
CONTINUE="""    v395_next_pc=addr;v395_next_lr=ctx.lr;
    ++v395_next_seen;
    if(mapped&&selected&&userdata){
      v396_start_inst=ctx.inst_count;
      return; // actual guest-selected callback body, not a guessed NAND address
    }
    ctx.is_running=false;throw ExceptionStop{};
  }"""
RESET="nwii::runtime::v395_next_lr=0u;"
PREVIOUS='''  check(v395_completed,
        "V395 original NAND _isfsFuncCb did not reach its next guest call");'''
MARKER="V396_NAND_CB_BODY kind="
TRIAL="V396_NAND_CB_TRIAL kind="
TRACE=r"""
  // Original PowerPC function calls following the guest-selected callback.
  if(v250_candidate_mode&&v250_nand_seen==1u&&v388_active&&
     v389_after_y1&&v389_flag_seen==1u&&
     v394_isfs_seen==1u&&v395_next_seen==1u&&
     v396_kind==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&(addr&3u)==0u&&
     ctx.inst_count>v396_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctl.has_value()&&flag.has_value()&&
         ((*ctl&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&!ipc70_bus.external_irq_level();
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool owned=ctx.lr>=v395_next_pc&&
         ctx.lr-v395_next_pc<0x800u&&(ctx.lr&3u)==0u;
    const bool cache=addr==0x80522294u;
    const bool context=addr==0x80522af4u||addr==0x805228ccu;
    const bool nand=addr==0x8051e06cu;
    const bool guest=v395_next_pc!=0u&&
         v395_next_seen==1u&&ctx.inst_count>v396_start_inst;
    // V395 proved the post-ACK snapshot at the selected callee entry.
    // Original guest code may legitimately change IPC/EE state afterwards.
    // Keep the later snapshot diagnostic, not an invariant or forced exit.
    check(guest,
          "V396 original ISFS-selected guest callee provenance lost");
    ++v396_calls;
    if(owned||v396_calls==24u){
      const bool bounded=!owned&&v396_calls==24u;
      const bool verified=guest&&(owned||bounded);
      v396_kind=owned?1u:2u;
      v396_stop_pc=addr;v396_stop_lr=ctx.lr;
      std::cout<<"V396_NAND_CB_BODY kind="<<v396_kind
               <<" verified="<<unsigned(verified)
               <<" owned="<<unsigned(owned)
               <<" clear="<<unsigned(clear)
               <<" masked="<<unsigned(masked)
               <<" registered="<<unsigned(registered)
               <<" cache="<<unsigned(cache)
               <<" context="<<unsigned(context)
               <<" nand="<<unsigned(nand)
               <<" bounded="<<unsigned(bounded)<<std::endl;
      check(verified,
            "V396 original callback body next guest entry not verified");
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
"""
TRIAL_PROOF=r"""  const bool v396_completed=v395_completed&&
       (nwii::runtime::v396_kind==1u||
        (nwii::runtime::v396_kind==2u&&
         nwii::runtime::v396_calls==24u))&&
       nwii::runtime::v396_stop_pc!=0u&&
       c.pc==nwii::runtime::v396_stop_pc&&
       c.lr==nwii::runtime::v396_stop_lr;
  std::cout<<"V396_NAND_CB_TRIAL kind="<<nwii::runtime::v396_kind
           <<" stopped="<<unsigned(!c.is_running)
           <<" completed="<<unsigned(v396_completed)<<std::endl;
  check(v396_completed,
        "V396 original guest-selected ISFS callback did not reach next call");"""
def patch(s:str)->str:
    if (s.count(HEAD)!=1 or s.count(STATE_OLD)!=1 or
        s.count(STOP)!=1 or s.count(RESET)!=1 or
        s.count(PREVIOUS)!=1 or
        s.count("V395_NAND_ISFS_NEXT guest=")!=1 or
        s.count("V395_NAND_ISFS_TRIAL isfs=")!=1 or
        s.count("V394_NAND_ISFS_ENTRY guest=")!=1 or
        s.count("V389_NAND_FLAG_ACK before=")!=1 or
        MARKER in s or TRIAL in s or "v396_kind" in s):
        raise ValueError("V396 selected callback original guest seam changed")
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(STOP,CONTINUE,1)
    out=out.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v396_kind=0u;\n"+
        "  nwii::runtime::v396_calls=0u;\n"+
        "  nwii::runtime::v396_start_inst=0u;\n"+
        "  nwii::runtime::v396_stop_pc=0u;\n"+
        "  nwii::runtime::v396_stop_lr=0u;",1)
    out=out.replace(HEAD,HEAD+TRACE,1)
    old=("nwii::runtime::v395_next_seen==1u&&\n"
         "         c.pc==nwii::runtime::v395_next_pc&&\n"
         "         c.lr==nwii::runtime::v395_next_lr")
    later=("nwii::runtime::v396_kind!=0u&&\n"
           "         c.pc==nwii::runtime::v396_stop_pc&&\n"
           "         c.lr==nwii::runtime::v396_stop_lr")
    for begin,end in (
        ("const bool v390_completed=", 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
        ("const bool v391_completed=", 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
        ("const bool v392_completed=", 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
        ("const bool v393_completed=", 'std::cout<<"V393_NAND_NEXT_TRIAL'),
        ("const bool v394_completed=", 'std::cout<<"V394_NAND_ISFS_TRIAL'),
    ):
        start=out.index(begin);stop=out.index(end,start)
        block=out[start:stop]
        if block.count(old)!=1:
            raise ValueError("V396 inherited guest evidence PC seam moved")
        block=block.replace(old,"(("+old+")||\n        ("+later+"))",1)
        out=out[:start]+block+out[stop:]
    start=out.index("const bool v395_completed=")
    end=out.index('std::cout<<"V395_NAND_ISFS_TRIAL',start)
    block=out[start:end]
    oldend=("c.pc==nwii::runtime::v395_next_pc&&\n"
            "       c.lr==nwii::runtime::v395_next_lr;")
    if block.count(oldend)!=1:
        raise ValueError("V396 preceding callback completion witness moved")
    block=block.replace(oldend,
        "((c.pc==nwii::runtime::v395_next_pc&&\n"
        "         c.lr==nwii::runtime::v395_next_lr)||\n"
        "        ("+later+"));",1)
    out=out[:start]+block+out[end:]
    out=out.replace(PREVIOUS,PREVIOUS+"\n"+TRIAL_PROOF,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL)!=1 or
        STOP in out or out.count(CONTINUE)!=1 or
        out.count("V370_NAND_FLAG_W1C n=")!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V395_NAND_ISFS_NEXT guest=")!=1):
        raise ValueError("V396 post-callback original guest transformation not unique")
    return out
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
        print("V396_NAND_CB_BODY_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V396_NAND_CB_BODY_ROUTE installed=1 selected_guest=1 bounded=24 no_fake_callback=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
