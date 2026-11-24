#!/usr/bin/env python3
"""Opt-in VI clock selector after V512 SI MMIO; no display or timing HLE."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_si_binding_v512 import CTX_PAIRS as SI_ACCESS
from apply_native_ios_width_v421 import ACCESS
HEADER='#include "undercover/wii_si_binding_v512.h"'
VI='#include "undercover/wii_vi_clock_v522.h"'
BIND='undercover::wii::ViClockBinding'
CTX_PAIRS=((HEADER,HEADER+'\n'+VI),)+tuple(
    (new,new+'\n    '+BIND+'::check(addr,'+str(width)+'u,'+integer+');')
    for new,width,integer in [
        (pair[1],width,str('read_f' not in pair[0] and 'write_f' not in pair[0]).lower())
        for pair,(_,width,_) in zip(SI_ACCESS[1:],ACCESS)])
STUB_PAIRS=((HEADER,HEADER+'\n'+VI),
    ('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  if(auto v='+BIND+'::read16(addr))return *v;'),
    ('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  if('+BIND+'::write16(addr,val))return;'))
MAIN_PAIRS=((HEADER,HEADER+'\n'+VI),
    ('    std::optional<undercover::wii::SiBinding> si_binding;',
     '''    std::optional<undercover::wii::SiBinding> si_binding;
    std::optional<undercover::wii::ViClockBinding> vi_clock;
    if(const char* clock=std::getenv("UNDERCOVER_V522_VICLK");clock){
        if((clock[0]!='0'&&clock[0]!='1')||clock[1]!='\\0')std::_Exit(105);
        vi_clock.emplace(static_cast<uint16_t>(clock[0]-'0'));
    }'''))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover'
    header=dest/'wii_vi_clock_v522.h'
    if any(p.is_symlink() for p in (dest,header)) or not (dest/'wii_si_binding_v512.h').is_file():raise ValueError('predecessor')
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
        print('V522_VI_CLOCK installed=0');return 1
    print('V522_VI_CLOCK installed=1 opt_in=1 timing=0');return 0
if __name__=='__main__':raise SystemExit(main())
