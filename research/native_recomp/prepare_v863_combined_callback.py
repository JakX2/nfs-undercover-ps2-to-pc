#!/usr/bin/env python3
"""Join the original changed wireless return with the V850 original epilogue.

Install only after V861. No successful device stub, no fresh CPU state,
no new dispatch of an unknown indirect callback.
"""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v850_callback_return import install as install_return,patch_label as return_label,LABEL_TICK,BLOCK_END
from prepare_v807_callback_prefix import SI

GATED=re.compile(r'(?m)^    if\(!undercover::wii::v847::active\(\)\) \{ (undercover::wii::(?:v768|v726)::restore_before\(ctx,[^\n]+\);) \}\n')

def patch_label(s,pc,w,role='before'):
    if role!='restore':return return_label(s,pc,w,role)
    hits=list(LABEL_TICK(pc,w).finditer(s))
    if len(hits)!=1:raise ValueError('combined return label')
    start=hits[0].end();stop=BLOCK_END.search(s,start);end=stop.start() if stop else len(s)
    block=s[start:end]
    guarded=list(GATED.finditer(block))
    if len(guarded)>1:raise ValueError('combined restore hooks')
    if not guarded:return return_label(s,pc,w,role)
    if block.count('undercover::wii::v847::before(ctx,')!=1:raise ValueError('combined restore owner')
    # Temporarily expose the exact older restore hook for V850's checks.
    g=guarded[0];legacy='    '+g[1]+'\n'
    restored=s[:start]+block[:g.start()]+legacy+block[g.end():]+s[end:]
    out=return_label(restored,pc,w,role)
    old='    if(!undercover::wii::v850::active()) '+g[1]+'\n'
    new='    if(!undercover::wii::v847::active()&&!undercover::wii::v850::active()) '+g[1]+'\n'
    # Replace inside this specific label, not another occurrence in a shard.
    return replace_exact(out,old,new)

def patch_wrapper(s):
    a='#include "wii_wireless_write_binding_v861.h"'
    s=replace_exact(s,a,a+'\n#include "wii_callback_return_binding_v850.h"')
    a='    v861::after(c,old,route);\n    finish(c);'
    s=replace_exact(s,a,r'''    v861::after(c,old,route);
    if(route.stage()==2u&&route.ordinal()==3u&&v850::enabled()){
        if(route.changed()&&(!v861::active()||!v861::device.held()))v861::reject(4);
        // V861 already emitted the verified write marker; do not emit a
        // second V847 terminal. The unchanged lane still needs its marker.
        if(route.changed()){v850::start(c,pc,w,true);return;}
        std::cout<<std::dec<<"V847_WIRELESS_RESULT ordinal="<<route.ordinal()
            <<" changed=0 visits="<<route.visits()<<" writes="<<route.writes()
            <<" returned=1 lock_entry=0 exi_executed=0 callback_return=0 boot_verified=0"<<std::endl;
        v850::start(c,pc,w,true);return;
    }
    finish(c);''')
    # V861's original unchanged wireless branch returns before v861::after.
    # Hand off at its real resume tick, not the legacy diagnostic stop.
    s=replace_exact(s,'template<class C>void finish(C& c){',
                       'template<class C>void finish(C& c,uint32_t pc,uint32_t w){')
    a='        std::_Exit(0);'
    s=replace_exact(s,a,
        '        if(route.stage()==2u&&route.ordinal()==3u&&!route.changed()&&v850::enabled()){v850::start(c,pc,w,true);return;}\n'+a)
    s=replace_exact(s,'    finish(c);return true;',
                       '    finish(c,pc,0u);return true;')
    s=replace_exact(s,'    finish(c);','    finish(c,pc,w);')
    # Both original exits remain when V850 is disabled.
    return s

def patch_write(s):
    a='<<" payload=1 abi=1 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','if(!continue_callback())std::_Exit(0);'))

def patch_ack(s):
    a='    if(v847::active()){\n'
    s=replace_exact(s,a,'    if(v850::active())return v850::poll(c);\n'+a)
    a='if(v847::observe(a,c))return;'
    s=replace_exact(s,a,'if(v850::observe(a,c))return;'+a)
    a='template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){'
    return replace_exact(s,a,a+'\n    if(v850::active())v850::reject(7);')

def patch_binding(s):
    a='#include "wii_callback_dispatch_device_v808.h"'
    s=replace_exact(s,a,a+'\n#include "wii_wireless_write_binding_v861.h"')
    # Guard both hardware states throughout every native suffix/return step.
    s=s.replace('si_transfer_device.held_now()','held(c)')
    a='template<class C>void capture(C& c,uint32_t pc,uint32_t w,unsigned ordinal){'
    s=replace_exact(s,a,r'''template<class C>bool held(C& c){
    if(!si_transfer_device.held_now())return false;
    if(!v861::active())return true;
    const auto* profile=ExiProfileSession::current();
    return profile&&v861::device.held()&&v861::payload(c)==profile->sram();
}
template<class C>void capture(C& c,uint32_t pc,uint32_t w,unsigned ordinal){''')
    a='    if(!si_transfer_device.after_return_at(c.inst_count))reject(6);'
    s=replace_exact(s,a,a+'\n    if(v861::active()&&!v861::device.observe(c.inst_count))v861::reject(5);')
    a='    if(!returned||!caller||!observe_completed_callback_dispatch(si_transfer_device,c.inst_count)||'
    s=replace_exact(s,a,'    if(v861::active()&&!v861::device.observe_dispatch(c.inst_count))v861::reject(5);\n'+a)
    a='    if(!returned||!caller||!si_transfer_device.after_return_at(c.inst_count)||'
    return replace_exact(s,a,'    if(v861::active()&&!v861::device.observe(c.inst_count))v861::reject(5);\n'+a)

def install(dol,elf,root,host):
    dest=root/'nWiiRuntime/include/undercover'
    write=dest/'wii_wireless_write_binding_v861.h'
    if write.is_symlink() or not write.is_file():raise ValueError('combined write predecessor')
    s=write.read_text()
    a='inline bool active(){return device.stage()!=0u;}'
    s=replace_exact(s,a,a+r'''
inline bool continue_callback(){
    const char* v=std::getenv("UNDERCOVER_V850_CALLBACK_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0';
}''')
    s=patch_write(s)
    install_return(dol,elf,root,host,label_patch=patch_label,wrapper_patch=patch_wrapper,ack_patch=patch_ack,binding_patch=patch_binding)
    write.write_text(s)
    print('V863_COMBINED_CALLBACK_ROUTE installed=1 write=1 suffix=1 outer_dispatch=1 default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('combined return label','combined restore hooks','combined restore owner','combined write predecessor','source seam','return role','return label','return scheduler','return duplicate hook','return shared hook','return handler hook','return tick','return geometry','return caller','return overlap','return tree','return owner','return edge','return destination','shared time label','shared time scheduler order','native IPC label identity','native IPC coverage','native IPC dispatch','resume dispatcher identity')
        print('V863_COMBINED_CALLBACK_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
