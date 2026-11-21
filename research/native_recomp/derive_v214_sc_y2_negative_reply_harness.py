#!/usr/bin/env python3
"""V214 verify the second original IOS_Open's genuine negative reply.

V208 proved the second authenticated SYSCONF IOS_Open has invalid mode
bytes in the original physical MEM2 request. The native IOS service
correctly returns -4 rather than opening a fabricated handle. This
independent phase proves real native reply publication, Y1/IRQ, and
CPU/SC invariance while retaining the true negative result.
"""
import argparse
from pathlib import Path
from derive_v208_sc_y2_reply_publication_harness import (
    derive as previous, PUBLISH as PREVIOUS_PUBLISH,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    check(opened,"V208 second IOS opened file descriptor kind differs");'''
VERIFY='''    // A genuine negative IOS_Open reply is a completed transport event,
    // not a successful device/file open. Never synthesize a descriptor.
    const bool invalid_fd=int32_t(fd)==S::Invalid&&!opened&&
          !(immediate||event||fs||file||es);
    const bool bad_mode=ipc70_ram.read32(req+16u)>3u;
    const bool nonzero_path=ipc70_ram.read32(req+12u)!=0u;
    const bool publication=step&&wire&&signal&&drained&&cpu&&sc_before;
    std::cout<<"V214_Y2_NEGATIVE invalid="<<invalid_fd
             <<" mode="<<bad_mode<<" path="<<nonzero_path
             <<" published="<<publication<<" irq="<<signal
             <<" drained="<<drained<<" cpu="<<cpu<<" sc="<<sc_before
             <<std::endl;
    check(invalid_fd&&bad_mode&&nonzero_path&&publication,
          "V214 original second IOS_Open negative reply was not faithfully published");
    ++v214_negative_seen;'''
NEXT_END='''      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            nwii::runtime::v208_reply_seen==1u&&
            nwii::runtime::v214_negative_seen==1u&&
            done&&!c.is_running&&c.pc==0x80529434u&&
            c.lr==0x80526cb0u&&
            c.mmu.read8(c.gpr[13]-3176u)==1u,
            "V214 authentic negative IOS reply publication checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_PUBLISH.count(STOP)!=1 or PREVIOUS_END.count(
        "nwii::runtime::v208_reply_seen==1u&&")!=1:
        raise ValueError("V214 inherited V208 reply publication contract changed")
    s=once(s,STATE,STATE+'''
 static unsigned v214_negative_seen=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v214_negative_seen=0u;''')
    s=once(s,STOP,VERIFY)
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
