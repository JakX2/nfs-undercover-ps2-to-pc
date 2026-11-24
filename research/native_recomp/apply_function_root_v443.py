#!/usr/bin/env python3
"""Keep the actual analyzer root separate from the lowest emitted instruction.

A backward tail branch can make a function's sorted instruction list begin
before its actual entry. Use the root for identity and the lowest label for
fallthrough. Never change the guest branch or instruction list.
"""
import argparse
from pathlib import Path
ANALYZER=Path('nWiiAnalyzer/src/analyzer.cpp')
EMITTER=Path('nWiiRecomp/src/recompiler.cpp')
ROOT_OLD='    func.start_address = min_pc;'
ROOT_NEW='    func.start_address = func_start;'
MIN_DECL='    uint32_t min_pc = func_start;\n'
MIN_UPDATE='        min_pc = std::min(min_pc, current_pc);\n'
DISPATCH_OLD='''  if (valid_addrs.size() > 1) {
    out << "    if (ctx.pc != 0x" << std::hex << std::uppercase
        << func.start_address << std::dec << ") {\\n";
    out << "        switch (ctx.pc) {\\n";
    for (uint32_t addr : valid_addrs) {
      if (addr != func.start_address) {'''
DISPATCH_NEW='''  if (valid_addrs.size() > 1) {
    // Sorted instruction order is not necessarily the discovered root.
    const uint32_t first_addr = *valid_addrs.begin();
    out << "    if (ctx.pc != 0x" << std::hex << std::uppercase
        << first_addr << std::dec << ") {\\n";
    out << "        switch (ctx.pc) {\\n";
    for (uint32_t addr : valid_addrs) {
      if (addr != first_addr) {'''
def rewrite(analyzer,emitter):
    before=(analyzer.count(ROOT_OLD)==1 and analyzer.count(MIN_DECL)==1 and
            analyzer.count(MIN_UPDATE)==1 and ROOT_NEW not in analyzer)
    after=(analyzer.count(ROOT_NEW)==1 and ROOT_OLD not in analyzer and
           MIN_DECL not in analyzer and MIN_UPDATE not in analyzer)
    old_dispatch=emitter.count(DISPATCH_OLD)==1 and DISPATCH_NEW not in emitter
    new_dispatch=emitter.count(DISPATCH_NEW)==1 and DISPATCH_OLD not in emitter
    if after and new_dispatch:return analyzer,emitter
    if not(before and old_dispatch):raise ValueError('unknown or mixed root/dispatch layout')
    a=analyzer.replace(ROOT_OLD,ROOT_NEW,1).replace(MIN_DECL,'',1).replace(MIN_UPDATE,'',1)
    e=emitter.replace(DISPATCH_OLD,DISPATCH_NEW,1)
    return a,e
def apply(root):
    a=root/ANALYZER;e=root/EMITTER
    if a.is_symlink() or e.is_symlink():raise ValueError('symlink')
    old=(a.read_text(encoding='utf-8'),e.read_text(encoding='utf-8'))
    new=rewrite(*old)
    if old==new:return False
    a.write_text(new[0],encoding='utf-8');e.write_text(new[1],encoding='utf-8')
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V443_FUNCTION_ROOT installed=1 changed={int(apply(a.root))}')
