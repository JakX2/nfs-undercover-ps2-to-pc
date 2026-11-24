#!/usr/bin/env python3
"""Opt-in exact ownership of the three authenticated physical mapping regions."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
FILE=Path('nWiiAnalyzer/src/analyzer.cpp')
ROOT='    uint32_t func_start = function_queue.front();\n    function_queue.pop();'
ROOT_NEW=ROOT+'''
    // Explicit owner-authenticated BAT roots, never general code discovery.
    const auto bat_owner = [](uint32_t a)->uint32_t {
      if (a>=0x805270c4u && a<0x80527144u) return 0x805270c4u;
      if (a>=0x80527144u && a<0x80527218u) return 0x80527144u;
      if (a>=0x80527550u && a<0x80527568u) return 0x80527550u;
      return 0;
    };
    if (bat_owner(func_start) && bat_owner(func_start)!=func_start) continue;'''
READ='        uint32_t raw_inst;\n        if (!read_instruction(current_pc, raw_inst))'
READ_NEW='''        const auto owner=bat_owner(current_pc);
        if ((owner && owner!=func_start) ||
            (bat_owner(func_start) && owner!=func_start)) break;
'''+READ
INST='        ppc::Instruction inst(raw_inst);'
INST_NEW=INST+'''
        if (owner && raw_inst==0x4c000064u) break; // terminal RFI in exact mapper'''
PAIRS=((ROOT,ROOT_NEW),(READ,READ_NEW),(INST,INST_NEW))
def apply(root):
    p=root/FILE
    if p.is_symlink():raise ValueError('symlink')
    s=p.read_text(encoding='utf-8');out=rewrite(s,PAIRS)
    if out!=s:p.write_text(out,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root)
    except (OSError,ValueError,UnicodeError):print('V586_BAT_ANALYZER installed=0');return 1
    print('V586_BAT_ANALYZER installed=1 exact_roots=3 terminal_rfi=1');return 0
if __name__=='__main__':raise SystemExit(main())
