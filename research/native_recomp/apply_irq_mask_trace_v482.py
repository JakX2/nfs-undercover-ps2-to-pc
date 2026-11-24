#!/usr/bin/env python3
"""Read-only observation of successful MMIO accesses after the V481 bindings."""
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
HEADER='#include "undercover/wii_irq_bank_binding_v481.h"'
BIND='undercover::wii::IrqBankBinding'
T='undercover::wii::irq_mask_io'
PAIRS=((HEADER,HEADER+'\n#include "undercover/wii_irq_return_witness_v482.h"'),)
for width in (16,32):
    a=f'  if (auto v = {BIND}::read{width}(addr)) return *v;'
    b=f'  if (auto v = {BIND}::read{width}(addr)) {{ {T}.record(false,addr,{width}u,*v,true); return *v; }}'
    c=f'  return MMIODispatcher::get().read{width}(addr);'
    d=f'  const auto v=MMIODispatcher::get().read{width}(addr);\n  {T}.record(false,addr,{width}u,v,false);\n  return v;'
    e=f'  if ({BIND}::write{width}(addr,val)) return;'
    f=f'  if ({BIND}::write{width}(addr,val)) {{ {T}.record(true,addr,{width}u,val,true); return; }}'
    g=f'  MMIODispatcher::get().write{width}(addr, val);'
    j=g+f'\n  {T}.record(true,addr,{width}u,val,false);'
    PAIRS+=((a,b),(c,d),(e,f),(g,j))
# An unexpected IPC operation must not escape the active bank census.
NATIVE='  if (auto value = undercover::wii::NativeIosBinding::read32(addr)) return *value;'
WRITE='    undercover::wii::irq_boot_trace.record(addr,val,32u,true);'
PAIRS+=((NATIVE,'  if (auto value = undercover::wii::NativeIosBinding::read32(addr)) { '+T+'.record(false,addr,32u,*value,true); return *value; }'),
        (WRITE,WRITE+'\n    '+T+'.record(true,addr,32u,val,true);'))
def apply(root,host):
    rt=root/'nWiiRuntime';p=rt/'src/core/os_hle_stubs.cpp';out=rt/'include/undercover/wii_irq_return_witness_v482.h'
    if p.is_symlink() or out.is_symlink() or not (out.parent/'wii_irq_bank_binding_v481.h').is_file():raise ValueError('predecessor')
    source=rewrite(p.read_text(encoding='utf-8'),PAIRS)
    data=(host/out.name).read_bytes()
    if out.exists() and out.read_bytes()!=data:raise ValueError('header conflict')
    out.write_bytes(data);p.write_text(source,encoding='utf-8')
