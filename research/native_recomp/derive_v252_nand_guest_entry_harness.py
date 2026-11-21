#!/usr/bin/env python3
"""V252: isolated 16-trial original Wii NAND bctrl-entry execution proof.

V250 owner-native reached the authentic restored callback bctrl with
matching frame16/CTR/LR/ABI in each trial, but the old V178 callee
assertion (for the *reduced* callback fixture) stopped further progress.
For the new private owner-callback mode only, stop at this precise and
previously verified *original* NAND function entry, then prove all
sixteen independent guest trials. The historical V244 baseline mode
is unchanged, still executed independently earlier in the owner runner.
No guest register, DOL byte, native IOS response or callback is patched.
"""
import argparse
from pathlib import Path
from derive_v250_restored_callback_nand_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    POST as PREVIOUS_POST,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

FALLTHROUGH='''    ++v250_nand_seen;
    // Fall through to the existing original-free IRQ/callback tracers.'''
BOUNDED_STOP='''    ++v250_nand_seen;
    ++v252_nand_entry_seen;
    // Isolated owner-callback check only. This execution is allowed to
    // stop before V178's historical reduced-callback next-call assertion.
    // The original NAND callee body is NOT claimed to have executed yet.
    ctx.is_running=false;throw ExceptionStop{};'''
VERIFY='''      check(exception_stop,"exception initialization did not reach exact test-only syscall");
      if(v250_probe&&nwii::runtime::v252_nand_entry_seen==1u){
        const bool checkpoint=nwii::runtime::v250_candidate_mode&&nwii::runtime::v250_cb_seen==1u&&
              nwii::runtime::v250_nand_seen==1u&&nwii::runtime::v252_nand_entry_seen==1u&&
              nwii::runtime::v244_cb_seen==1u&&nwii::runtime::v244_cb_registered&&nwii::runtime::v244_cb_abi&&
              nwii::runtime::v244_nested_target==0x8051e06cu;
        const bool regs=c.pc==0x8051e06cu&&c.lr==0x804f0f54u&&
              c.ctr==0x8051e06cu&&!c.is_running&&
              nwii::runtime::v250_initial_sp>=c.gpr[1]&&
              nwii::runtime::v250_initial_sp-c.gpr[1]==16u&&
              c.inst_count>nwii::runtime::v250_initial_inst;
        const bool real_reply=nwii::runtime::v153_phys!=0u&&
              nwii::runtime::ipc70_ram.valid(nwii::runtime::v153_phys,64u)&&
              nwii::runtime::ipc70_ram.read32(nwii::runtime::v153_phys)==undercover::wii::StmIos::Reply;
        const bool before_second=nwii::runtime::v183_second_phys==0u;
        const bool result=checkpoint&&regs&&real_reply&&before_second;
        std::cout<<"V252_NAND_GUEST checked="<<checkpoint
                 <<" regs="<<regs<<" reply="<<real_reply
                 <<" before_second="<<before_second
                 <<" trial="<<(trial+1u)<<std::endl;
        check(result,"V252 genuine NAND bctrl entry or guest ABI differs");
        continue; // candidate-only isolated proof; never weaken V244 owner baseline
      }'''
def derive(source:str)->str:
    s=previous(source)
    if (PREVIOUS_OBSERVER.count(FALLTHROUGH)!=1 or
            s.count(PREVIOUS_POST)!=1 or
            s.count('const bool owner=v250_probe||std::string(argv[2])=="owner";')!=1):
        raise ValueError("V252 authenticated owner-callback/old V178 phase seam changed")
    s=once(s,STATE,STATE+'''
 static unsigned v252_nand_entry_seen=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v252_nand_entry_seen=0u;''')
    s=once(s,FALLTHROUGH,BOUNDED_STOP)
    s=once(s,PREVIOUS_POST,VERIFY)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
