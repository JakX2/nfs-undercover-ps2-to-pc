#!/usr/bin/env python3
"""Opt-in pre-guest lowmem profile for the independently established MI mapping."""
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
INCLUDE='#include "runtime/hw/hw.h"'
ANCHOR='    poke_global(0x80003158, 0x00000023);\n  }'
PAIRS=((INCLUDE,INCLUDE+'\n#include "undercover/wii_cold_mapping_v612.h"'),
       (ANCHOR,ANCHOR+'''
  if (const char* profile=std::getenv("UNDERCOVER_V612_MAPPING"); profile) {
    const char* bounded=std::getenv("UNDERCOVER_V419_START");
    const char* mi=std::getenv("UNDERCOVER_V591_MI");
    if(profile[0]!='1'||profile[1]!='\\0'||!bounded||bounded[0]!='1'||bounded[1]!='\\0'||
       !mi||mi[0]!='1'||mi[1]!='\\0'||
       !undercover::wii::ColdMappingProfile::install(ctx->mmu,exe.sections,!is_gc,!vdisc.valid())){
      std::cout<<"V612_MAPPING_PROFILE accepted=0"<<std::endl;std::_Exit(118);
    }
    std::cout<<"V612_MAPPING_PROFILE accepted=1 mem1=24 mem2=64 mapped_mem2=52 ipc_kib=512 synthetic=1"<<std::endl;
  }'''))
# The include itself is shared with existing startup installers. Append after
# their edits; exact reversible patch checks preserve all of their additions.
def apply(root,host):
    p=root/'nWiiRuntime/src/core/main.cpp'
    dest=root/'nWiiRuntime/include/undercover/wii_cold_mapping_v612.h'
    if any(x.is_symlink() for x in (p,dest,dest.parent)):raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old,PAIRS)
    data=(host/dest.name).read_bytes()
    if dest.exists() and dest.read_bytes()!=data:raise ValueError('header conflict')
    if new==old and not dest.is_file():raise ValueError('partial installation')
    if new!=old:
        dest.write_bytes(data);p.write_text(new,encoding='utf-8')
