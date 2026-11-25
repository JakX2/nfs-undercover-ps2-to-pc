#!/usr/bin/env python3
"""Complete original fourth-call return after the existing private V768 installation."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_transfer_v765 import plan
from prepare_owner_pair_v753 import plan as pair
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v768_transfer_prefix import expectations as prefix_expectations
HOOK=re.compile(r'(?m)^    undercover::wii::(?:v768::(?:before|save_before|restore_before)|v709::before|v672::before)\(ctx,[^\n]+\);\n')
SI='    ctx.si_instruction_boundary();\n'
def move_hooks(s):
    # Earlier installations instrument immediately after ++inst_count.
    # The real scheduler must advance before the new observer sees a tick.
    # Refuse if a target label lacks the exact existing scheduler boundary.
    matches=list(HOOK.finditer(s))
    for m in reversed(matches):
        end=s.find(SI,m.end(),m.end()+2048)
        if end<0 or '\nloc_' in s[m.end():end] or HOOK.search(s,m.end(),end):raise ValueError('scheduler hook ordering')
        middle=s[m.end():end]
        if not re.fullmatch(r'(?:    (?:ctx\.[a-z_]+_instruction_boundary\(\)|undercover::wii::[a-zA-Z0-9_:]+\(ctx,[^\n]+\));\n)*',middle):
            raise ValueError('scheduler hook intervening code')
        tail=end+len(SI)
        s=s[:m.start()]+s[m.end():tail]+m[0]+s[tail:]
    return s,len(matches)
def patch_si(s):
    a='#include "wii_si_completion_ack_v668.h"'
    s=replace_exact(s,a,a+'\n#include "wii_postack_transfer_device_v771.h"\n#include "wii_si_type_scheduler_v514.h"')
    # The device header is independent of the SI binding; the global is
    # declared there once. Keep the previous ACK path entirely intact.
    a='    static bool active()noexcept{return active_!=nullptr;}'
    s=replace_exact(s,a,a+r'''
    static bool begin_transfer_device(const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
                                      const uint64_t& tick,unsigned channel,bool idle){
        if(!active_)return false;
        const auto cfg=SiTickBinding::configuration(active_->controller_,channel,tick);
        return cfg&&si_transfer_device.begin(active_->controller_,cause,mask,si_completion_ack_trace,tick,channel,idle,cfg->response,cfg->latency);
    }''')
    a='        try{return si_completion_ack_trace.read(active_->controller_,off);}'
    s=replace_exact(s,a,r'''        if(si_transfer_device.stage()){
            uint32_t value=0;
            if(!si_transfer_device.read(active_->controller_,off,value)){
                std::cout<<"V777_TRANSFER_MMIO_INVALID kind=1 reason="<<si_transfer_device.failure()<<std::endl;std::_Exit(126);
            }
            return value;
        }
'''+a)
    a='try{si_completion_ack_trace.write(active_->controller_,*off,value);}'
    return replace_exact(s,a,r'''try{
            if(si_transfer_device.stage()){
                if(!si_transfer_device.write(active_->controller_,*off,value)){
                    std::cout<<"V777_TRANSFER_MMIO_INVALID kind=2 reason="<<si_transfer_device.failure()<<std::endl;std::_Exit(126);
                }
            }else si_completion_ack_trace.write(active_->controller_,*off,value);
        }''')
def patch_ack(s):
    a='    if(!si_completion_ack_trace.before(pc,word))reject(3);'
    return replace_exact(s,a,'    if(v768::active()){v768::handler_return(c,pc,word);return;}\n'+a)
def render(dol,elf):
    roots,C,D,Q,S,R,edges=plan(dol,elf)
    _,_,_,_,site,_,_=prefix_expectations(dol,elf)
    n,*_=geometry(dol,elf);_,_,branch=edge(HANDLER,exact(dol,elf,HANDLER,n),4)
    _,_,count,sb,rb,disp,_=pair(dol,elf,4)
    if count!=6:raise ValueError('restore count')
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    def call(i):
        pc,a=edges[i];return (pc,a,a+4*len(roots[a]),roots[C][(pc-C)//4])
    h='#pragma once\n#include "wii_transfer_return_v774.h"\nnamespace undercover::wii::v768 {\n'
    h+='inline constexpr TransferReturnExpectation expected{'+fmt((site,C,C+432,branch,roots[C][0]))+','
    h+='SiHelperExpectation{'+fmt(call(0))+f',26u,{sb}u,{disp}'+'},'
    h+='PostAckLeafExpectation{'+fmt(call(1))+',1u},0x80619a60u,{{'
    h+=','.join('PostAckLeafExpectation{'+fmt(call(i))+',3u}' for i in (2,3))+'}},'
    pc,a=edges[4];h+='GprRestoreExpectation{'+fmt((pc,a,roots[C][(pc-C)//4]))+f',26u,{rb}u,{disp}'+'}};\n}\n'
    return roots,C,D,Q,S,R,site,h
def patch_restore(s,a,words):
    body=exact_function(s,a);out=body
    for i,w in enumerate(words):
        pc=a+4*i
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        if len(pat.findall(out))!=1:raise ValueError('restore label identity')
        out=pat.sub(lambda m:m[0]+f'    undercover::wii::v768::restore_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
    s=replace_exact(s,body,out)
    inc='#include "undercover/wii_transfer_prefix_binding_v768.h"'
    return s if inc in s else replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
def install(dol,elf,root,host):
    roots,C,D,Q,S,R,site,header=render(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('private tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    owners=[(p,exact_function(s,R)) for p,s in src.items() if owns_root(s,R)]
    if len(owners)!=1 or sum(entry_count(s,R) for s in src.values())!=1:raise ValueError('restore entry')
    p,body=owners[0];expected={R+4*i:(R,w) for i,w in enumerate(roots[R])}
    if audit_native([body],outer,expected)!=len(expected):raise ValueError('restore coverage')
    src[p]=patch_restore(src[p],R,roots[R])
    # The earlier exact original handler and leaf audits already passed.
    # Move only the authenticated route hooks; do not add a scheduler tick.
    changes={};count=0
    for p,s in src.items():
        out,n=move_hooks(s)
        if n:changes[p]=out;count+=n
    if count<150:raise ValueError('route hook coverage')
    dest=root/'nWiiRuntime/include/undercover'
    names=('wii_transfer_return_v774.h','wii_postack_transfer_device_v771.h','wii_si_follow_on_v750.h','wii_gpr_restore_v736.h')
    files={dest/n:(host/n).read_text() for n in names}
    f=dest/'wii_postack_transfer_device_v771.h'
    files[f]=replace_exact(files[f],'\n};\n}\n','\n};\ninline thread_local PostAckTransferDevice si_transfer_device{};\n}\n')
    files[dest/'v777_private_transfer_return.h']=header
    b=dest/'wii_transfer_prefix_binding_v768.h';si=dest/'wii_si_binding_v512.h';ack=dest/'wii_si_ack_binding_v672.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() or not p.is_file() for p in (b,si,ack)):raise ValueError('destination')
    files[b]=(host/'wii_transfer_return_binding_v777.h').read_text()
    files[si]=patch_si(si.read_text());files[ack]=patch_ack(ack.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V777_TRANSFER_ROUTE installed=1 restore_labels={len(expected)} scheduler_ordered={count} original_return=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        safe=('restore count','restore label identity','private tree','restore entry','restore coverage','scheduler hook ordering','scheduler hook intervening code','route hook coverage','destination','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch')
        print('V777_TRANSFER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
