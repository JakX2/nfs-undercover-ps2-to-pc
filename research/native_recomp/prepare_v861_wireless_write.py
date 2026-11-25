#!/usr/bin/env python3
"""Private opt-in extension of V847 through genuine EXI write and setter return."""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from prepare_owner_wireless_return_v837 import plan,H,J
from prepare_owner_scheduler_v722 import reachable
from make_start_to_exi_transaction_v56 import IMM,SYNC,SELECT,DESELECT,HWREV,IRQMASK
from audit_callback_frontiers_v799 import call_sites
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v813_callback_time import verify_order
from prepare_v807_callback_prefix import SI
from prepare_v850_callback_return import LABEL_TICK,BLOCK_END

def render(roots,rules,revision,immex,unlock,L):
    hx=lambda x:f'0x{x:08x}u'
    h='#pragma once\n#include "wii_wireless_wrapper_v844.h"\nnamespace undercover::wii::v861 {\n'
    for i,(a,ws) in enumerate(roots.items()):
        h+=f'inline constexpr std::array<uint32_t,{len(ws)}> words_{i}{{'+','.join(map(hx,ws))+'};\n'
    h+=f'inline constexpr std::array<WirelessCode,{len(roots)}> code{{{{'+','.join('WirelessCode{'+hx(a)+f',words_{i}'+'}' for i,a in enumerate(roots))+'}};\n'
    h+=f'inline constexpr std::array<WirelessRestoreRule,{len(rules)}> restores{{{{'+','.join('WirelessRestoreRule{'+hx(a)+f',{n}u,{b}u,{d}'+'}' for a,n,b,d in rules)+'}};\n'
    h+='inline constexpr WirelessWriteExtension extension{code,restores,'+','.join(map(hx,(HWREV,revision,0x806f1560)))+'};\n'
    vals={'lock':L,'mask_helper':IRQMASK,'select':SELECT,'imm':IMM,'sync':SYNC,'immex':immex,'deselect':DESELECT,'unlock':unlock,'sram':0x806f52c0}
    return h+'inline constexpr uint32_t '+','.join(k+'='+hx(v) for k,v in vals.items())+';\n}\n'

# Only earlier audited route hooks are gated; all native scheduler calls
# and ordinary instruction bodies remain exactly where the emitter put them.
OLD=re.compile(r'(?m)^    (?:(?:if\(!undercover::wii::v(?:807|850)::active\(\)\) )?undercover::wii::(?:v680::before|v768::(?:save_before|restore_before)|v726::restore_before|v807::before|v786::before|v767::before)\(ctx,[^\n]+\);)\n')
SCHED=re.compile(r'(?:    ctx\.[a-z_]+_instruction_boundary\(\);\n)*')
def patch_label(s,pc,w):
    hits=list(LABEL_TICK(pc,w).finditer(s))
    if len(hits)!=1:raise ValueError('write label')
    start=hits[0].end();stop=BLOCK_END.search(s,start);end=stop.start() if stop else len(s)
    block=s[start:end]
    if block.count(SI)!=1:raise ValueError('write scheduler')
    before=block[:block.index(SI)+len(SI)]
    if not SCHED.fullmatch(OLD.sub('',before)):raise ValueError('write scheduler')
    if 'undercover::wii::v847::before(ctx,' in block:raise ValueError('write duplicate hook')
    if re.search(r'(?m)^    (?:if\([^\n]+\) )?undercover::wii::',OLD.sub('',block)):raise ValueError('write unknown shared hook')
    block=OLD.sub(lambda m:'    if(!undercover::wii::v847::active()) { '+m[0].strip()+' }\n',block)
    at=block.index(SI)+len(SI)
    block=block[:at]+f'    undercover::wii::v847::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+block[at:]
    return s[:start]+block+s[end:]

