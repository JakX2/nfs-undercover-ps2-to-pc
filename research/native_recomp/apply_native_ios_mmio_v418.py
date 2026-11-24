#!/usr/bin/env python3
"""Opt-in source-only NWii MMIO transport seam; no automatic runtime binding."""
from __future__ import annotations
import argparse
from pathlib import Path
from apply_hollywood_mmio_v62 import rewrite as aperture

HEADERS=("wii_ios_memory.h","wii_physical_ram.h","wii_ipc_mailbox.h",
         "wii_hollywood_irq.h","wii_guest_filesystem.h","wii_stm_ios.h",
         "wii_ios_bus.h","wii_ios_yield_scheduler.h","wii_native_ios_transport.h",
         "wii_native_ios_binding.h")
INCLUDE='#include "runtime/hw/mmio_dispatcher.h"'
BIND='undercover::wii::NativeIosBinding'
PAIRS=(
    (INCLUDE,INCLUDE+'\n#include "undercover/wii_native_ios_binding.h"'),
    ('uint32_t HW_Reg_Read32(uint32_t addr) {',
     'uint32_t HW_Reg_Read32(uint32_t addr) {\n  if (auto value = '+BIND+'::read32(addr)) return *value;'),
    ('uint16_t HW_Reg_Read16(uint32_t addr) {',
     'uint16_t HW_Reg_Read16(uint32_t addr) {\n  '+BIND+'::reject_subword(addr);'),
    ('void HW_Reg_Write32(uint32_t addr, uint32_t val) {',
     'void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  if ('+BIND+'::write32(addr, val)) return;'),
    ('  MMIODispatcher::get().write32(addr, val);',
     '  MMIODispatcher::get().write32(addr, val);\n  '+BIND+'::refresh_pi(addr);'),
    ('void HW_Reg_Write16(uint32_t addr, uint16_t val) {',
     'void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  '+BIND+'::reject_subword(addr);'),
)

def rewrite(source:str)->str:
    if all(source.count(new)==1 for _,new in PAIRS):
        back=source
        for old,new in reversed(PAIRS):back=back.replace(new,old,1)
        if BIND in back or any(back.count(old)!=1 for old,_ in PAIRS):raise ValueError('ambiguous patched MMIO seam')
        return source
    if BIND in source or any(new in source or source.count(old)!=1 for old,new in PAIRS):raise ValueError('unknown upstream MMIO seam')
    result=source
    for old,new in PAIRS:result=result.replace(old,new,1)
    back=result
    for old,new in reversed(PAIRS):back=back.replace(new,old,1)
    if back!=source:raise ValueError('nonreversible MMIO seam')
    return result

def apply(root:Path,host:Path)->None:
    ctx=root/'nWiiRuntime/include/runtime/cpu_context.h'
    mmio=root/'nWiiRuntime/src/core/os_hle_stubs.cpp'
    dest=root/'nWiiRuntime/include/undercover'
    # Validate both source shapes and every destination before any writes.
    plans={ctx:aperture(ctx.read_text(encoding='utf-8')).encode(),mmio:rewrite(mmio.read_text(encoding='utf-8')).encode()}
    if dest.is_symlink():raise ValueError('header destination symlink')
    for name in HEADERS:
        data=(host/name).read_bytes();out=dest/name
        if out.is_symlink() or (out.exists() and out.read_bytes()!=data):raise ValueError('header destination conflict')
        plans[out]=data
    for path in (ctx,mmio):
        if path.is_symlink():raise ValueError('source symlink')
    dest.mkdir(exist_ok=True)
    for path,data in plans.items():
        if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('upstream_root',type=Path);a=p.parse_args()
    try:apply(a.upstream_root,Path(__file__).parent)
    except (ValueError,OSError):
        print('V418_NWII_MMIO_ROUTE installed=0');return 1
    print('V418_NWII_MMIO_ROUTE installed=1 opt_in=1 automatic_ios=0');return 0
if __name__=='__main__':raise SystemExit(main())
