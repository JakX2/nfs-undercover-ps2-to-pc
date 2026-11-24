#!/usr/bin/env python3
"""Attach opt-in cold MI/EXI/AI banks after the V475 runtime bootstrap."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_native_ios_width_v421 import ACCESS,BIND,INCLUDE
BANK='undercover::wii::IrqBankBinding'
HEADER='#include "undercover/wii_irq_bank_binding_v481.h"'
NATIVE='#include "undercover/wii_native_ios_binding.h"'
MAIN_PAIRS=((NATIVE,NATIVE+'\n'+HEADER),
('    undercover::wii::NativeIosBinding binding(transport);', '''    undercover::wii::NativeIosBinding binding(transport);
    const char* irq_banks = std::getenv("UNDERCOVER_V481_IRQ_BANKS");
    std::optional<undercover::wii::WiiIrqBanks> banks;
    std::optional<undercover::wii::IrqBankBinding> bank_binding;
    if (irq_banks && irq_banks[0]=='1' && irq_banks[1]=='\\0') {
        banks.emplace(nwii::runtime::hw::pi_intsr);
        bank_binding.emplace(*banks);
    }'''))
STUB_PAIRS=((NATIVE,NATIVE+'\n'+HEADER),
('uint32_t HW_Reg_Read32(uint32_t addr) {','uint32_t HW_Reg_Read32(uint32_t addr) {\n  if (auto v = '+BANK+'::read32(addr)) return *v;\n  '+BANK+'::refresh_pi(addr);'),
('uint16_t HW_Reg_Read16(uint32_t addr) {','uint16_t HW_Reg_Read16(uint32_t addr) {\n  if (auto v = '+BANK+'::read16(addr)) return *v;'),
('void HW_Reg_Write32(uint32_t addr, uint32_t val) {','void HW_Reg_Write32(uint32_t addr, uint32_t val) {\n  if ('+BANK+'::write32(addr,val)) return;'),
('void HW_Reg_Write16(uint32_t addr, uint16_t val) {','void HW_Reg_Write16(uint32_t addr, uint16_t val) {\n  if ('+BANK+'::write16(addr,val)) return;'),
('  undercover::wii::NativeIosBinding::refresh_pi(addr);','  undercover::wii::NativeIosBinding::refresh_pi(addr);\n  '+BANK+'::refresh_pi(addr);'))
# There are repeated access-check strings at the same width, so anchor each
# specific MMU function rather than globally replacing duplicate strings.
CTX_PAIRS=((NATIVE,NATIVE+'\n'+HEADER),)+tuple(
    (old+'\n    '+BIND+f'::check_cpu_access(addr,{width}u,{str(allow).lower()});',
     old+'\n    '+BIND+f'::check_cpu_access(addr,{width}u,{str(allow).lower()});\n    '+BANK+
        f'::check_cpu_access(addr,{width}u,{str("read_f" not in old and "write_f" not in old).lower()});')
    for old,width,allow in ACCESS)
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover'
    pairs=((rt/'src/core/main.cpp',MAIN_PAIRS),(rt/'src/core/os_hle_stubs.cpp',STUB_PAIRS),
           (rt/'include/runtime/cpu_context.h',CTX_PAIRS))
    if dest.is_symlink() or not (dest/'wii_irq_bootstrap_v475.h').is_file():raise ValueError('predecessor')
    changes={}
    for path,ps in pairs:
        if path.is_symlink():raise ValueError('source symlink')
        changes[path]=rewrite(path.read_text(encoding='utf-8'),ps).encode()
    for name in ('wii_irq_banks_v480.h','wii_irq_bank_binding_v481.h'):
        out=dest/name;data=(host/name).read_bytes()
        if out.is_symlink() or (out.exists() and out.read_bytes()!=data):raise ValueError('header conflict')
        changes[out]=data
    for path,data in changes.items():
        if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:apply(a.generated,Path(__file__).parent)
    except (OSError,ValueError):
        print('V481_IRQ_BANK_ROUTE installed=0');return 1
    print('V481_IRQ_BANK_ROUTE installed=1 opt_in=1 transfers=0 audio_playback=0');return 0
if __name__=='__main__':raise SystemExit(main())