def patch_wrapper(s):
    a='#include "wii_postack_transfer_device_v771.h"'
    s=replace_exact(s,a,a+'\n#include "wii_wireless_write_binding_v861.h"')
    a='    std::cout<<"V847_WIRELESS_ENTRY'
    s=replace_exact(s,a,'    v861::start(c,route);\n'+a)
    s=replace_exact(s,'inline void finish(){','template<class C>void finish(C& c){')
    a='        std::_Exit(0);'
    s=replace_exact(s,a,'        if(route.stage()==3u&&v861::active()){\n            if(!route.continue_write(c,v861::extension,si_transfer_device.held_now()))reject(2);\n            return;\n        }\n'+a)
    a='    finish();return true;'
    s=replace_exact(s,a,'    v861::entry(c,pc);\n    finish(c);return true;')
    a='    if(!si_transfer_device.after_return_at(c.inst_count)||!route.before(c,pc,w,si_transfer_device.held_now()))reject(4);\n    finish();'
    return replace_exact(s,a,r'''    if(!si_transfer_device.after_return_at(c.inst_count))reject(4);
    if(v861::active()&&!v861::device.observe(c.inst_count))v861::reject(5);
    const auto old=route.returning_root();
    if(!route.before(c,pc,w,si_transfer_device.held_now()))reject(4);
    v861::after(c,old,route);
    finish(c);''')

def patch_ack(s):
    a='    if(v847::active())v847::reject(3);'
    return replace_exact(s,a,r'''    if(v847::active()){
        if(!v847::route.extended()||!v847::route.poll(c,si_transfer_device.held_now()))v847::reject(3);
        return false;
    }''')

def install(dol,elf,root,host):
    base,rules,aliases,revision,immex,unlock,shared=plan(dol,elf)
    roots,A,B,U,L,guards=base
    existing={A,B,U,DISABLE,RESTORE};excluded={H,J,*guards}
    ext={a:ws for a,ws in roots.items() if a not in existing|excluded}
    if L not in ext or HWREV not in ext or not 1<=len(ext)<=32:raise ValueError('write geometry')
    rules=list({r[0]:r for r in rules}.values())
    if any(r[0] not in ext for r in rules):raise ValueError('write restore')
    for a,ws in ext.items():
        if tuple(ws)!=tuple(exact(dol,elf,a,len(ws))):raise ValueError('write original words')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(f.is_symlink() or not f.is_file() or f.stat().st_size>64*1024*1024 for f in paths+[main]):
        raise ValueError('write tree')
    src={f:f.read_text() for f in paths};outer=main.read_text();changes={};labels=edges=0
    for a,ws in ext.items():
        owners=[f for f,s in src.items() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('write owner')
        f=owners[0];s=changes.get(f,src[f]);body=exact_function(s,a)
        expected={pc:(a,ws[(pc-a)//4]) for pc in reachable(a,ws)}
        audit_native([body],outer,expected)
        for pc,k,dst in call_sites(a,ws):
            if k==2 and a==unlock:
                verify_indirect(body,pc)
            elif k==1 and dst in roots and dst not in (H,J):
                verify_direct(body,pc,dst)
            else:raise ValueError('write edge')
            edges+=1
        out=body
        for pc,(_,w) in sorted(expected.items()):
            out=patch_label(out,pc,w)
            verify_order(out,pc,w,'v847');labels+=1
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_wireless_wrapper_binding_v847.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[f]=s
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_wireless_sram_write_v857.h','wii_sram_write_witness_v818.h','wii_wireless_profile_trace_v859.h','wii_wireless_write_binding_v861.h')}
    files[dest/'v861_private_wireless_write.h']=render(ext,rules,revision,immex,unlock,L)
    if dest.is_symlink() or any(f.exists() or f.is_symlink() for f in files):raise ValueError('write destination')
    for n,fn in {'wii_wireless_wrapper_binding_v847.h':patch_wrapper,'wii_si_ack_binding_v672.h':patch_ack}.items():
        f=dest/n
        if f.is_symlink() or not f.is_file():raise ValueError('write destination')
        files[f]=fn(f.read_text())
    for f,s in {**changes,**files}.items():f.write_text(s)
    print(f'V861_WIRELESS_WRITE_ROUTE installed=1 roots={len(ext)} labels={labels} edges={edges} restore_aliases={len(rules)} default_disabled=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('write label','write scheduler','write duplicate hook','write unknown shared hook','write geometry','write restore','write original words','write tree','write owner','write edge','write destination','source seam','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','shared time label','shared time scheduler order','indirect label','indirect LR','indirect dispatch','indirect fallback')
        print('V861_WIRELESS_WRITE_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
