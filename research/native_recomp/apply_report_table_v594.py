#!/usr/bin/env python3
"""Exact boot-report local table analysis, enabled only in an authenticated scope."""
from pathlib import Path
import argparse
from apply_irq_bootstrap_v475 import rewrite
from make_v594_boot_report_geometry import START,END,TARGETS,TABLE,geometry
FILE=Path('nWiiAnalyzer/src/analyzer.cpp')
ROOT='    uint32_t func_start = function_queue.front();\n    function_queue.pop();'
READ='        uint32_t raw_inst;\n        if (!read_instruction(current_pc, raw_inst))'
BRANCH='        } else if (inst.is_unconditional_indirect_branch()) {'
def pairs(bctr):
    if bctr&3 or not START<=bctr<TARGETS[0]:raise ValueError('bctr address')
    root=ROOT+'''
    // Authenticated boot-report internal cases are not independent roots.
    if (func_start>0x805203c4u && func_start<0x80520670u) continue;'''
    read='''        const bool report_pc=current_pc>=0x805203c4u&&current_pc<0x80520670u;
        if(report_pc!=(func_start==0x805203c4u)) break;
'''+READ
    branch=BRANCH+f'''
          if(func_start==0x805203c4u && current_pc==0x{bctr:08x}u) {{
            if(raw_inst!=0x4e800420u) throw std::runtime_error("report branch mismatch");
            std::set<uint32_t> report_targets;
            for(unsigned i=0;i<26;++i) {{
              uint32_t target=read_data32(0x{TABLE:08x}u+4*i);
              if(target<0x805204ecu||target>0x8052054cu||(target-0x805204ecu)%16u||
                 !is_text_address(target)) throw std::runtime_error("report table mismatch");
              report_targets.insert(target);
            }}
            if(report_targets.size()!=7) throw std::runtime_error("report target count");
            for(auto target:report_targets) {{
              block_queue.push(target);local_jump_targets.insert(target);
            }}
            break;
          }}'''
    return ((ROOT,root),(READ,read),(BRANCH,branch))
def apply(root,bctr):
    p=root/FILE
    if p.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');out=rewrite(old,pairs(bctr))
    if old!=out:p.write_text(out,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        bctr,_=geometry(a.dol.read_bytes(),a.elf.read_bytes());apply(a.root,bctr)
    except (OSError,ValueError,UnicodeError):print('V594_REPORT_ANALYZER installed=0');return 1
    print('V594_REPORT_ANALYZER installed=1 scoped=1 table=26 targets=7');return 0
if __name__=='__main__':raise SystemExit(main())
