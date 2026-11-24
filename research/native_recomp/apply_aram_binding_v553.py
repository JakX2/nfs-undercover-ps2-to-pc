#!/usr/bin/env python3
"""Opt-in ARAM-only MMIO and instruction visits, no main activation."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_native_ios_width_v421 import ACCESS
from apply_native_tick_v438 import FILE as EMITTER,LABEL_TICK
BIND='undercover::wii::AramBinding'
HEADER='#include "undercover/wii_aram_binding_v553.h"'
CTX_PAIRS=(('#include <stack>','#include <stack>\n'+HEADER),('  uint64_t inst_count = 0;','  uint64_t inst_count = 0;\n  void aram_instruction_boundary() { '+BIND+'::advance(inst_count); }'))+tuple(
    (old,old+'\n    '+BIND+f'::check(addr,{width}u,{str("read_f" not in old and "write_f" not in old).lower()});')
    for old,width,_ in ACCESS)
STUB_PAIRS=(('#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+HEADER),
    ('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if(auto v='+BIND+'::read32(addr))return *v;\n  '+BIND+'::refresh_pi(addr);'),
    ('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  if(auto v='+BIND+'::read16(addr))return *v;'),
    ('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  if('+BIND+'::write32(addr,val))return;'),
    ('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  if('+BIND+'::write16(addr,val))return;'),
    ('  MMIODispatcher::get().write32(addr, val);','  MMIODispatcher::get().write32(addr, val);\n  '+BIND+'::refresh_pi(addr);'))
EMIT_PAIRS=((LABEL_TICK,LABEL_TICK+'\n  out << "    ctx.aram_instruction_boundary();\\n";'),)
def apply(root,phase,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover';updates={}
    if phase=='emitter':
        pairs=((root/EMITTER,EMIT_PAIRS),)
    else:
        pairs=((rt/'include/runtime/cpu_context.h',CTX_PAIRS),(rt/'src/core/os_hle_stubs.cpp',STUB_PAIRS))
        if dest.is_symlink():raise ValueError('symlink')
        for name in ('wii_aram_binding_v553.h','wii_aram_dma_v552.h','wii_physical_ram.h','wii_ios_memory.h'):
            p=dest/name;data=(host/name).read_bytes()
            if p.is_symlink() or (p.exists() and p.read_bytes()!=data):raise ValueError('header conflict')
            updates[p]=data
    for p,ps in pairs:
        if p.is_symlink():raise ValueError('symlink')
        updates[p]=rewrite(p.read_text(encoding='utf-8'),ps).encode()
    if phase=='runtime':dest.mkdir(exist_ok=True)
    for p,c in updates.items():
        if not p.exists() or p.read_bytes()!=c:p.write_bytes(c)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('phase',choices=('emitter','runtime'));a=p.parse_args()
    try:apply(a.root,a.phase,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V553_ARAM_ROUTE installed=0');return 1
    print(f'V553_ARAM_ROUTE installed=1 phase={a.phase} opt_in=1');return 0
if __name__=='__main__':raise SystemExit(main())
