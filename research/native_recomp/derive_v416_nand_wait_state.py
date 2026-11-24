#!/usr/bin/env python3
"""Add read-only hardware and timebase evidence to the V414 resumed trace."""
from __future__ import annotations
import argparse
from pathlib import Path
from derive_v414_nand_resumed_coverage import TRACE

STATE=r'''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      const auto ctrl=ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      const auto msg=ipc70_bus.read32(B::IPC+M::PPCMSG);
      const bool mapped=msg.has_value()&&*msg!=0u&&(*msg&31u)==0u&&ipc70_ram.valid(*msg,64u);
      const bool reply=mapped&&ipc70_ram.read32(*msg)==undercover::wii::StmIos::Reply;
      const bool negative=reply&&(ipc70_ram.read32(*msg+4u)&0x80000000u)!=0u;
      std::cout<<"V416_WAIT_STATE call="<<v396_calls
               <<" lr="<<std::hex<<ctx.lr<<std::dec
               <<" inst="<<ctx.inst_count<<" tb="<<ctx.read_timebase()
               <<" mapped="<<unsigned(mapped)<<" reply="<<unsigned(reply)
               <<" negative="<<unsigned(negative)
               <<" pending="<<unsigned(ipc70_bus.pending_native_ios_request())
               <<" queued="<<unsigned(ipc70_bus.services().queued_replies()>0u)
               <<" irq="<<unsigned(ipc70_bus.external_irq_level())
               <<" ee="<<unsigned((ctx.msr&B::MSR_EE)!=0u)
               <<" eligible="<<unsigned(ipc70_bus.external_exception_pending(ctx.msr))
               <<" x1="<<unsigned(ctrl.has_value()&&((*ctrl&M::X1)!=0u))
               <<" y1="<<unsigned(ctrl.has_value()&&((*ctrl&M::Y1)!=0u))
               <<" y2="<<unsigned(ctrl.has_value()&&((*ctrl&M::Y2)!=0u))
               <<" flag="<<unsigned(flag.has_value()&&((*flag&H::IPC_PPC)!=0u))
               <<" expired="<<unsigned(ctx.dec_expired())<<std::endl;'''
NEW=TRACE[:-len('    }')]+STATE+'\n    }'

def patch(source:str)->str:
    if source.count(TRACE)!=1 or source.count('V414_RESUMED_BEGIN after=')!=1 or 'V416_WAIT_STATE' in source:
        raise ValueError('geometry')
    out=source.replace(TRACE,NEW,1)
    if out.replace(NEW,TRACE,1)!=source:raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    try:
        out=patch(a.prior.read_text(encoding='utf-8'))
        with a.output.open('x',encoding='utf-8') as f:f.write(out)
    except (ValueError,OSError):
        print('V416_WAIT_ROUTE installed=0');return 1
    print('V416_WAIT_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
