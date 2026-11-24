#!/usr/bin/env python3
"""Opt-in Hollywood audio ACR register subset after native VI/MMIO ownership."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_vi_clock_v522 import CTX_PAIRS as VI_ACCESS
from apply_native_ios_width_v421 import ACCESS
HEADER='#include "undercover/wii_vi_clock_v522.h"'
ACR='#include "undercover/wii_audio_acr_v537.h"'
BIND='undercover::wii::AudioAcrBinding'
CTX_PAIRS=((HEADER,HEADER+'\n'+ACR),)+tuple(
    (new,new+'\n    '+BIND+'::check(addr,'+str(width)+'u,'+integer+');')
    for new,width,integer in [
        (pair[1],width,str('read_f' not in pair[0] and 'write_f' not in pair[0]).lower())
        for pair,(_,width,_) in zip(VI_ACCESS[1:],ACCESS)])
STUB_PAIRS=((HEADER,HEADER+'\n'+ACR),
    ('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if(auto v='+BIND+'::read32(addr))return *v;'),
    ('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  if('+BIND+'::write32(addr,val))return;'))
MAIN_PAIRS=((HEADER,HEADER+'\n'+ACR),
    ('    std::optional<undercover::wii::ViClockBinding> vi_clock;',
     '''    std::optional<undercover::wii::ViClockBinding> vi_clock;
    std::optional<undercover::wii::AudioAcrBinding> audio_acr;
    if(const char* acr=std::getenv("UNDERCOVER_V537_ACR");acr){
        if(acr[0]!='1'||acr[1]!='\\0')std::_Exit(109);
        // Explicit synthetic boot register values, not hardware defaults.
        audio_acr.emplace(undercover::wii::AudioAcrBinding::Profile{0x12345680u,0xa955aa55u,0xf1234567u});
    }'''))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover';header=dest/'wii_audio_acr_v537.h'
    if any(p.is_symlink() for p in (dest,header)) or not (dest/'wii_vi_clock_v522.h').is_file():raise ValueError('predecessor')
    data=(host/header.name).read_bytes()
    if header.exists() and header.read_bytes()!=data:raise ValueError('header conflict')
    updates={header:data}
    for path,pairs in ((rt/'include/runtime/cpu_context.h',CTX_PAIRS),
                       (rt/'src/core/os_hle_stubs.cpp',STUB_PAIRS),(rt/'src/core/main.cpp',MAIN_PAIRS)):
        if path.is_symlink():raise ValueError('symlink')
        updates[path]=rewrite(path.read_text(encoding='utf-8'),pairs).encode()
    for p,c in updates.items():
        if not p.exists() or p.read_bytes()!=c:p.write_bytes(c)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V537_AUDIO_ACR installed=0');return 1
    print('V537_AUDIO_ACR installed=1 opt_in=1 pll_timing=0');return 0
if __name__=='__main__':raise SystemExit(main())
