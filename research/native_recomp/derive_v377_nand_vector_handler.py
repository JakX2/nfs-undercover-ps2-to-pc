#!/usr/bin/env python3
"""V377: resume original installed NAND Y1 vector after genuine V376 entry.

V376 owner-original entered the installed 0x80000500 PowerPC exception vector
and verified saved SRRs and GPR/LR/CTR/XER, but a historical V160 first-SC
test assertion then aborted. In the already-authenticated NAND candidate
only, preserve that assertion for its original SC lane and execute the
translated original Wii vector until actual 0x80526CE0 handler entry.

No fake PowerPC handler, guest branch, reply, IRQ ACK or forced return code.
Stop before the original handler body to inspect its saved guest ABI.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

HEAD="void trace_call(uint32_t addr, CPUContext&ctx){"
V376='V376_NAND_VECTOR n='
V375='V375_NAND_Y1_BOUNDARY n='
V160='V160 did not execute original SC Y1 exception vector to handler'
MARKER='V377_NAND_HANDLER_ENTRY vector='
VECTOR='V377_NAND_VECTOR_ENTRY saved='
TRIAL='V377_NAND_HANDLER_TRIAL stopped='
REQUIRED=('v160_vector_seen','v160_handler_seen','v159_vector_seen',
          'v158_rfi_seen','c.pc==0x80526ce0u')

STATE=r"""
// V377: observer-only phase gate and immutable interrupted CPU snapshot.
// Reset for each NAND owner candidate; the first-SC path is unchanged.
static bool v377_live=false;
static unsigned v377_vector_seen=0u,v377_handler_seen=0u;
static uint32_t v377_resume=0u,v377_srr1=0u,v377_irq_msr=0u;
static uint32_t v377_lr=0u,v377_ctr=0u,v377_xer=0u;
static uint64_t v377_start_inst=0u;
static std::array<uint32_t,32> v377_gprs{};
"""

TRACE=r"""
  // V377 executes only the original vector/handler native AOT functions.
  if(v377_live&&v377_handler_seen==0u){
    if(addr==undercover::wii::ExternalVector){
      bool bytes=true;
      for(size_t i=0u;i<irq74_vector.size();++i){
        const uint32_t at=undercover::wii::ExternalVector+uint32_t(i);
        bytes=bytes&&ctx.mmu.get_ptr(at)!=nullptr&&
              ctx.mmu.read8(at)==irq74_vector[i];
      }
      const bool saved=ctx.pc==addr&&ctx.srr0==v377_resume&&
                       ctx.srr1==v377_srr1&&ctx.msr==v377_irq_msr;
      const bool regs=ctx.gpr==v377_gprs&&ctx.lr==v377_lr&&
                      ctx.ctr==v377_ctr&&ctx.xer==v377_xer;
      const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u;
      const bool pending=ipc70_bus.external_irq_level()&&
                         !ipc70_bus.external_exception_pending(ctx.msr);
      std::cout<<"V377_NAND_VECTOR_ENTRY saved="<<unsigned(saved)
               <<" regs="<<unsigned(regs)
               <<" bytes="<<unsigned(bytes)
               <<" masked="<<unsigned(masked)
               <<" pending="<<unsigned(pending)
               <<std::endl;
      check(v377_vector_seen==0u&&saved&&regs&&bytes&&masked&&pending,
            "V377 resumed NAND original vector state changed");
      ++v377_vector_seen;
      return; // execute authentic translated guest vector instructions
    }
    if(addr==0x80526ce0u){
      const uint32_t frame=ctx.gpr[4];
      const bool mapped=frame!=0u&&(frame&7u)==0u&&
           frame<=0xfffffe60u&&ctx.mmu.get_ptr(frame)!=nullptr&&
           ctx.mmu.get_ptr(frame+415u)!=nullptr;
      const bool saved=mapped&&ctx.mmu.read32(frame+408u)==v377_resume&&
           ctx.mmu.read32(frame+412u)==v377_srr1;
      const bool vector=v377_vector_seen==1u&&ctx.pc==addr;
      const bool index=ctx.gpr[3]==4u;
      const bool masked=(ctx.msr&undercover::wii::IosBus::MSR_EE)==0u&&
           !ipc70_bus.external_exception_pending(ctx.msr);
      const auto ctrl=ipc70_bus.read32(undercover::wii::IosBus::IPC+
                                      undercover::wii::IpcMailbox::PPCCTRL);
      const bool y1=ctrl.has_value()&&
           ((*ctrl&undercover::wii::IpcMailbox::Y1)!=0u)&&
           ((*ctrl&undercover::wii::IpcMailbox::Y2)==0u)&&
           ipc70_bus.external_irq_level();
      const bool advanced=ctx.inst_count>v377_start_inst;
      std::cout<<"V377_NAND_HANDLER_ENTRY vector="<<unsigned(vector)
               <<" index="<<unsigned(index)
               <<" frame="<<unsigned(mapped)
               <<" saved="<<unsigned(saved)
               <<" masked="<<unsigned(masked)
               <<" y1="<<unsigned(y1)
               <<" advanced="<<unsigned(advanced)
               <<std::endl;
      check(vector&&index&&mapped&&saved&&masked&&y1&&advanced,
            "V377 original NAND Y1 vector/exception handler ABI differs");
      ++v377_handler_seen;
      ctx.is_running=false;throw ExceptionStop{};
    }
  }
