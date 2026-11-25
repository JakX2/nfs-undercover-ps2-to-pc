#!/usr/bin/env python3
"""Install opt-in live pre-exception snapshot and saved-frame verification."""
import argparse
from pathlib import Path
from prepare_v419_full_start import replace_exact
def patch(s):
    a='#include "v663_private_external_expectations.h"'
    s=replace_exact(s,a,a+'\n#include "wii_cold_return_capture_v741.h"')
    a='inline thread_local ColdExternalEntry route(expected);'
    s=replace_exact(s,a,a+r'''
inline thread_local ColdReturnCapture capture;
inline bool capture_enabled(){const char* v=std::getenv("UNDERCOVER_V751_CAPTURE");return v&&v[0]=='1'&&v[1]=='\0';}
''')
    a='    bool entered=route.poll(c,pi_intsr.load(),pi_intmr.load());'
    s=replace_exact(s,a,r'''    bool entered=capture_enabled()?route.poll(c,pi_intsr.load(),pi_intmr.load(),capture):
                                   route.poll(c,pi_intsr.load(),pi_intmr.load());
    if(entered&&capture_enabled()){
        if(capture.witness().stage()!=1)reject(10);
        std::cout<<"V751_CAPTURE_STAGE n=1"<<std::endl;
    }''')
    a='    if(route.stage()==6){'
    s=replace_exact(s,a,a+r'''
        if(capture_enabled()){
            const auto saved=capture.witness().saved_integer(c,ColdExternalEntry::Thread);
            if(!saved.ok()){
                std::cout<<"V751_CAPTURE_INVALID valid="<<unsigned(saved.valid)<<" gprs="<<saved.gpr_mismatches
                         <<" special="<<saved.special_mask<<std::endl;reject(11);
            }
            std::cout<<"V751_CAPTURE_STAGE n=2"<<std::endl;
            std::cout<<"V751_CAPTURE_RESULT live_snapshot=1 saved_gprs=32 special=6 rfi_return=0 boot_verified=0"<<std::endl;
        }''')
    return s
def install(root,host):
    dest=root/'nWiiRuntime/include/undercover';bind=dest/'wii_external_entry_binding_v663.h'
    files={dest/n:(host/n).read_text() for n in ('wii_external_return_v706.h','wii_cold_return_capture_v741.h')}
    if dest.is_symlink() or bind.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    files[bind]=patch(bind.read_text())
    for p,s in files.items():p.write_text(s)
    print('V751_CAPTURE_ROUTE installed=1 pre_entry=1 saved_frame=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:install(a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):
        print('V751_CAPTURE_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
