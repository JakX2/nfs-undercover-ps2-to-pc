#!/usr/bin/env python3
"""V395: original NAND _isfsFuncCb next genuine translated guest call.

Continue from V394's authenticated original _isfsFuncCb entry and execute
the guest function without changing PowerPC state, IOS response data,
request header or callback pointer. Observe only the naturally linked
guest callee whose LR belongs to the callback body. Classify the NAND
open completion callback at 0x8051E06C and its request/result/userdata
ABI. The classification never forces the call or reports callback
execution just from entry.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v394_context_seen=0u,v394_isfs_seen=0u;"
STATE_NEW="""static unsigned v394_context_seen=0u,v394_isfs_seen=0u;
static unsigned v395_next_seen=0u;
static uint64_t v395_isfs_inst=0u;
static uint32_t v395_next_pc=0u,v395_next_lr=0u;"""
STOP="""    ++v394_isfs_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }"""
CONTINUE="""    ++v394_isfs_seen;
    v395_isfs_inst=ctx.inst_count;
    return; // genuine original _isfsFuncCb PowerPC body executes
  }"""
RESET="nwii::runtime::v394_context_inst=0u;"
PREVIOUS='''  check(v394_completed,
        "V394 original NAND reply path did not enter authentic ISFS callback");'''
MARKER="V395_NAND_ISFS_NEXT guest="
TRIAL="V395_NAND_ISFS_TRIAL isfs="
TRACE=r"""
  // Original translated function calls out of _isfsFuncCb.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v394_context_seen==1u&&v394_isfs_seen==1u&&
     v395_next_seen==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&(addr&3u)==0u&&
     ctx.lr>=0x804f0e04u&&ctx.lr<0x804f0f84u&&
     (ctx.lr&3u)==0u&&ctx.inst_count>v395_isfs_inst){
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
    const uint32_t data=ctx.gpr[31];
    const bool mapped=data<=0xfffffef8u&&
         ctx.mmu.get_ptr(data)!=nullptr&&
         ctx.mmu.get_ptr(data+263u)!=nullptr;
    const bool selected=mapped&&ctx.mmu.read32(data+256u)==addr;
    const bool userdata=mapped&&ctx.gpr[4]==ctx.mmu.read32(data+260u);
    const bool nand=addr==0x8051e06cu&&ctx.lr==0x804f0f54u;
    const bool guest=ctx.inst_count>v395_isfs_inst&&
         v394_isfs_seen==1u&&v393_next_pc==0x805228ccu;
    const bool verified=guest&&clear&&masked&&registered;
    std::cout<<"V395_NAND_ISFS_NEXT guest="<<unsigned(guest)
             <<" clear="<<unsigned(clear)
             <<" masked="<<unsigned(masked)
             <<" registered="<<unsigned(registered)
             <<" mapped="<<unsigned(mapped)
             <<" selected="<<unsigned(selected)
             <<" userdata="<<unsigned(userdata)
             <<" nand="<<unsigned(nand)<<std::endl;
    check(verified,
          "V395 original NAND ISFS callback did not reach authentic guest callee");
    v395_next_pc=addr;v395_next_lr=ctx.lr;
    ++v395_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
TRIAL_PROOF=r"""  const bool v395_completed=v394_completed&&
       nwii::runtime::v395_next_seen==1u&&
       nwii::runtime::v395_next_pc!=0u&&
       c.pc==nwii::runtime::v395_next_pc&&
       c.lr==nwii::runtime::v395_next_lr;
  std::cout<<"V395_NAND_ISFS_TRIAL isfs="<<unsigned(
                nwii::runtime::v394_isfs_seen==1u)
           <<" next="<<unsigned(nwii::runtime::v395_next_seen==1u)
           <<" completed="<<unsigned(v395_completed)<<std::endl;
  check(v395_completed,
        "V395 original NAND _isfsFuncCb did not reach its next guest call");"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or source.count(RESET)!=1 or
        source.count(PREVIOUS)!=1 or
        source.count("V394_NAND_ISFS_ENTRY guest=")!=1 or
        source.count("V394_NAND_ISFS_TRIAL context=")!=1 or
        source.count("V393_NAND_NEXT_CALL guest=")!=1 or
        source.count("V392_NAND_POST_CACHE_EVENT kind=")!=1 or
        source.count("V389_NAND_FLAG_ACK before=")!=1 or
        MARKER in source or TRIAL in source or "v395_next_seen" in source):
        raise ValueError("V395 original NAND ISFS callback source seam changed")
    s=source.replace(STATE_OLD,STATE_NEW,1)
    s=s.replace(STOP,CONTINUE,1)
    s=s.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v395_next_seen=0u;\n"+
        "  nwii::runtime::v395_isfs_inst=0u;\n"+
        "  nwii::runtime::v395_next_pc=0u;\n"+
        "  nwii::runtime::v395_next_lr=0u;",1)
    s=s.replace(HEAD,HEAD+TRACE,1)
    old="nwii::runtime::v394_isfs_seen==1u&&\n         c.pc==0x804f0e04u&&c.lr==0x805192acu"
    later="nwii::runtime::v395_next_seen==1u&&\n         c.pc==nwii::runtime::v395_next_pc&&\n         c.lr==nwii::runtime::v395_next_lr"
    for begin,end in (
        ("const bool v390_completed=", 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
        ("const bool v391_completed=", 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
        ("const bool v392_completed=", 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
        ("const bool v393_completed=", 'std::cout<<"V393_NAND_NEXT_TRIAL'),
    ):
        i=s.index(begin);j=s.index(end,i);block=s[i:j]
        if block.count(old)!=1:
            raise ValueError("V395 inherited guest/ISFS stop geometry changed")
        block=block.replace(old,"(("+old+")||\n        ("+later+"))",1)
        s=s[:i]+block+s[j:]
    begin=s.index("const bool v394_completed=")
    end=s.index('std::cout<<"V394_NAND_ISFS_TRIAL',begin)
    block=s[begin:end]
    oldend="c.pc==0x804f0e04u&&c.lr==0x805192acu;"
    if block.count(oldend)!=1:
        raise ValueError("V395 inherited ISFS entry trial PC changed")
    block=block.replace(oldend,
        "((c.pc==0x804f0e04u&&c.lr==0x805192acu)||\n"+
        "        ("+later+"));",1)
    s=s[:begin]+block+s[end:]
    s=s.replace(PREVIOUS,PREVIOUS+"\n"+TRIAL_PROOF,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or STOP in s or
        s.count(CONTINUE)!=1 or
        s.count("V370_NAND_FLAG_W1C n=")!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count("V394_NAND_ISFS_ENTRY guest=")!=1):
        raise ValueError("V395 original callback entry continuation not unique")
    return s

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        staged=patch(a.prior_private_harness.read_text(encoding="utf-8"))
        with a.next_private_harness.open("x",encoding="utf-8") as out:
            out.write(staged)
    except (OSError,ValueError):
        print("V395_NAND_ISFS_NEXT_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V395_NAND_ISFS_NEXT_ROUTE installed=1 original_guest=1 callback_classify_only=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
