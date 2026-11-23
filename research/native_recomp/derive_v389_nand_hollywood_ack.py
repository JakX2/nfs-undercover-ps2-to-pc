#!/usr/bin/env python3
"""V389: original Wii NAND Hollywood PPC_FLAG W1C after genuine Y1 ACK.

V388 owner-original proved the original guest cleared Broadway PPCCTRL.Y1
while Hollywood IPC_PPC remained asserted. Keep that verified V388 MMIO
observer but DO NOT stop there; allow unchanged guest PPC instructions to
execute their own distinct Hollywood flag W1C through the existing V370
native bus. Stop immediately after authentic host-observed original write.
No synthetic IOS result, flag write, guest PC, or NAND callback.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from derive_v370_nand_ipc_flag_w1c import INJECTION as V370_FLAG
from derive_v388_nand_bounded_trace import ACK as V388_ACK

STATE_OLD="static bool v388_active=false;"
STATE_NEW="""static bool v388_active=false;
static bool v389_after_y1=false;
static unsigned v389_flag_seen=0u;
static uint64_t v389_y1_inst=0u;"""
Y1_END="""        v388_kind=1u;
        ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
      }"""
Y1_CONTINUE="""        v388_kind=1u;
        v389_after_y1=true;
        v389_y1_inst=ipc70_ram.cpu->inst_count;
        // Continue unchanged original PowerPC to its independent flag W1C.
      }"""
RESET="nwii::runtime::v388_start_inst=c.inst_count;"
V388_TRIAL="""  check(v388_completed,
        "V388 original NAND bounded guest call chain yielded no verified stop");"""
FLAG_END="""      mmio_writes.emplace_back(addr,value);
      return;"""
MARKER="V389_NAND_FLAG_ACK before="
TRIAL="V389_NAND_FLAG_TRIAL y1="
FLAG_PROOF=r"""      mmio_writes.emplace_back(addr,value);
      // V389 is never active during early NAND boot/first Hollywood ACK.
      // At this stage Y1 was cleared by the authentic original guest writer.
      if(v388_active&&v389_after_y1&&v389_flag_seen==0u){
        using M=undercover::wii::IpcMailbox;
        const auto control=ipc70_bus.read32(B::IPC+M::PPCCTRL);
        const bool y1clear=control.has_value()&&
             ((*control&(M::Y1|M::Y2))==0u);
        const bool wrote=(value&H::IPC_PPC)!=0u;
        const bool cleared=!remaining;
        const bool down=!ipc70_bus.external_irq_level();
        const bool registered=ipc70_ram.cpu!=nullptr&&
             ipc70_ram.cpu->mmu.get_ptr(IRQ_TABLE+27u*4u)!=nullptr&&
             ipc70_ram.cpu->mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u;
        const bool guest=ipc70_ram.cpu!=nullptr&&
             (ipc70_ram.cpu->msr&B::MSR_EE)==0u&&
             ipc70_ram.cpu->inst_count>v389_y1_inst;
        const bool verified=before&&wrote&&cleared&&down&&
             y1clear&&registered&&guest;
        std::cout<<"V389_NAND_FLAG_ACK before="<<unsigned(before)
                 <<" wrote="<<unsigned(wrote)
                 <<" cleared="<<unsigned(cleared)
                 <<" down="<<unsigned(down)
                 <<" y1="<<unsigned(y1clear)
                 <<" guest="<<unsigned(guest)
                 <<" registered="<<unsigned(registered)
                 <<std::endl;
        check(verified,
              "V389 original NAND PPC_FLAG guest W1C failed distinct ACK proof");
        ++v389_flag_seen;
        ipc70_ram.cpu->is_running=false;throw ExceptionStop{};
      }
      return;"""
TRIAL_PROOF=r"""  const auto v389_ctrl=nwii::runtime::ipc70_bus.read32(
       undercover::wii::IosBus::IPC+undercover::wii::IpcMailbox::PPCCTRL);
  const auto v389_flag=nwii::runtime::ipc70_bus.read32(
       undercover::wii::IosBus::IPC+undercover::wii::HollywoodIrq::PPC_FLAG);
  const bool v389_completed=v388_completed&&
       nwii::runtime::v389_flag_seen==1u&&
       nwii::runtime::v389_after_y1&&
       nwii::runtime::v388_kind==1u&&
       v389_ctrl.has_value()&&v389_flag.has_value()&&
       ((*v389_ctrl&(undercover::wii::IpcMailbox::Y1|
                     undercover::wii::IpcMailbox::Y2))==0u)&&
       ((*v389_flag&undercover::wii::HollywoodIrq::IPC_PPC)==0u)&&
       !nwii::runtime::ipc70_bus.external_irq_level();
  std::cout<<"V389_NAND_FLAG_TRIAL y1="<<unsigned(
                nwii::runtime::v388_kind==1u)
           <<" flag="<<unsigned(nwii::runtime::v389_flag_seen==1u)
           <<" completed="<<unsigned(v389_completed)<<std::endl;
  check(v389_completed,
        "V389 original NAND Hollywood flag ACK did not release native IRQ");
"""

def patch(s:str)->str:
    if (s.count(STATE_OLD)!=1 or s.count(V388_ACK)!=1 or
        s.count(V370_FLAG)!=1 or s.count(RESET)!=1 or
        s.count(V388_TRIAL)!=1 or
        s.count('V388_NAND_BOUNDARY kind=')!=2 or
        s.count('V388_NAND_BOUNDED_TRIAL kind=')!=1 or
        s.count('V387_NAND_ROUTE_EVENT kind=')!=2 or
        s.count('V385_NAND_ARMMSG_MIRROR coherent=')!=1 or
        MARKER in s or TRIAL in s or "v389_after_y1" in s):
        raise ValueError("V389 authentic V370/V388 guest-W1C seam changed")
    if V388_ACK.count(Y1_END)!=1 or V370_FLAG.count(FLAG_END)!=1:
        raise ValueError("V389 original PowerPC hardware observer geometry changed")
    continuing=V388_ACK.replace(Y1_END,Y1_CONTINUE,1)
    flag=V370_FLAG.replace(FLAG_END,FLAG_PROOF,1)
    out=s.replace(STATE_OLD,STATE_NEW,1)
    out=out.replace(V388_ACK,continuing,1)
    out=out.replace(V370_FLAG,flag,1)
    out=out.replace(
        RESET,RESET+"\n"+
        "  nwii::runtime::v389_after_y1=false;\n"+
        "  nwii::runtime::v389_flag_seen=0u;\n"+
        "  nwii::runtime::v389_y1_inst=0u;",1
    )
    out=out.replace(V388_TRIAL,V388_TRIAL+"\n"+TRIAL_PROOF,1)
    if (out.count(MARKER)!=1 or out.count(TRIAL)!=1 or
        out.count('V388_NAND_BOUNDARY kind=')!=2 or
        out.count('V370_NAND_FLAG_W1C n=')!=1 or
        out.count('try{run_game(c);}')!=s.count('try{run_game(c);}') or
        Y1_END in out):
        raise ValueError("V389 original Hollywood ACK observer not uniquely installed")
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
    except (OSError,ValueError):
        print("V389_NAND_FLAG_ROUTE installed=0",file=sys.stderr)
        return 1
    print("V389_NAND_FLAG_ROUTE installed=1 original_guest=1 separate_w1c=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
