#!/usr/bin/env python3
"""V385: scope V80's first-SYSCONF ARMMSG oracle after authenticated NAND Y1.

V384 entered original NAND IpcReplyHandler; V385's first execution of the
real PPC register-read helper hit V80's *old first reply* request-address
assertion. The later NAND ARMMSG address is not the old SC request.
Preserve the exact early-SC check/counter; on authenticated NAND only,
compare the original read result to the real native ARMMSG mailbox.

No MMIO interception, guest code/data change, IOS reply/ACK, invented
request or forced success. Require a strict unique inherited source seam.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

OLD='''       check(result&&*result==submit72_phys,"V80 original ARMMSG read selected a different request");
       ++wake80_armmsg;'''
MARKER='V385_NAND_ARMMSG_MIRROR coherent='
NEW='''       // V385: V80 is a first-SYSCONF request witness, not a NAND
       // request identity contract. Do not touch the guest MMIO reader.
       if(v250_candidate_mode&&v250_nand_seen==1u&&v384_read_seen==1u){
         using V385Bus=undercover::wii::IosBus;
         using V385Mail=undercover::wii::IpcMailbox;
         const auto v385_arm=ipc70_bus.read32(V385Bus::IPC+V385Mail::ARMMSG);
         const auto v385_ctrl=ipc70_bus.read32(V385Bus::IPC+V385Mail::PPCCTRL);
         const bool v385_coherent=result.has_value()&&v385_arm.has_value()&&
                                *result==*v385_arm;
         const bool v385_y1=v385_ctrl.has_value()&&
                  ((*v385_ctrl&V385Mail::Y1)!=0u)&&
                  ((*v385_ctrl&V385Mail::Y2)==0u);
         std::cout<<"V385_NAND_ARMMSG_MIRROR coherent="<<unsigned(v385_coherent)
                  <<" y1="<<unsigned(v385_y1)<<std::endl;
         check(v385_coherent&&v385_y1,
               "V385 original NAND ARMMSG read differs from live native mailbox");
       }else{
         check(result&&*result==submit72_phys,"V80 original ARMMSG read selected a different request");
         ++wake80_armmsg;
       }'''

def patch(source:str)->str:
    if (source.count(OLD)!=1 or
        source.count('V385_NAND_SECOND_READ caller=')!=1 or
        source.count('V384_NAND_REPLY_READ caller=')!=1 or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        source.count('v384_read_seen')<2 or
        source.count('ipc70_bus.read32(')<2 or
        MARKER in source):
        raise ValueError('V385 authenticated NAND ARMMSG/V80 source geometry changed')
    output=source.replace(OLD,NEW,1)
    if (output.count(MARKER)!=1 or
        output.count('V80 original ARMMSG read selected a different request')!=1 or
        output.replace(NEW,OLD,1)!=source):
        raise ValueError('V385 V80 first-request observer not exactly reversible')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_harness',type=Path)
    p.add_argument('next_private_harness',type=Path)
    args=p.parse_args()
    try:
        if args.next_private_harness.exists() or args.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        generated=patch(args.prior_private_harness.read_text(encoding='utf-8'))
        with args.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(generated)
    except (OSError,ValueError):
        print('V385_NAND_ARMMSG_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V385_NAND_ARMMSG_ROUTE installed=1 original_guest=1 first_sc_preserved=1 live_mailbox=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
