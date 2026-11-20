#!/usr/bin/env python3
"""V138 classify the pending original Wii IOS request at the SC retry boundary.

This reads only a validated guest physical request and classifies paths.
Never logs owner paths, original executable bytes or mutates IOS/guest state.
"""
import argparse
from pathlib import Path
from derive_v137_ios_liveness_harness import derive as previous

ANCHOR = '     std::cout<<"V137_IOS_LIVENESS x1="'
INJECTION = '''     using V138Bus=undercover::wii::IosBus;
     using V138Mail=undercover::wii::IpcMailbox;
     using V138Ios=undercover::wii::StmIos;
     const auto v138_msg=ipc70_bus.read32(V138Bus::IPC+V138Mail::PPCMSG);
     const bool v138_valid=v138_msg.has_value()&&*v138_msg!=0u&&
           !(*v138_msg&31u)&&ipc70_ram.valid(*v138_msg,64u);
     const uint32_t v138_cmd=v138_valid?ipc70_ram.read32(*v138_msg):0u;
     const uint32_t v138_mode=(v138_valid&&v138_cmd==V138Ios::Open)?
           ipc70_ram.read32(*v138_msg+16u):255u;
     unsigned v138_kind=0u; // 0:not-open; 7:unsupported/unreadable pathname
     if(v138_valid&&v138_cmd==V138Ios::Open){
       const uint32_t ptr=ipc70_ram.read32(*v138_msg+12u);
       std::string name;bool terminated=false;
       for(unsigned index=0;index<64u;++index){
         if(ptr>0xffffffffu-index||!ipc70_ram.valid(ptr+index,1u))break;
         const char ch=char(ipc70_ram.read8(ptr+index));
         if(ch==0){terminated=true;break;}
         name.push_back(ch);
       }
       if(!terminated)v138_kind=7u;
       else if(name=="/dev/stm/immediate")v138_kind=1u;
       else if(name=="/dev/stm/eventhook")v138_kind=2u;
       else if(name=="/dev/fs")v138_kind=3u;
       else if(name=="/shared2/sys/SYSCONF")v138_kind=4u;
       else if(name=="/dev/es")v138_kind=5u;
       else v138_kind=6u;
     }
     std::cout<<"V138_IOS_REQUEST valid="<<v138_valid
              <<" command="<<v138_cmd<<" path_kind="<<v138_kind
              <<" mode="<<v138_mode<<std::endl;
     std::cout<<"V137_IOS_LIVENESS x1="'''


def derive(source: str) -> str:
    s = previous(source)
    if s.count(ANCHOR) != 1:
        raise ValueError("V138 original-free request observer anchor changed")
    return s.replace(ANCHOR, INJECTION, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as output:
        output.write(derive(args.source.read_text(encoding="utf-8")))
