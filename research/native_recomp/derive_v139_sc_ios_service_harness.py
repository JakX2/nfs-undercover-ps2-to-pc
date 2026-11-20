#!/usr/bin/env python3
"""V139 acknowledge original Wii SYSCONF IOS_Open using a real native service step.

Owner-original guest code and request bytes are unchanged. The only new host
behavior is an explicit read-only synthetic SYSCONF mount and one IOS service
step when the already-submitted original guest request reaches the wait loop.
The reply is queued; no fake return, forced status, or automatic IRQ dispatch.
"""
import argparse
from pathlib import Path
from derive_v138_ios_request_harness import derive as previous

ANCHOR = '     std::cout<<"V137_IOS_LIVENESS x1="'
ADDITION = '''     const bool v139_request=v138_valid&&v138_cmd==V138Ios::Open&&
           v138_kind==4u&&v138_mode==1u;
     check(v139_request,"V139 original SC request is not SYSCONF read-only open");
     auto v139_files=std::make_shared<undercover::wii::GuestFiles>();
     const bool v139_generated=undercover::wii::SysconfImage::add_to(*v139_files);
     const bool v139_mounted=v139_generated&&
           ipc70_bus.services().mount_filesystem(v139_files);
     check(v139_mounted,"V139 native IOS could not mount test SYSCONF before request");
     undercover::wii::IosYieldScheduler v139_scheduler(ipc70_bus);
     const auto v139_state=v139_scheduler.service_one(ctx.msr);
     const bool v139_ack=v139_state.progress==undercover::wii::StmIos::Pump::Ack;
     const bool v139_queued=ipc70_bus.services().queued_replies()==1u;
     bool v139_fd=false;
     for(unsigned fd=0u;fd<undercover::wii::StmIos::DescriptorCount;++fd)
       v139_fd|=ipc70_bus.services().is_open(fd,undercover::wii::StmIos::Device::File);
     std::cout<<"V139_SC_IOS_ACK mount="<<v139_mounted
              <<" request="<<v139_request<<" ack="<<v139_ack
              <<" queued="<<v139_queued<<" irq="<<v139_state.guest_exception_ready
              <<" fd="<<v139_fd<<std::endl;
     check(v139_ack&&v139_queued&&v139_state.guest_exception_ready&&v139_fd,
           "V139 original pending SC request was not authentically ACKed by native IOS");
     std::cout<<"V137_IOS_LIVENESS x1="'''


def derive(source: str) -> str:
    s=previous(source)
    if s.count(ANCHOR)!=1:
        raise ValueError("V139 request classification/IOS observer anchor changed")
    s=s.replace(ANCHOR,ADDITION,1)
    return ('#include "wii_sysconf_image.h"\n'
            '#include "wii_ios_yield_scheduler.h"\n' + s)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
