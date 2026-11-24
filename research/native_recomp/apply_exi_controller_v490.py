#!/usr/bin/env python3
"""Opt-in EXI controller route in the generated V481 MMU binding."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
HEADER='#include "wii_irq_banks_v480.h"'
CTOR='    explicit IrqBankBinding(WiiIrqBanks& b):banks_(b){'
FIELD='    WiiIrqBanks& banks_;'
ENUM='enum class Reg{None,Unsupported,MiMask,MiStatus,Exi0,Exi1,Exi2,Ai};'
CASE_R='            case Reg::Exi0:return active_->banks_.exi_csr(0);'
CASE_W='            case Reg::Exi0:active_->banks_.write_exi_csr(0,value);return true;'
IDENT='            if(bad)return Reg::Unsupported;\n            return p==Exi?Reg::Exi0:'
PAIRS=((HEADER,HEADER+'\n#include "wii_exi_controller_v489.h"'),
       (CTOR,'    explicit IrqBankBinding(WiiIrqBanks& b,ExiController* exi=nullptr):banks_(b),exi_(exi){\n        if(exi_&&!exi_->bound_to(b))throw std::invalid_argument("EXI bank identity");'),
       (FIELD,FIELD+'\n    ExiController* exi_;'),
       (ENUM,ENUM.replace('Exi2,Ai','Exi2,ExiFull,Ai')),
       (CASE_R,'            case Reg::ExiFull:{const auto off=exi_offset(a);return active_->exi_->read(off/20u,off%20u);}\n'+CASE_R),
       (CASE_W,'            case Reg::ExiFull:{const auto off=exi_offset(a);active_->exi_->write(off/20u,off%20u,value);return true;}\n'+CASE_W),
       (IDENT,'            if(bad)return Reg::Unsupported;\n            if(active_&&active_->exi_)return !(p&3u)?Reg::ExiFull:Reg::Unsupported;\n            return p==Exi?Reg::Exi0:'),
       ('    static Reg identify(uint32_t a)noexcept{','    static uint32_t exi_offset(uint32_t a)noexcept{return ((a&0x3fffffffu)&~Mirror)-Exi;}\n    static Reg identify(uint32_t a)noexcept{'))
MAIN_PAIRS=(('    std::optional<undercover::wii::IrqBankBinding> bank_binding;',
             '    std::optional<undercover::wii::ExiController> exi_controller;\n    std::optional<undercover::wii::IrqBankBinding> bank_binding;'),
            ('        bank_binding.emplace(*banks);','''        const char* exi_enabled=std::getenv("UNDERCOVER_V490_EXI_CONTROLLER");
        if(exi_enabled&&exi_enabled[0]=='1'&&exi_enabled[1]=='\\0')exi_controller.emplace(*banks);
        bank_binding.emplace(*banks,exi_controller?&*exi_controller:nullptr);'''))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover';binding=dest/'wii_irq_bank_binding_v481.h'
    main=rt/'src/core/main.cpp';controller=dest/'wii_exi_controller_v489.h'
    if any(p.is_symlink() for p in (dest,binding,main,controller)):raise ValueError('symlink')
    data=(host/controller.name).read_bytes()
    if controller.exists() and controller.read_bytes()!=data:raise ValueError('header conflict')
    updates={binding:rewrite(binding.read_text(encoding='utf-8'),PAIRS).encode(),
             main:rewrite(main.read_text(encoding='utf-8'),MAIN_PAIRS).encode(),controller:data}
    for path,content in updates.items():
        if not path.exists() or path.read_bytes()!=content:path.write_bytes(content)
def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:apply(a.generated,Path(__file__).parent)
    except (OSError,ValueError):
        print('V490_EXI_ROUTE installed=0');return 1
    print('V490_EXI_ROUTE installed=1 opt_in=1 endpoints=0 dma=0');return 0
if __name__=='__main__':raise SystemExit(main())
