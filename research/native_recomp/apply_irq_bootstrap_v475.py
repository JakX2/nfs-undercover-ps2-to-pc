#!/usr/bin/env python3
"""Bounded native CPU-thread IRQ bootstrap using the existing IOS transport.
Apply to a private generated runtime after V418 and V421, not to other scopes.
This does not install the asynchronous scheduling boundary or prove IOS IPC.
"""
import argparse
from pathlib import Path
from apply_native_ios_mmio_v418 import HEADERS,rewrite as mmio_rewrite
from apply_native_ios_width_v421 import rewrite as width_rewrite
from apply_hollywood_mmio_v62 import rewrite as aperture
MAIN_INCLUDE='#include "runtime/hw/hw.h"'
MAIN_RUN='  run_game(*ctx);'
MAIN_PAIRS=((MAIN_INCLUDE,MAIN_INCLUDE+'\n#include "undercover/wii_native_ios_binding.h"'),
(MAIN_RUN,'''  const char* irq_boot = std::getenv("UNDERCOVER_V475_IRQ_MMIO");
  const char* bounded = std::getenv("UNDERCOVER_V419_START");
  if (irq_boot && irq_boot[0]=='1' && irq_boot[1]=='\\0') {
    if (!bounded || bounded[0]!='1' || bounded[1]!='\\0') std::_Exit(95);
    undercover::wii::NativeIosTransport transport(ctx->mmu.mem1, ctx->mmu.mem2,
        nwii::runtime::hw::pi_intsr, nwii::runtime::hw::pi_intmr);
    undercover::wii::NativeIosBinding binding(transport);
    run_game(*ctx);
  } else {
    run_game(*ctx);
  }'''))
STUB_INCLUDE='#include "undercover/wii_native_ios_binding.h"'
NATIVE_WRITE='  if (undercover::wii::NativeIosBinding::write32(addr, val)) return;'
PI_WRITE='  undercover::wii::NativeIosBinding::refresh_pi(addr);'
HALF_WRITE='  MMIODispatcher::get().write16(addr, val);'
STUB_PAIRS=((STUB_INCLUDE,STUB_INCLUDE+'\n#include "undercover/wii_irq_bootstrap_v475.h"'),
(NATIVE_WRITE,'''  if (undercover::wii::NativeIosBinding::write32(addr, val)) {
    undercover::wii::irq_boot_trace.record(addr,val,32u,true);
    return;
  }'''),
(PI_WRITE,PI_WRITE+'\n  undercover::wii::irq_boot_trace.record(addr,val,32u,false);'),
(HALF_WRITE,HALF_WRITE+'\n  undercover::wii::irq_boot_trace.record(addr,val,16u,false);'))
def rewrite(source,pairs):
    if all(source.count(b)==1 for _,b in pairs):
        back=source
        for a,b in reversed(pairs):back=back.replace(b,a,1)
        if any(back.count(a)!=1 for a,_ in pairs):raise ValueError('ambiguous patch')
        return source
    if any(source.count(a)!=1 or b in source for a,b in pairs):raise ValueError('source shape')
    out=source
    for a,b in pairs:out=out.replace(a,b,1)
    back=out
    for a,b in reversed(pairs):back=back.replace(b,a,1)
    if back!=source:raise ValueError('roundtrip')
    return out
def apply(root,host):
    rt=root/'nWiiRuntime';main=rt/'src/core/main.cpp';stubs=rt/'src/core/os_hle_stubs.cpp'
    ctx=rt/'include/runtime/cpu_context.h';dest=rt/'include/undercover'
    vector=dest/'wii_exception_vector_witness_v457.h'
    if any(p.is_symlink() for p in (main,stubs,ctx,dest,vector)) or not vector.is_file():raise ValueError('predecessor')
    sources={p:p.read_text(encoding='utf-8') for p in (main,stubs,ctx)}
    # All transformations and destination identities are checked before
    # any file is written. This installer is for a fresh generated tree.
    updates={
        main:rewrite(sources[main],MAIN_PAIRS).encode(),
        stubs:rewrite(mmio_rewrite(sources[stubs]),STUB_PAIRS).encode(),
        ctx:width_rewrite(aperture(sources[ctx])).encode(),
    }
    for name in (*HEADERS,'wii_irq_bootstrap_v475.h'):
        out=dest/name;data=(host/name).read_bytes()
        if out.is_symlink() or (out.exists() and out.read_bytes()!=data):raise ValueError('header conflict')
        updates[out]=data
    for p,data in updates.items():
        if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('generated',type=Path);a=p.parse_args()
    try:apply(a.generated,Path(__file__).parent)
    except (OSError,ValueError):
        print('V475_IRQ_BOOTSTRAP installed=0');return 1
    print('V475_IRQ_BOOTSTRAP installed=1 native_mask=1 ios_scheduler=0');return 0
if __name__=='__main__':raise SystemExit(main())
