#!/usr/bin/env python3
"""Bind the explicit cold arena reset profile to actual native MMIO."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_native_ios_width_v421 import ACCESS
HEADER='#include "undercover/wii_arena_reset_v606.h"'
B='undercover::wii::ArenaResetBinding'
CTX=(('#include <stack>','#include <stack>\n'+HEADER),)+tuple(
    (old,old+'\n    '+B+f'::check(addr,{width}u,{str("read_f" not in old and "write_f" not in old).lower()},{str("write" in old).lower()});')
    for old,width,_ in ACCESS)
STUB=(('#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+HEADER),
    ('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if(auto v='+B+'::read32(addr))return *v;'),
    ('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  '+B+'::check(addr,2,true,false);'),
    ('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  '+B+'::check(addr,4,true,true);'),
    ('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  '+B+'::check(addr,2,true,true);'))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover/wii_arena_reset_v606.h'
    if dest.parent.is_symlink() or dest.is_symlink():raise ValueError('destination')
    data=(host/dest.name).read_bytes()
    if dest.exists() and dest.read_bytes()!=data:raise ValueError('header conflict')
    files={}
    for p,pairs in ((rt/'include/runtime/cpu_context.h',CTX),(rt/'src/core/os_hle_stubs.cpp',STUB)):
        if p.is_symlink():raise ValueError('symlink')
        files[p]=rewrite(p.read_text(encoding='utf-8'),pairs).encode()
    dest.parent.mkdir(exist_ok=True);files[dest]=data
    for p,v in files.items():
        if not p.exists() or p.read_bytes()!=v:p.write_bytes(v)
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):print('V606_ARENA_RESET_ROUTE installed=0');return 1
    print('V606_ARENA_RESET_ROUTE installed=1 default_inactive=1 cold_profile=1');return 0
if __name__=='__main__':raise SystemExit(main())