"""

def select_v160(source:str)->tuple[int,int,str]:
    if source.count(V160)!=1:
        raise ValueError('V160 original SC-only assertion label moved')
    label=source.index(V160)
    if label==0 or source[label-1]!='"' or source[label+len(V160)]!='"':
        raise ValueError('V160 not a unique quoted assertion')
    end=source.find(');',label)
    if end<0 or end-label>180:
        raise ValueError('V160 original assertion ending absent')
    end+=2
    found=[]
    for match in re.finditer(r'(?m)^[ \t]{2,16}check\(',source[max(0,label-1800):label]):
        start=max(0,label-1800)+match.start()
        value=source[start:end]
        if (len(value)<80 or len(value)>1800 or
            ';' in value[:-1] or value.count('check(')!=1 or
            not all(token in value for token in REQUIRED)):
            continue
        found.append((start,end,value))
    if len(found)!=1:
        raise ValueError('V160 SC-only completion assertion ambiguous')
    return found[0]

def wrap_v160(old:str)->str:
    pad=old[:old.index('check(')]
    if pad.strip() or len(pad)<2 or len(pad)>16:
        raise ValueError('V377 V160 indentation changed')
    return (
        pad+'// V377: historical SC completion oracle does not apply after NAND IRQ.\n'
        +pad+'if(nwii::runtime::v250_candidate_mode&&\n'
        +pad+'   nwii::runtime::v250_nand_seen==1u){\n'
        +pad+'  using V377Bus=undercover::wii::IosBus;\n'
        +pad+'  using V377Mail=undercover::wii::IpcMailbox;\n'
        +pad+'  const auto v377_ctrl=nwii::runtime::ipc70_bus.read32(\n'
        +pad+'       V377Bus::IPC+V377Mail::PPCCTRL);\n'
        +pad+'  const bool v377_irq=nwii::runtime::ipc70_bus.external_irq_level()&&\n'
        +pad+'       v377_ctrl.has_value()&&((*v377_ctrl&V377Mail::Y1)!=0u)&&\n'
        +pad+'       ((*v377_ctrl&V377Mail::Y2)==0u)&&\n'
        +pad+'       !nwii::runtime::ipc70_bus.pending_native_ios_request();\n'
        +pad+'  const bool v377_vector=!c.is_running&&\n'
        +pad+'       c.pc==undercover::wii::ExternalVector&&\n'
        +pad+'       c.srr0!=0u&&(c.srr0&3u)==0u&&\n'
        +pad+'       (c.srr1&V377Bus::MSR_EE)!=0u&&\n'
        +pad+'       (c.msr&V377Bus::MSR_EE)==0u;\n'
        +pad+'  bool v377_bytes=true;\n'
        +pad+'  for(size_t v377_i=0u;v377_i<nwii::runtime::irq74_vector.size();++v377_i){\n'
        +pad+'    const uint32_t v377_at=undercover::wii::ExternalVector+uint32_t(v377_i);\n'
        +pad+'    v377_bytes=v377_bytes&&c.mmu.get_ptr(v377_at)!=nullptr&&\n'
        +pad+'         c.mmu.read8(v377_at)==nwii::runtime::irq74_vector[v377_i];\n'
        +pad+'  }\n'
        +pad+'  check(v377_irq&&v377_vector&&v377_bytes,\n'
        +pad+'        "V377 original NAND Y1 vector resumption prerequisite missing");\n'
        +pad+'  nwii::runtime::v377_live=true;\n'
        +pad+'  nwii::runtime::v377_vector_seen=0u;\n'
        +pad+'  nwii::runtime::v377_handler_seen=0u;\n'
        +pad+'  nwii::runtime::v377_resume=c.srr0;\n'
        +pad+'  nwii::runtime::v377_srr1=c.srr1;\n'
        +pad+'  nwii::runtime::v377_irq_msr=c.msr;\n'
        +pad+'  nwii::runtime::v377_lr=c.lr;\n'
        +pad+'  nwii::runtime::v377_ctr=c.ctr;\n'
        +pad+'  nwii::runtime::v377_xer=c.xer;\n'
        +pad+'  nwii::runtime::v377_start_inst=c.inst_count;\n'
        +pad+'  nwii::runtime::v377_gprs=c.gpr;\n'
        +pad+'  c.is_running=true; // resume at the genuine saved vector PC\n'
        +pad+'  bool v377_stopped=false;\n'
        +pad+'  try{run_game(c);}catch(const ExceptionStop&){v377_stopped=true;}\n'
        +pad+'  const bool v377_completed=v377_stopped&&\n'
        +pad+'       nwii::runtime::v377_vector_seen==1u&&\n'
        +pad+'       nwii::runtime::v377_handler_seen==1u&&\n'
        +pad+'       !c.is_running&&c.pc==0x80526ce0u;\n'
        +pad+'  std::cout<<"V377_NAND_HANDLER_TRIAL stopped="<<unsigned(v377_stopped)\n'
        +pad+'           <<" vector="<<unsigned(nwii::runtime::v377_vector_seen==1u)\n'
        +pad+'           <<" handler="<<unsigned(nwii::runtime::v377_handler_seen==1u)\n'
        +pad+'           <<" completed="<<unsigned(v377_completed)<<std::endl;\n'
        +pad+'  check(v377_completed,\n'
        +pad+'        "V377 original NAND vector never reached actual Wii handler entry");\n'
        +pad+'  continue; // finish this authenticated NAND-only bounded trial\n'
        +pad+'}else{\n'
        +old+'\n'
        +pad+'}\n'
    )

def patch(source:str)->str:
    if (source.count(HEAD)!=1 or source.count(V376)!=1 or
        source.count(V375)!=1 or source.count(V160)!=1 or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        'irq74_vector' not in source or MARKER in source or
        VECTOR in source or TRIAL in source):
        raise ValueError('V377 authenticated NAND/SC phase seam changed')
    start,end,old=select_v160(source)
    wrapped=wrap_v160(old)
    output=source[:start]+wrapped+source[end:]
    output=output.replace(HEAD,STATE+HEAD+TRACE,1)
    if (output.count(MARKER)!=1 or output.count(VECTOR)!=1 or
        output.count(TRIAL)!=1 or output.count(V160)!=1 or
        output.replace(STATE+HEAD+TRACE,HEAD,1).
          replace(wrapped,old,1)!=source):
        raise ValueError('V377 source changes are not reversible')
    return output

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prior_private_harness',type=Path)
    parser.add_argument('next_private_harness',type=Path)
    opts=parser.parse_args()
    try:
        if opts.next_private_harness.exists() or opts.next_private_harness.is_symlink():
            raise ValueError('output_exists')
        with opts.next_private_harness.open('x',encoding='utf-8') as out:
            out.write(patch(opts.prior_private_harness.read_text(encoding='utf-8')))
    except (ValueError,OSError):
        print('V377_NAND_HANDLER_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V377_NAND_HANDLER_ROUTE installed=1 original_guest=1 resume_original_vector=1 sc_oracle_preserved=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
