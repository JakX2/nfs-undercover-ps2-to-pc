#!/usr/bin/env python3
"""Close unsupported-width/alias bypasses at the pinned NWiiRuntime MMU.
Requires the opt-in V418 MMIO wrapper patch and its host headers.
"""
from __future__ import annotations
import argparse
from pathlib import Path

HEADER='#include <stack>'
BIND='undercover::wii::NativeIosBinding'
INCLUDE=HEADER+'\n#include "undercover/wii_native_ios_binding.h"'
ACCESS=(('  uint8_t read8(uint32_t addr) {',1,False),
        ('  void write8(uint32_t addr, uint8_t value) {',1,False),
        ('  uint16_t read16(uint32_t addr) {',2,False),
        ('  void write16(uint32_t addr, uint16_t value) {',2,False),
        ('  uint32_t read32(uint32_t addr) {',4,True),
        ('  void write32(uint32_t addr, uint32_t value) {',4,True),
        ('  float read_f32(uint32_t addr) {',4,False),
        ('  void write_f32(uint32_t addr, float value) {',4,False),
        ('  uint64_t read64(uint32_t addr) {',8,False),
        ('  void write64(uint32_t addr, uint64_t value) {',8,False),
        ('  double read_f64(uint32_t addr) {',8,False),
        ('  void write_f64(uint32_t addr, double value) {',8,False))
PAIRS=((HEADER,INCLUDE),)+tuple((a,a+f'\n    {BIND}::check_cpu_access(addr,{width}u,{str(allow).lower()});') for a,width,allow in ACCESS)

def rewrite(source:str)->str:
    if 'paddr >= 0x0D800000' not in source:raise ValueError('V418 Hollywood aperture missing')
    if all(source.count(b)==1 for _,b in PAIRS):
        back=source
        for a,b in reversed(PAIRS):back=back.replace(b,a,1)
        if BIND in back or any(back.count(a)!=1 for a,_ in PAIRS):raise ValueError('ambiguous width patch')
        return source
    if BIND in source or INCLUDE in source or any(source.count(a)!=1 for a,_ in PAIRS):raise ValueError('unknown MMU access seam')
    out=source
    for a,b in PAIRS:out=out.replace(a,b,1)
    back=out
    for a,b in reversed(PAIRS):back=back.replace(b,a,1)
    if back!=source:raise ValueError('nonreversible width patch')
    return out

def apply(root:Path)->None:
    rt=root/'nWiiRuntime';ctx=rt/'include/runtime/cpu_context.h';stubs=rt/'src/core/os_hle_stubs.cpp'
    binding=rt/'include/undercover/wii_native_ios_binding.h'
    if any(p.is_symlink() for p in (ctx,stubs,binding)):raise ValueError('symlink')
    if BIND+'::read32(addr)' not in stubs.read_text(encoding='utf-8') or 'static void check_cpu_access(' not in binding.read_text(encoding='utf-8'):raise ValueError('V418 binding missing')
    original=ctx.read_text(encoding='utf-8');out=rewrite(original)
    if out!=original:ctx.write_text(out,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('upstream_root',type=Path);a=p.parse_args()
    try:apply(a.upstream_root)
    except (OSError,ValueError):
        print('V421_MMIO_WIDTH_ROUTE installed=0');return 1
    print('V421_MMIO_WIDTH_ROUTE installed=1 opt_in=1 width_checks=12');return 0
if __name__=='__main__':raise SystemExit(main())
