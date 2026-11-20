#!/usr/bin/env python3
"""V137 observe native IOS mailbox liveness at the third original SC call."""
from pathlib import Path
import argparse
from derive_v136_second_retry_harness import derive as previous
OLD='''     std::cout<<"V136_SECOND_PASS pc="'''
NEW='''     using V137Bus=undercover::wii::IosBus;
     using V137Mail=undercover::wii::IpcMailbox;
     const auto v137_ctrl=ipc70_bus.read32(V137Bus::IPC+V137Mail::PPCCTRL);
     const bool v137_x1=v137_ctrl.has_value()&&((*v137_ctrl&V137Mail::X1)!=0u);
     const unsigned v137_queued=ipc70_bus.services().queued_replies();
     const bool v137_event=ipc70_bus.services().event_pending();
     const bool v137_irq=ipc70_bus.external_irq_level();
     const bool v137_ee=(ctx.msr&V137Bus::MSR_EE)!=0u;
     std::cout<<"V137_IOS_LIVENESS x1="<<v137_x1
              <<" queued="<<v137_queued<<" event="<<v137_event
              <<" irq="<<v137_irq<<" ee="<<v137_ee<<std::endl;
     std::cout<<"V136_SECOND_PASS pc="'''
def derive(source):
    s=previous(source)
    if s.count(OLD)!=1:raise ValueError("V137 IOS observation anchor differs")
    return s.replace(OLD,NEW,1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
