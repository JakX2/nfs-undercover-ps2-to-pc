#!/usr/bin/env python3
"""V260 candidate-only original PPCMSG boundary after verified NAND IPC entry.

Continue genuine translated guest execution from the V259 entry PC 8051906C
and observe the first actual original MMIO PPCMSG store call. Capture the
physical request header and CPU state BEFORE forwarding the write, then stop
the test. No IOS submission, reply, register, packet or game-code fabrication.
"""
import argparse
from pathlib import Path
from derive_v259_ipc_reentry_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

V259_STOP='''    ctx.is_running=false;throw ExceptionStop{};
  }'''
V259_CONTINUE='''    return; // V260: execute genuine 0x8051906C guest body after entry
  }'''
WRITE_ANCHOR='''void HW_Reg_Write32(uint32_t addr,uint32_t value){'''
WRITE_OBSERVER='''void HW_Reg_Write32(uint32_t addr,uint32_t value){
  // First authentic PPCMSG after restored NAND -> IPC helper.
  // Observe before any hardware publication; this is NOT a sent request.
  using V260Bus=undercover::wii::IosBus;
  using V260Mail=undercover::wii::IpcMailbox;
  const bool ppcmsg=addr==V260Bus::IPC+V260Mail::PPCMSG||
                    addr==V260Bus::MIRROR+V260Mail::PPCMSG;
  if(v250_candidate_mode&&v259_ipc_seen==1u&&v260_msg_seen==0u&&ppcmsg){
    CPUContext* cpu=ipc70_ram.cpu;
    const bool guest=cpu!=nullptr&&
          cpu->inst_count>v259_ipc_inst&&
          cpu->pc>=0x80000000u&&cpu->pc<0x80600000u&&
          cpu->gpr[13]==v147_first_r13;
    const bool aligned=value!=0u&&(value&31u)==0u;
    const bool mapped=aligned&&ipc70_ram.valid(value,64u);
    const uint32_t command=mapped?ipc70_ram.read32(value):0u;
    const uint32_t path=mapped?ipc70_ram.read32(value+12u):0u;
    const uint32_t mode=mapped?ipc70_ram.read32(value+16u):0u;
    const bool fresh=value!=v153_phys&&v153_phys!=0u;
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply;
    const bool open=command==undercover::wii::StmIos::Open;
    const bool mem2=value>=0x10000000u&&value<0x14000000u;
    const bool path_phys=path!=0u&&ipc70_ram.valid(path,1u);
    const bool path_alias=path!=0u&&ipc70_ram.valid(path&0x3fffffffu,1u);
    const bool mode_ok=mode<=3u;
    const auto ctrl=ipc70_bus.read32(V260Bus::IPC+V260Mail::PPCCTRL);
    const bool idle=ctrl.has_value()&&
          ((*ctrl&(V260Mail::X1|V260Mail::Y1|V260Mail::Y2))==0u);
    const bool coherent=guest&&
          ipc70_bus.external_exception_pending(cpu->msr)==
          (((cpu->msr&V260Bus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    std::cout<<"V260_PPCMSG_BOUNDARY guest="<<guest
             <<" aligned="<<aligned<<" mapped="<<mapped
             <<" fresh="<<fresh<<" coherent="<<coherent
             <<" reply="<<reply<<" open="<<open<<" mem2="<<mem2
             <<" mode_ok="<<mode_ok<<" path_phys="<<path_phys
             <<" path_alias="<<path_alias<<" idle="<<idle
             <<" prewrite=1"<<std::endl;
    check(guest&&aligned&&mapped&&fresh&&coherent,
          "V260 authentic post-NAND PPCMSG ABI, RAM or IRQ invalid");
    v260_msg_phys=value;
    v260_msg_cmd=command;
    v260_guest_pc=cpu->pc;
    v260_guest_lr=cpu->lr;
    v260_guest_inst=cpu->inst_count;
    ++v260_msg_seen;
    cpu->is_running=false;throw ExceptionStop{};
  }
'''
CANDIDATE='''      if(v250_probe&&nwii::runtime::v260_msg_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&
              nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v254_next_seen==1u&&
              nwii::runtime::v256_return_seen==1u&&
              nwii::runtime::v257_next_seen==1u&&
              nwii::runtime::v259_ipc_seen==1u;
        const bool mmio=!c.is_running&&
              c.pc==nwii::runtime::v260_guest_pc&&
              c.lr==nwii::runtime::v260_guest_lr&&
              c.inst_count==nwii::runtime::v260_guest_inst&&
              c.inst_count>nwii::runtime::v259_ipc_inst;
        const bool memory=nwii::runtime::ipc70_ram.valid(
                  nwii::runtime::v260_msg_phys,64u)&&
              nwii::runtime::ipc70_ram.read32(
                  nwii::runtime::v260_msg_phys)==nwii::runtime::v260_msg_cmd&&
              c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v259_ipc_sc;
        std::cout<<"V260_NAND_GUEST callback="<<callback
                 <<" mmio="<<mmio<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&mmio&&memory,
              "V260 authentic PPCMSG boundary did not persist in guest context");
        continue; // private candidate only; original V244 path unaffected
      }'''

def derive(source:str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(V259_STOP)!=1 or
            s.count(PREVIOUS_OBSERVER)!=1 or
            s.count(PREVIOUS_CANDIDATE)!=1 or
            s.count(WRITE_ANCHOR)!=1):
        raise ValueError("V260 inherited original NAND/IPC source anchors changed")
    s=once(s,STATE,STATE+'''
 static unsigned v260_msg_seen=0u;
 static uint32_t v260_msg_phys=0u,v260_msg_cmd=0u;
 static uint32_t v260_guest_pc=0u,v260_guest_lr=0u;
 static uint64_t v260_guest_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v260_msg_seen=0u;
     nwii::runtime::v260_msg_phys=nwii::runtime::v260_msg_cmd=0u;
     nwii::runtime::v260_guest_pc=nwii::runtime::v260_guest_lr=0u;
     nwii::runtime::v260_guest_inst=0u;''')
    s=once(s,PREVIOUS_OBSERVER,
           PREVIOUS_OBSERVER.replace(V259_STOP,V259_CONTINUE,1))
    s=once(s,WRITE_ANCHOR,WRITE_OBSERVER)
    s=once(s,PREVIOUS_CANDIDATE,CANDIDATE)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
