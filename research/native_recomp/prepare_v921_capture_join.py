#!/usr/bin/env python3
"""Join the actual V751 snapshot to the original V920 return."""
import argparse
from pathlib import Path
from prepare_v419_full_start import replace_exact

def patch_capture(s):
    a='#include "wii_cold_return_capture_v741.h"'
    s=replace_exact(s,a,a+'\n#include "wii_saved_context_join_v921.h"')
    a='            std::cout<<"V751_CAPTURE_STAGE n=2"'
    return replace_exact(s,a,'            if(!v921::join.attach(c,capture.witness(),ColdExternalEntry::Thread))reject(11);\n'+a)

def patch_return(s):
    a='#include "v920_private_handler_resume.h"'
    s=replace_exact(s,a,a+'\n#include "wii_saved_context_join_v921.h"')
    a='    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;'
    return replace_exact(s,a,a+'''
    if(!v921::join.returned(c,v921::join.context()))reject(6);
    std::cout<<"V921_SAVED_CONTEXT_RETURN original_snapshot=1 saved_gprs=32 special=6 same_cpu=1 unchanged=1 rfi_return=0 boot_verified=0"<<std::endl;''')

def install(root,host):
    dest=root/'nWiiRuntime/include/undercover'
    a=dest/'wii_external_entry_binding_v663.h';b=dest/'wii_handler_suffix_binding_v868.h';h=dest/'wii_saved_context_join_v921.h'
    if dest.is_symlink() or any(p.is_symlink() or not p.is_file() for p in (a,b)) or h.exists() or h.is_symlink():raise ValueError('destination')
    files={a:patch_capture(a.read_text()),b:patch_return(b.read_text()),h:(host/h.name).read_text()}
    for p,s in files.items():p.write_text(s)
    print('V921_CAPTURE_JOIN_ROUTE installed=1 pre_exception=1 saved_frame=1 handler_return=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:install(a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V921_CAPTURE_JOIN_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
