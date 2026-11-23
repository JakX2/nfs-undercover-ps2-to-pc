#!/usr/bin/env python3
"""V391: bounded original NAND post-ACK call chain toward context/callback.

V390 first verifies a genuine original guest call after Broadway Y1 and
Hollywood W1C both completed. Continue that original translated call without
a new host resume/PC jump. Observe the next naturally linked original call
whose LR belongs to the NAND IPC reply handler, or stop after sixteen other
translated call entries. Recognize context/cache/callback *targets* but never
treat a classified call entry as execution of the NAND callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v390_call_seen=0u;"
STATE_NEW="""static unsigned v390_call_seen=0u;
static unsigned v391_kind=0u,v391_calls=0u;
static uint64_t v391_start_inst=0u;
static uint32_t v391_next_pc=0u,v391_next_lr=0u;"""
STOP="""    v390_call_pc=addr;v390_call_lr=ctx.lr;
    ++v390_call_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }"""
CONTINUE="""    v390_call_pc=addr;v390_call_lr=ctx.lr;
    ++v390_call_seen;
    v391_start_inst=ctx.inst_count;
    return; // original post-ACK guest function executes unmodified
  }"""
RESET="nwii::runtime::v390_call_lr=0u;"
PREVIOUS_TRIAL='''  check(v390_completed,
        "V390 original NAND guest never left Hollywood ACK for next callee");'''
MARKER="V391_NAND_POST_ACK_EVENT kind="
TRIAL="V391_NAND_POST_ACK_TRIAL kind="
TRACE=r"""
  // Bounded genuine function entries after both original hardware ACKs.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v390_call_seen==1u&&v391_kind==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&(addr&3u)==0u&&
     ctx.inst_count>v391_start_inst){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto ctl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=ctl.has_value()&&flag.has_value()&&
         ((*ctl&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&
         !ipc70_bus.external_irq_level();
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool owner=ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&
         (ctx.lr&3u)==0u;
    const bool cache=addr==0x80522294u;
    const bool context=addr==0x80522af4u||addr==0x805228ccu;
    const bool callback=addr==0x804f0e04u;
    const bool guest=v389_flag_seen==1u&&v390_call_seen==1u&&
         ctx.inst_count>v391_start_inst;
    check(clear&&masked&&guest,
          "V391 original post-ACK NAND call chain reasserted IRQ");
    ++v391_calls;
    if(owner||v391_calls==16u){
      const bool cap=!owner&&v391_calls==16u;
      const bool valid=clear&&masked&&guest&&
           (owner||cap);
      v391_kind=owner?1u:2u;
      v391_next_pc=addr;v391_next_lr=ctx.lr;
      std::cout<<"V391_NAND_POST_ACK_EVENT kind="<<v391_kind
               <<" verified="<<unsigned(valid)
               <<" owner="<<unsigned(owner)
               <<" cache="<<unsigned(cache)
               <<" context="<<unsigned(context)
               <<" callback="<<unsigned(callback)
               <<" cap="<<unsigned(cap)<<std::endl;
      check(valid,"V391 original NAND reply successor boundary not verified");
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
"""
TRIAL_PROOF=r"""  const bool v391_completed=v390_completed&&
       (nwii::runtime::v391_kind==1u||
        (nwii::runtime::v391_kind==2u&&
         nwii::runtime::v391_calls==16u))&&
       nwii::runtime::v391_next_pc!=0u&&
       c.pc==nwii::runtime::v391_next_pc&&
       c.lr==nwii::runtime::v391_next_lr;
  std::cout<<"V391_NAND_POST_ACK_TRIAL kind="<<nwii::runtime::v391_kind
           <<" stopped="<<unsigned(!c.is_running)
           <<" completed="<<unsigned(v391_completed)<<std::endl;
  check(v391_completed,
        "V391 original NAND post-ACK call trace did not reach real boundary");"""

def patch(s:str)->str:
    if (s.count(HEAD)!=1 or s.count(STATE_OLD)!=1 or
        s.count(STOP)!=1 or s.count(RESET)!=1 or
        s.count(PREVIOUS_TRIAL)!=1 or
        s.count("V390_NAND_POST_ACK guest=")!=1 or
        s.count("V390_NAND_POST_ACK_TRIAL flag=")!=1 or
        s.count("V389_NAND_FLAG_ACK before=")!=1 or
        s.count("V385_NAND_ARMMSG_MIRROR coherent=")!=1 or
        MARKER in s or TRIAL in s or "v391_kind" in s):
        raise ValueError("V391 authenticated original post-ACK source seam changed")
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(STOP,CONTINUE,1)
    out=out.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v391_kind=0u;\n"+
        "  nwii::runtime::v391_calls=0u;\n"+
        "  nwii::runtime::v391_start_inst=0u;\n"+
        "  nwii::runtime::v391_next_pc=0u;\n"+
        "  nwii::runtime::v391_next_lr=0u;",1)
    out=out.replace(HEAD,HEAD+TRACE,1)
    # V390's own entry witness remains mandatory, but now accepts the
    # later authenticated original guest stop instead of requiring its
    # earlier function entry to remain the current PC.
    begin=out.index("const bool v390_completed=")
    end=out.index('std::cout<<"V390_NAND_POST_ACK_TRIAL',begin)
    segment=out[begin:end]
    old="c.pc==nwii::runtime::v390_call_pc&&\n       c.lr==nwii::runtime::v390_call_lr;"
    new="((c.pc==nwii::runtime::v390_call_pc&&\n         c.lr==nwii::runtime::v390_call_lr)||\n        (nwii::runtime::v391_kind!=0u&&\n         c.pc==nwii::runtime::v391_next_pc&&\n         c.lr==nwii::runtime::v391_next_lr));"
    if segment.count(old)!=1:raise ValueError("V391 inherited V390 stop geometry moved")
    out=out[:begin]+segment.replace(old,new,1)+out[end:]
    out=out.replace(PREVIOUS_TRIAL,PREVIOUS_TRIAL+"\n"+TRIAL_PROOF,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL)!=1 or
        out.count(STOP)!=0 or out.count(CONTINUE)!=1 or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V391 guest bounded continuation not uniquely installed")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        staged=patch(a.prior_private_harness.read_text(encoding="utf-8"))
        with a.next_private_harness.open("x",encoding="utf-8") as out:out.write(staged)
    except (ValueError,OSError):
        print("V391_NAND_POST_ACK_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V391_NAND_POST_ACK_ROUTE installed=1 original_guest=1 bounded=16 no_fabricated_callback=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
