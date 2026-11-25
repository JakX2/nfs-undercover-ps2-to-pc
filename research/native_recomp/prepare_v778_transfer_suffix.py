#!/usr/bin/env python3
"""Resume the original handler after an authenticated transfer return.

Stop before the next unverified linked call or handler BLR. Do not admit
any second MMIO operation, new transaction, context restore or IRQ entry.
"""
import argparse
from pathlib import Path
from prepare_v419_full_start import replace_exact
def patch_transfer(s):
    a='inline bool active(){return route.stage()!=0;}'
    s=replace_exact(s,a,a+r'''
inline bool returned_active(){return route.stage()==4;}
inline bool continue_suffix(){const char* v=std::getenv("UNDERCOVER_V778_TRANSFER_SUFFIX");return v&&v[0]=='1'&&v[1]=='\0';}
''')
    a='template<class C>void handler_return(C& c,uint32_t pc,uint32_t w){'
    s=replace_exact(s,a,r'''template<class C>void suffix_before(C& c){
    if(!returned_active()||!si_transfer_device.after_return_at(c.inst_count))reject(7);
}
'''+a)
    a='    std::_Exit(0);\n}\n}'
    return replace_exact(s,a,'    if(!continue_suffix())std::_Exit(0);\n}\n}')
def patch_handler(s):
    a='inline bool held(){return si_completion_ack_trace.postack_held();}'
    s=replace_exact(s,a,'inline bool held(){return v768::returned_active()?si_transfer_device.held_now():si_completion_ack_trace.postack_held();}')
    a='        if(v742::continue_suffix()&&v742::route.stage()==4&&witness.failure()==4&&'
    s=replace_exact(s,a,r'''        if(v768::returned_active()&&v768::continue_suffix()&&witness.failure()==4&&
           ordinal>=5&&ordinal<=12&&kind>=1&&kind<=2){
            std::cout<<std::dec<<"V778_NEXT_BOUNDARY ordinal="<<ordinal<<" kind="<<kind
                <<" visits="<<witness.visits()<<" polls="<<witness.polls()
                <<" follow="<<si_transfer_device.follow_stage()<<" executed=0"<<std::endl;
            reject(3);
        }
'''+a)
    a='    if(witness.stage()==3)std::cout<<"V726_HANDLER_STAGE n=3"<<std::endl;'
    s=replace_exact(s,a,r'''    if(v768::returned_active()&&witness.stage()==3){
        if(!v768::continue_suffix()||!held())reject(3);
        std::cout<<std::dec<<"V778_HANDLER_BLR abi=1 visits="<<witness.visits()<<" polls="<<witness.polls()
            <<" follow="<<si_transfer_device.follow_stage()<<" executed=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
'''+a)
    a='witness.stage()==2?si_completion_ack_trace.native_branch_poll(c.pc):held()'
    return replace_exact(s,a,'v768::returned_active()?held():(witness.stage()==2?si_completion_ack_trace.native_branch_poll(c.pc):held())')
def patch_ack(s):
    a='    if(v768::active()){v768::handler_return(c,pc,word);return;}'
    s=replace_exact(s,a,r'''    if(v768::active()){
        if(!v768::returned_active()){
            v768::handler_return(c,pc,word);
            if(!v726::witness.transfer_returned(c,pc,v768::route.total(),v726::held()))v726::reject(3);
        }else v768::suffix_before(c);
        v726::before(c,pc,word,ordinal,kind);return;
    }''')
    a='    if(v768::active())return v768::poll(c);'
    s=replace_exact(s,a,'    if(v768::active()&&!v768::returned_active())return v768::poll(c);')
    # After transfer, any native function entry remains forbidden by the
    # old observer (only handler internal labels are permitted).
    return s
def install(root):
    dest=root/'nWiiRuntime/include/undercover'
    patches={'wii_transfer_prefix_binding_v768.h':patch_transfer,
             'wii_si_handler_return_binding_v726.h':patch_handler,
             'wii_si_ack_binding_v672.h':patch_ack}
    files={}
    for n,fn in patches.items():
        p=dest/n
        if dest.is_symlink() or p.is_symlink() or not p.is_file():raise ValueError('destination')
        files[p]=fn(p.read_text())
    for p,s in files.items():p.write_text(s)
    print('V778_SUFFIX_ROUTE installed=1 exact_transfer_return=1 handler_witness=1 device_held=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:install(a.generated)
    except (OSError,ValueError,UnicodeError):print('V778_SUFFIX_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
