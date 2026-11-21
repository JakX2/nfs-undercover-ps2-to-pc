#!/usr/bin/env python3
"""V254: execute original Wii restored NAND callback into next AOT call.

V250 owner observed genuine _isfsFuncCb bctrl into nandOpenCallback with
correct 16-byte frame, LR/CTR and userdata. V252 isolates the initial
guest entry. V254 resumes the original native NAND body and captures
its first actual translated PowerPC child call. The historical V178
callee expectation is scoped ONLY for this authenticated candidate
NAND entry; baseline V244 and all other V178 paths remain untouched.
No synthetic guest register/memory modification or success reply.
"""
import argparse
from pathlib import Path
from derive_v252_nand_guest_entry_harness import (
    derive as previous, BOUNDED_STOP as PREVIOUS_STOP,
    CANDIDATE as PREVIOUS_CANDIDATE,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

V178_CALLEE='''    check(addr==0x80545100u&&ctx.lr==0x804f1e40u,
          "V178 owner-original SC reply callee differs from V177 proof");'''
V178_SCOPED='''    // The restored, authenticated callback really enters NAND first.
    // The earlier reduced fixture reaches 0x80545100 directly. Preserve
    // that historical guard except for this one verified NAND bctrl.
    if(v250_candidate_mode&&v252_nand_entry_seen==1u&&
       addr==0x8051e06cu&&ctx.lr==0x804f0f54u)
      return;
    check(addr==0x80545100u&&ctx.lr==0x804f1e40u,
          "V178 owner-original SC reply callee differs from V177 proof");'''
NAND_RESUME='''    ++v250_nand_seen;
    ++v252_nand_entry_seen;
    v254_nand_inst=ctx.inst_count;
    // Original translated NAND function begins immediately after return.
    // Its body is never patched or replaced by a host callback.'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
OBSERVER='''void trace_call(uint32_t addr, CPUContext&ctx){
  if(v250_candidate_mode&&v252_nand_entry_seen==1u&&
     v254_next_seen==0u&&ctx.pc==addr&&addr!=0x8051e06cu&&
     addr>=0x80000000u&&addr<0x80600000u){
    using VI=undercover::wii::StmIos;
    const bool guest=ctx.inst_count>v254_nand_inst&&
          ctx.gpr[13]==v147_first_r13;
    const bool caller=ctx.lr>=0x80400000u&&ctx.lr<0x80600000u&&
          !(ctx.lr&3u)&&!(addr&3u);
    const bool reply=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u)&&
          ipc70_ram.read32(v153_phys)==VI::Reply;
    const uint32_t scaddr=ctx.gpr[13]-3176u;
    const bool mapped=ctx.mmu.get_ptr(scaddr)!=nullptr;
    const uint32_t sc=mapped?ctx.mmu.read8(scaddr):0u;
    const bool frame=v250_initial_sp>=ctx.gpr[1]&&
          v250_initial_sp-ctx.gpr[1]>=16u;
    const bool coherent=ipc70_bus.external_exception_pending(ctx.msr)==
          (((ctx.msr&undercover::wii::IosBus::MSR_EE)!=0u)&&
           ipc70_bus.external_irq_level());
    const bool text=addr>=0x80400000u;
    const bool low=addr<0x80400000u;
    std::cout<<"V254_NAND_CHILD guest="<<guest
             <<" caller="<<caller<<" reply="<<reply
             <<" mapped="<<mapped<<" frame="<<frame
             <<" coherent="<<coherent<<" text="<<text
             <<" low="<<low<<" sc="<<sc
             <<" pc="<<std::hex<<addr<<" lr="<<ctx.lr
             <<std::dec<<std::endl;
    check(guest&&caller&&reply&&mapped&&frame&&coherent,
          "V254 original NAND callback body did not reach genuine native child");
    v254_next_pc=addr;v254_next_lr=ctx.lr;
    v254_final_sc=sc;
    ++v254_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }
'''
VERIFY='''      check(exception_stop,"exception initialization did not reach exact test-only syscall");
      if(v250_probe&&nwii::runtime::v254_next_seen==1u){
        const bool callback=nwii::runtime::v250_candidate_mode&&
              nwii::runtime::v244_cb_seen==1u&&
              nwii::runtime::v244_cb_registered&&nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu&&
              nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&
              nwii::runtime::v252_nand_entry_seen==1u;
        const bool guest=nwii::runtime::v254_next_seen==1u&&
              c.pc==nwii::runtime::v254_next_pc&&
              c.lr==nwii::runtime::v254_next_lr&&
              c.inst_count>nwii::runtime::v254_nand_inst&&
              !c.is_running;
        const bool memory=c.mmu.get_ptr(c.gpr[13]-3176u)!=nullptr&&
              c.mmu.read8(c.gpr[13]-3176u)==nwii::runtime::v254_final_sc;
        std::cout<<"V254_NAND_GUEST callback="<<callback
                 <<" next="<<guest<<" memory="<<memory
                 <<" trial="<<(trial+1u)<<std::endl;
        check(callback&&guest&&memory,
              "V254 restored original NAND child call did not persist");
        continue; // only the independent owner-callback mode, not V244 owner
      }'''
CANDIDATE=VERIFY.split('''      check(exception_stop,"exception initialization did not reach exact test-only syscall");\n''',1)[1]

def derive(source:str)->str:
    s=previous(source)
    if (s.count(PREVIOUS_STOP)!=1 or
            s.count(PREVIOUS_CANDIDATE)!=1 or
            s.count(V178_CALLEE)!=1 or
            s.count(TRACE_ANCHOR)!=1):
        raise ValueError("V254 callback and legacy callee source anchors changed")
    s=once(s,STATE,STATE+'''
 static unsigned v254_next_seen=0u;
 static uint64_t v254_nand_inst=0u;
 static uint32_t v254_next_pc=0u,v254_next_lr=0u,v254_final_sc=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v254_next_seen=0u;
     nwii::runtime::v254_nand_inst=0u;
     nwii::runtime::v254_next_pc=nwii::runtime::v254_next_lr=
         nwii::runtime::v254_final_sc=0u;''')
    s=once(s,PREVIOUS_STOP,NAND_RESUME)
    s=once(s,V178_CALLEE,V178_SCOPED)
    s=once(s,TRACE_ANCHOR,OBSERVER)
    # Replace only the candidate-specific V163 final shortcut. The
    # preceding game-executed V163 assertion still runs in baseline owner.
    s=once(s,PREVIOUS_CANDIDATE,CANDIDATE)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
