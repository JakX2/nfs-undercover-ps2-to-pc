#!/usr/bin/env python3
"""Install explicit SI host-profile selection after V512 MMIO and V515 ticks."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
INCLUDE='#include "undercover/wii_si_binding_v512.h"'
DECL='    std::optional<undercover::wii::SiBinding> si_binding;'
BIND='        si_binding.emplace(*si_controller);'
PAIRS=((INCLUDE,INCLUDE+'\n#include "undercover/wii_si_profile_v518.h"'),
       (DECL,DECL+'\n    std::optional<undercover::wii::SiProfileSession> si_session;\n    const char* si_profile=std::getenv("UNDERCOVER_V518_SI_PROFILE");'),
       (BIND,BIND+'\n        if(si_profile&&*si_profile)si_session.emplace(*si_controller,undercover::wii::SiHostProfile::load(si_profile));'),
       ('    if(const char* enabled=std::getenv("UNDERCOVER_V512_SI");enabled&&enabled[0]==\'1\'&&enabled[1]==\'\\0\'){',
        '''    if(si_profile&&*si_profile){
        const char* enabled=std::getenv("UNDERCOVER_V512_SI");
        if(!enabled||enabled[0]!='1'||enabled[1]!='\\0')std::_Exit(102);
    }
    if(const char* enabled=std::getenv("UNDERCOVER_V512_SI");enabled&&enabled[0]=='1'&&enabled[1]=='\\0'){'''))
def apply(root,host):
    rt=root/'nWiiRuntime';dest=rt/'include/undercover';main=rt/'src/core/main.cpp'
    header=dest/'wii_si_profile_v518.h'
    if any(p.is_symlink() for p in (dest,main,header)) or not (dest/'wii_si_type_scheduler_v514.h').is_file():
        raise ValueError('predecessor')
    data=(host/header.name).read_bytes()
    if header.exists() and header.read_bytes()!=data:raise ValueError('header conflict')
    updates={main:rewrite(main.read_text(encoding='utf-8'),PAIRS).encode(),header:data}
    for p,c in updates.items():
        if not p.exists() or p.read_bytes()!=c:p.write_bytes(c)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V518_SI_PROFILE installed=0');return 1
    print('V518_SI_PROFILE installed=1 opt_in=1 type_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
