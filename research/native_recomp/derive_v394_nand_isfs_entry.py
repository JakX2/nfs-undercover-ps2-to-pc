#!/usr/bin/env python3
"""V394: optional original NAND OSSetCurrentContext -> _isfsFuncCb entry.

The historical SC/Y1 reply path reached OSSetCurrentContext and then
the original _isfsFuncCb at 0x804F0E04 via guest indirect call. This is
an independently guarded NAND follow-up to the V393 first guest call.
It may execute the context setter only if the original observed target
and LR match. It must not fabricate an IOS result or set a callback PC.

At the guest callback ENTRY classify original request callback, status,
and userdata fields against the live guest frame. They are evidence, not
assertions that the NAND completion callback ran.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v393_next_seen=0u;"
STATE_NEW="""static unsigned v393_next_seen=0u;
static unsigned v394_context_seen=0u,v394_isfs_seen=0u;
static uint64_t v394_context_inst=0u;"""
STOP="""    v393_next_pc=addr;v393_next_lr=ctx.lr;
    ++v393_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }"""
CONTINUE="""    v393_next_pc=addr;v393_next_lr=ctx.lr;
    ++v393_next_seen;
    if(addr==0x805228ccu&&ctx.lr==0x80519298u){
      v394_context_seen=1u;
      v394_context_inst=ctx.inst_count;
      return; // execute original guest OSSetCurrentContext
    }
    ctx.is_running=false;throw ExceptionStop{};
  }"""
RESET="nwii::runtime::v393_next_lr=0u;"
PREVIOUS='''  check(v393_completed,
        "V393 original non-cache NAND callee did not reach next guest function");'''
MARKER="V394_NAND_ISFS_ENTRY guest="
TRIAL="V394_NAND_ISFS_TRIAL context="
TRACE=r"""
  // Original post-ACK guest indirect _isfsFuncCb entry, never synthesized.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v392_kind==1u&&v393_next_seen==1u&&
     v394_context_seen==1u&&v394_isfs_seen==0u&&
     addr==0x804f0e04u&&ctx.pc==addr&&ctx.lr==0x805192acu){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=control.has_value()&&flag.has_value()&&
         ((*control&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&
         !ipc70_bus.external_irq_level();
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const uint32_t request=ctx.gpr[31];
    const bool header=request<=0xffffffe0u&&
         ctx.mmu.get_ptr(request)!=nullptr&&
         ctx.mmu.get_ptr(request+39u)!=nullptr;
    const bool selected=header&&ctx.mmu.read32(request+32u)==addr;
    const bool result=header&&ctx.gpr[3]==ctx.mmu.read32(request+4u);
    const bool userdata=header&&ctx.gpr[4]==ctx.mmu.read32(request+36u);
    const bool guest=ctx.inst_count>v394_context_inst&&
         v393_next_pc==0x805228ccu&&v393_next_lr==0x80519298u&&
         v394_context_seen==1u&&ctx.pc==addr;
    const bool verified=guest&&clear&&masked&&registered;
    std::cout<<"V394_NAND_ISFS_ENTRY guest="<<unsigned(guest)
             <<" clear="<<unsigned(clear)
             <<" masked="<<unsigned(masked)
             <<" registered="<<unsigned(registered)
             <<" mapped="<<unsigned(header)
             <<" selected="<<unsigned(selected)
             <<" result="<<unsigned(result)
             <<" userdata="<<unsigned(userdata)<<std::endl;
    check(verified,"V394 original NAND callback entry lost guest IRQ state");
    ++v394_isfs_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
TRIAL_PROOF=r"""  const bool v394_completed=v393_completed&&
       nwii::runtime::v394_context_seen==1u&&
       nwii::runtime::v394_isfs_seen==1u&&
       c.pc==0x804f0e04u&&c.lr==0x805192acu;
  std::cout<<"V394_NAND_ISFS_TRIAL context="<<unsigned(
                nwii::runtime::v394_context_seen==1u)
           <<" isfs="<<unsigned(nwii::runtime::v394_isfs_seen==1u)
           <<" completed="<<unsigned(v394_completed)<<std::endl;
  check(v394_completed,
        "V394 original NAND reply path did not enter authentic ISFS callback");"""

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(STATE_OLD)!=1 or
        source.count(STOP)!=1 or source.count(RESET)!=1 or
        source.count(PREVIOUS)!=1 or
        source.count("V393_NAND_NEXT_CALL guest=")!=1 or
        source.count("V393_NAND_NEXT_TRIAL first=")!=1 or
        source.count("V392_NAND_POST_CACHE_EVENT kind=")!=1 or
        source.count("V391_NAND_POST_ACK_EVENT kind=")!=1 or
        source.count("V389_NAND_FLAG_ACK before=")!=1 or
        MARKER in source or TRIAL in source or "v394_isfs_seen" in source):
        raise ValueError("V394 original NAND context/ISFS source seam changed")
    s=source.replace(STATE_OLD,STATE_NEW,1)
    s=s.replace(STOP,CONTINUE,1)
    s=s.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v394_context_seen=0u;\n"+
        "  nwii::runtime::v394_isfs_seen=0u;\n"+
        "  nwii::runtime::v394_context_inst=0u;",1)
    s=s.replace(HEAD,HEAD+TRACE,1)
    old="nwii::runtime::v393_next_seen==1u&&\n         c.pc==nwii::runtime::v393_next_pc&&\n         c.lr==nwii::runtime::v393_next_lr"
    later="nwii::runtime::v394_isfs_seen==1u&&\n         c.pc==0x804f0e04u&&c.lr==0x805192acu"
    for begin,end in (
        ("const bool v390_completed=", 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
        ("const bool v391_completed=", 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
        ("const bool v392_completed=", 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
    ):
        start=s.index(begin);stop=s.index(end,start)
        block=s[start:stop]
        if block.count(old)!=1:
            raise ValueError("V394 inherited NAND guest stop proof moved")
        block=block.replace(old,"(("+old+")||\n        ("+later+"))",1)
        s=s[:start]+block+s[stop:]
    begin=s.index("const bool v393_completed=")
    end=s.index('std::cout<<"V393_NAND_NEXT_TRIAL',begin)
    block=s[begin:end]
    previous="c.pc==nwii::runtime::v393_next_pc&&\n       c.lr==nwii::runtime::v393_next_lr;"
    if block.count(previous)!=1:
        raise ValueError("V394 V393 context guest stop proof changed")
    block=block.replace(previous,
        "((c.pc==nwii::runtime::v393_next_pc&&\n"+
        "         c.lr==nwii::runtime::v393_next_lr)||\n"+
        "        ("+later+"));",1)
    s=s[:begin]+block+s[end:]
    s=s.replace(PREVIOUS,PREVIOUS+"\n"+TRIAL_PROOF,1)
    if (s.count(MARKER)!=1 or s.count(TRIAL)!=1 or
        STOP in s or s.count(CONTINUE)!=1 or
        s.count("V370_NAND_FLAG_W1C n=")!=1 or
        s.count("try{run_game(c);}")!=source.count("try{run_game(c);}") or
        s.count("V393_NAND_NEXT_CALL guest=")!=1):
        raise ValueError("V394 guest callback observer did not preserve prior route")
    return s

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        output=patch(a.prior_private_harness.read_text(encoding="utf-8"))
        with a.next_private_harness.open("x",encoding="utf-8") as out:
            out.write(output)
    except (OSError,ValueError):
        print("V394_NAND_ISFS_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V394_NAND_ISFS_ROUTE installed=1 original_guest=1 no_forced_result=1 callback_entry_only=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
