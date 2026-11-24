#!/usr/bin/env python3
"""Opt-in native SI cold communication binding after the V501 profile."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_exi_profile_v501 import CTX_PAIRS as PROFILE_ACCESS
from apply_native_ios_width_v421 import ACCESS
HEADER='#include "undercover/wii_exi_profile_v501.h"'
SI='#include "undercover/wii_si_binding_v512.h"'
BIND='undercover::wii::SiBinding'
CTX_PAIRS=((HEADER,HEADER+'\n'+SI),)+tuple(
    (new,new+'\n    '+BIND+'::check(addr,'+str(width)+'u,'+integer+');')
    for new,width,integer in [
        (pair[1],width,str('read_f' not in pair[0] and 'write_f' not in pair[0]).lower())
        for pair,(_,width,_) in zip(PROFILE_ACCESS[1:],ACCESS)])
STUB_PAIRS=((HEADER,HEADER+'\n'+SI),
    ('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if(auto v='+BIND+'::read32(addr))return *v;\n  '+BIND+'::refresh_pi(addr);'),
    ('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  if('+BIND+'::write32(addr,val))return;'),
    ('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  '+BIND+'::check(addr,2,true);'),
    ('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  '+BIND+'::check(addr,2,true);'))
MAIN_PAIRS=((HEADER,HEADER+'\n'+SI),
    ('    std::optional<undercover::wii::ExiProfileSession> exi_session;',
     '''    std::optional<undercover::wii::ExiProfileSession> exi_session;
    std::optional<undercover::wii::SiController> si_controller;
    std::optional<undercover::wii::SiBinding> si_binding;
    if(const char* enabled=std::getenv("UNDERCOVER_V512_SI");enabled&&enabled[0]=='1'&&enabled[1]=='\\0'){
        si_controller.emplace(nwii::runtime::hw::pi_intsr);
        si_binding.emplace(*si_controller);
    }'''))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover'
    paths=((rt/'include/runtime/cpu_context.h',CTX_PAIRS),(rt/'src/core/os_hle_stubs.cpp',STUB_PAIRS),
           (rt/'src/core/main.cpp',MAIN_PAIRS))
    if dest.is_symlink() or not (dest/'wii_exi_profile_v501.h').is_file():raise ValueError('predecessor')
    updates={}
    for path,pairs in paths:
        if path.is_symlink():raise ValueError('symlink')
        updates[path]=rewrite(path.read_text(encoding='utf-8'),pairs).encode()
    for name in ('wii_si_controller_v511.h','wii_si_binding_v512.h'):
        path=dest/name;data=(host/name).read_bytes()
        if path.is_symlink() or (path.exists() and path.read_bytes()!=data):raise ValueError('header conflict')
        updates[path]=data
    for path,data in updates.items():
        if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V512_SI_ROUTE installed=0');return 1
    print('V512_SI_ROUTE installed=1 opt_in=1 polling=0 endpoints=0');return 0
if __name__=='__main__':raise SystemExit(main())
