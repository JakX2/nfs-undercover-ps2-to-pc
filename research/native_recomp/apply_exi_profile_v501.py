#!/usr/bin/env python3
"""Opt-in host EXI profile session on the V497 runtime and V490 binding."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_native_ios_width_v421 import ACCESS,BIND
from apply_irq_banks_v481 import BANK
from apply_exi_tick_v497 import runtime as tick_runtime
HEADER='#include "undercover/wii_exi_tick_binding_v497.h"'
PROFILE='#include "undercover/wii_exi_profile_v501.h"'
MAIN_HEADER='#include "undercover/wii_irq_bank_binding_v481.h"'
MAIN_PAIRS=((MAIN_HEADER,MAIN_HEADER+'\n'+PROFILE),
('    std::optional<undercover::wii::IrqBankBinding> bank_binding;',
 '    std::optional<undercover::wii::IrqBankBinding> bank_binding;\n    std::optional<undercover::wii::ExiProfileSession> exi_session;'),
('        if(exi_enabled&&exi_enabled[0]==\'1\'&&exi_enabled[1]==\'\\0\')exi_controller.emplace(*banks);',
 '''        const char* exi_profile=std::getenv("UNDERCOVER_V501_EXI_PROFILE");
        if(exi_enabled&&exi_enabled[0]=='1'&&exi_enabled[1]=='\\0') {
            exi_controller.emplace(*banks,&transport.physical_ram());
            if(exi_profile&&*exi_profile)exi_session.emplace(*exi_controller,undercover::wii::ExiHostProfile::load(exi_profile));
        }else if(exi_profile&&*exi_profile)std::_Exit(101);'''))
STUB_PAIRS=((MAIN_HEADER,MAIN_HEADER+'\n'+PROFILE),
('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if(auto v=undercover::wii::ExiDiConfigBinding::read32(addr))return *v;'),
('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  undercover::wii::ExiDiConfigBinding::check(addr,4,true,true);'),
('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  undercover::wii::ExiDiConfigBinding::check(addr,2,true,false);'),
('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  undercover::wii::ExiDiConfigBinding::check(addr,2,true,true);'))
CTX_PAIRS=((HEADER,HEADER+'\n'+PROFILE),)+tuple(
    (old+'\n    '+BIND+f'::check_cpu_access(addr,{width}u,{str(allow).lower()});'+'\n    '+BANK+f'::check_cpu_access(addr,{width}u,{str("read_f" not in old and "write_f" not in old).lower()});',
     old+'\n    '+BIND+f'::check_cpu_access(addr,{width}u,{str(allow).lower()});'+'\n    '+BANK+f'::check_cpu_access(addr,{width}u,{str("read_f" not in old and "write_f" not in old).lower()});'+'\n    undercover::wii::ExiDiConfigBinding::check(addr,'+str(width)+'u,'+str("read_f" not in old and "write_f" not in old).lower()+','+str("write" in old).lower()+');')
    for old,width,allow in ACCESS)
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover'
    ctx=rt/'include/runtime/cpu_context.h';main=rt/'src/core/main.cpp';stub=rt/'src/core/os_hle_stubs.cpp'
    header=dest/'wii_exi_profile_v501.h'
    if any(p.is_symlink() for p in (dest,ctx,main,stub,header)) or not (dest/'wii_exi_tick_binding_v497.h').is_file():raise ValueError('predecessor')
    data=(host/header.name).read_bytes()
    if header.exists() and header.read_bytes()!=data:raise ValueError('header conflict')
    updates={ctx:rewrite(ctx.read_text(encoding='utf-8'),CTX_PAIRS).encode(),
             main:rewrite(main.read_text(encoding='utf-8'),MAIN_PAIRS).encode(),
             stub:rewrite(stub.read_text(encoding='utf-8'),STUB_PAIRS).encode(),header:data}
    for path,content in updates.items():
        if not path.exists() or path.read_bytes()!=content:path.write_bytes(content)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V501_EXI_PROFILE_ROUTE installed=0');return 1
    print('V501_EXI_PROFILE_ROUTE installed=1 opt_in=1 persistence=0');return 0
if __name__=='__main__':raise SystemExit(main())
