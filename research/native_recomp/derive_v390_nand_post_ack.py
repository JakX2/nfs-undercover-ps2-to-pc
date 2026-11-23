#!/usr/bin/env python3
"""V390: execute original NAND IPC reply code past both actual guest IRQ ACKs.

V389 owner-original proved guest PPCCTRL.Y1 W1C followed by a distinct
Hollywood PPC_FLAG.IPC_PPC W1C, lowering the native IRQ line. Instead of
stopping inside HW_Reg_Write32 immediately after the Hollywood W1C, allow
that *same original translated function call* to finish. Observe the next
genuine translated PPC callee owned by the original IpcReplyHandler.

Known previous SC/Y1 behavior entered DCInvalidateRange (0x80522294),
but the NAND callback must establish its own guest callsite. Report this
as a classification, not a required/forced branch. No host-side ACK,
guest context rewrite, IOS response overwrite, or invented callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
STATE_OLD="static unsigned v389_flag_seen=0u;"
STATE_NEW="""static unsigned v389_flag_seen=0u;
static unsigned v390_call_seen=0u;
static uint64_t v390_flag_inst=0u;
static uint32_t v390_call_pc=0u,v390_call_lr=0u;"""
FLAG_STOP="""        ++v389_flag_seen;
        ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
      }"""
FLAG_CONTINUE="""        ++v389_flag_seen;
        v390_flag_inst=ipc70_ram.cpu->inst_count;
        // Continue the same original guest MMIO writer after native W1C.
      }"""
RESET="nwii::runtime::v389_y1_inst=0u;"
PREV_TRIAL='''  check(v389_completed,
        "V389 original NAND Hollywood flag ACK did not release native IRQ");'''
MARKER="V390_NAND_POST_ACK guest="
TRIAL="V390_NAND_POST_ACK_TRIAL flag="
TRACE=r"""
  // First original translated callee after BOTH guest-owned MMIO W1Cs.
  if(v250_candidate_mode&&v250_nand_seen==1u&&
     v388_active&&v389_after_y1&&v389_flag_seen==1u&&
     v390_call_seen==0u&&ctx.pc==addr&&
     addr>=0x80400000u&&addr<0x80600000u&&(addr&3u)==0u&&
     ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u&&(ctx.lr&3u)==0u){
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const bool clear=control.has_value()&&flag.has_value()&&
         ((*control&(M::Y1|M::Y2))==0u)&&
         ((*flag&H::IPC_PPC)==0u)&&
         !ipc70_bus.external_irq_level();
    const bool registered=ctx.mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
         ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
    const bool guest=ctx.pc==addr&&ctx.inst_count>v390_flag_inst&&
         v388_kind==1u&&v389_flag_seen==1u&&
         v377_vector_seen==1u&&v381_ipc_seen==1u;
    const bool masked=(ctx.msr&B::MSR_EE)==0u&&
         !ipc70_bus.external_exception_pending(ctx.msr);
    const bool cache=addr==0x80522294u&&ctx.lr==0x80519124u;
    const bool context=addr==0x80522af4u||addr==0x805228ccu;
    std::cout<<"V390_NAND_POST_ACK guest="<<unsigned(guest)
             <<" clear="<<unsigned(clear)
             <<" registered="<<unsigned(registered)
             <<" masked="<<unsigned(masked)
             <<" cache="<<unsigned(cache)
             <<" context="<<unsigned(context)<<std::endl;
    check(guest&&clear&&registered&&masked,
          "V390 original NAND post-ACK guest successor not authenticated");
    v390_call_pc=addr;v390_call_lr=ctx.lr;
    ++v390_call_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
"""
TRIAL_PROOF=r"""  const bool v390_completed=v389_completed&&
       nwii::runtime::v390_call_seen==1u&&
       nwii::runtime::v390_call_pc!=0u&&
       c.pc==nwii::runtime::v390_call_pc&&
       c.lr==nwii::runtime::v390_call_lr;
  std::cout<<"V390_NAND_POST_ACK_TRIAL flag="<<unsigned(
                 nwii::runtime::v389_flag_seen==1u)
           <<" next="<<unsigned(nwii::runtime::v390_call_seen==1u)
           <<" completed="<<unsigned(v390_completed)<<std::endl;
  check(v390_completed,
        "V390 original NAND guest never left Hollywood ACK for next callee");"""

def patch(s:str)->str:
    if (s.count(HEAD)!=1 or s.count(STATE_OLD)!=1 or
        s.count(FLAG_STOP)!=1 or s.count(RESET)!=1 or
        s.count(PREV_TRIAL)!=1 or
        s.count("V389_NAND_FLAG_ACK before=")!=1 or
        s.count("V389_NAND_FLAG_TRIAL y1=")!=1 or
        s.count("V388_NAND_BOUNDARY kind=")!=2 or
        s.count("V385_NAND_ARMMSG_MIRROR coherent=")!=1 or
        MARKER in s or TRIAL in s or "v390_call_seen" in s):
        raise ValueError("V390 original guest post-Hollywood ACK source seam changed")
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(FLAG_STOP,FLAG_CONTINUE,1)
    out=out.replace(RESET,RESET+"\n"+
        "  nwii::runtime::v390_call_seen=0u;\n"+
        "  nwii::runtime::v390_flag_inst=0u;\n"+
        "  nwii::runtime::v390_call_pc=0u;\n"+
        "  nwii::runtime::v390_call_lr=0u;",1)
    out=out.replace(HEAD,HEAD+TRACE,1)
    out=out.replace(PREV_TRIAL,PREV_TRIAL+"\n"+TRIAL_PROOF,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL)!=1 or
        out.count(FLAG_CONTINUE)!=1 or FLAG_STOP in out or
        out.count("try{run_game(c);}")!=s.count("try{run_game(c);}") or
        out.count("V370_NAND_FLAG_W1C n=")!=1):
        raise ValueError("V390 original guest post-ACK observer not unique")
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("prior_private_harness",type=Path)
    p.add_argument("next_private_harness",type=Path)
    a=p.parse_args()
    try:
        if a.next_private_harness.exists() or a.next_private_harness.is_symlink():
            raise ValueError("output_exists")
        generated=patch(a.prior_private_harness.read_text(encoding="utf-8"))
        with a.next_private_harness.open("x",encoding="utf-8") as out:out.write(generated)
    except (ValueError,OSError):
        print("V390_NAND_POST_ACK_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V390_NAND_POST_ACK_ROUTE installed=1 original_guest=1 native_irq_down=1 no_synthetic_callback=1")
    return 0
if __name__=="__main__":raise SystemExit(main())
