#!/usr/bin/env python3
"""Install the authenticated held pending epilogue and third vector route."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v767_live_epilogue import geometry as ep_geometry
from prepare_v1146_postalarm_handler_return import geometry_return,render as render_return
from prepare_v667_si_dispatch import DISPATCH,exact,DISABLE,RESTORE
from prepare_v663_external_entry import TRAMP
from audit_v662_external_overlay import VECTOR,expected as vector_words
from make_private_elf_symbol_map import parse_functions
from prepare_v1141_postalarm_handler import block_at
from prepare_v1097_after_alarm import ACTIVE,SI,fmt,inherited_hooks
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v1029_third_transfer import replace_body,include_once

NEW='undercover::wii::v958::held_epilogue_active()'
ACK='undercover::wii::v958::active()'

def patch_label(body,pc,w,vector=False,shared=False):
    block=block_at(body,pc,w)
    tick='    ++ctx.inst_count;\n';args=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    if block.count(tick)!=1 or block.count(SI)!=1 or block.index(tick)>block.index(SI) or NEW in block:
        raise ValueError('held epilogue tick')
    legacy=f'undercover::wii::v922::{"second_before" if vector else "before"}({args});'
    plain='    '+legacy+'\n';gated=f'    if(!{ACK}) '+legacy+'\n'
    # Match the owner call, not a v922::active() predicate on an
    # independent V709 observer. The real shared leaves contain both.
    legacy_lines=[s for s in block.splitlines(keepends=True) if any(
        name in s for name in ('v922::before(','v922::second_before(','v922::second_dispatch_before('))]
    if legacy_lines not in ([plain],[gated]) or (vector and legacy_lines!=[plain]) or (shared and legacy_lines!=[gated]):
        raise ValueError('held epilogue legacy')
    old=legacy_lines[0]
    if block.count(old)!=1 or block.index(old)<block.index(SI):raise ValueError('held epilogue legacy')
    current=f'undercover::wii::v958::before({args},false);'
    current_line='    '+current+'\n'
    hits=re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block)
    observed=''.join(hits)
    if shared:
        allowed=set(inherited_hooks(pc,w).values())|{f'    if({ACTIVE}) '+current+'\n'}
        if observed not in allowed or block.count(observed)!=1 or block.index(observed)<block.index(SI):
            raise ValueError('held epilogue shared')
        # Already covered by the V958 owner and its postalarm-active guard.
        if observed!=current_line and ACTIVE not in observed:
            raise ValueError('held epilogue shared')
        if not observed.startswith(current_line) and ('else ' in observed and 'true);' not in observed):
            raise ValueError('held epilogue shared')
    else:
        if hits or legacy_lines!=[plain]:raise ValueError('held epilogue shared')
        # The old observer is after the same native SI tick. Keep it in
        # the exact opposite branch; do not add an instruction or tick.
        block=block.replace(plain,f'    if({NEW}) '+current+'\n    else '+plain.lstrip(),1)
    original=block_at(body,pc,w)
    if body.count(original)!=1:raise ValueError('held epilogue block')
    return body.replace(original,block,1)

def metadata(dol,elf):
    call,R,dispatch_resume,restore,tail,w,_,_,_=geometry_return(dol,elf)
    ep,j,resume,h,edges,entries=ep_geometry(dol,elf)
    if j!=dispatch_resume or ep.get(j)!=(DISPATCH,w) or resume==j:
        raise ValueError('held epilogue geometry')
    ep=dict(ep);ep.pop(resume)
    vec=vector_words(dol)
    if len(vec)!=38 or parse_functions(elf).get(TRAMP)!=80:raise ValueError('held epilogue vector')
    tramp=exact(dol,elf,TRAMP,20);dw=exact(dol,elf,DISPATCH,1)[0]
    vh='#pragma once\n#include "wii_second_vector_v939.h"\nnamespace undercover::wii::v922 {\n'
    vh+='inline constexpr std::array<uint32_t,38> second_vector_words{'+fmt(vec)+'};\n'
    vh+='inline constexpr std::array<uint32_t,20> second_trampoline_words{'+fmt(tramp)+'};\n'
    vh+='inline constexpr SecondVectorExpectation second_expected{'+fmt((TRAMP,DISPATCH,0x806f5318,dw))+',second_vector_words,second_trampoline_words};\n}\n'
    raw=struct.pack('>38I',*vec)
    eh='#pragma once\n#include "v616_private_irq_expectations.h"\n#include "wii_cold_external_entry_v663.h"\n'
    eh+='namespace undercover::wii::v663 {\ninline constexpr ColdExternalExpectations expected{v616::expected_irq,{'
    eh+=','.join(map(str,raw))+'},'+fmt((tramp[0],dw))+'};\n}\n'
    vectors={VECTOR+4*i:(VECTOR,x) for i,x in enumerate(vec)}
    vectors.update({TRAMP+4*i:(TRAMP,x) for i,x in enumerate(tramp)})
    prior={'v1145_private_postalarm_handler_return.h':render_return(call,R,dispatch_resume,restore,tail,w),
           'v922_private_irq_return.h':h.replace('::v767','::v922'),
           'v939_private_second_vector.h':vh,'v663_private_external_expectations.h':eh}
    return ep,j,vectors,edges,entries,dw,prior

def render():
    return ('#pragma once\n#include "v922_private_irq_return.h"\n#include "v939_private_second_vector.h"\n'
            '#include "v663_private_external_expectations.h"\nnamespace undercover::wii::v1151 {\n'
            'inline constexpr auto epilogue=v922::expected;\ninline constexpr auto vector=v922::second_expected;\n'
            'inline constexpr auto image=v663::expected.vector;\n}\n')

def install(dol,elf,root,host):
    ep,j,vectors,edges,entries,dw,prior=metadata(dol,elf)
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    result=dest/'v1151_private_held_epilogue.h'
    additions=('wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h')
    for n in ('wii_live_epilogue_v762.h','wii_second_vector_v939.h','wii_second_si_dispatch_v944.h',
              'wii_pending_external_reentry_v932.h','wii_second_ack_live_v958.h','wii_third_alarm_suffix_v1047.h'):
        prior[n]=(host/n).read_text()
    if dest.is_symlink() or any(x.exists() or x.is_symlink() for x in (result,*[dest/n for n in additions])) or any(
        x.is_symlink() or not x.is_file() for x in (private,*[dest/n for n in prior])):
        raise ValueError('held epilogue destination')
    if any((dest/n).read_text()!=value for n,value in prior.items()):raise ValueError('held epilogue identity')
    old=private.read_text();macro='#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE' in old:raise ValueError('held epilogue mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('held epilogue tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    if set(ep)&set(vectors):raise ValueError('held epilogue geometry')
    expected={**ep,**vectors,DISPATCH:(DISPATCH,dw)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('held epilogue coverage')
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('held epilogue owner')
        return hits[0]
    for a in (*entries,VECTOR,TRAMP,DISPATCH):owner(a)
    verify_resume_dispatch(outer,DISPATCH,j)
    for a,links in edges:
        body=exact_function(src[owner(a)],a)
        for pc,dst_pc in links:verify_direct(body,pc,dst_pc)
    # V1146 already owns the first dispatcher instruction. Its exact
    # pre-tick seam must survive; the new begin() consumes it at that tick.
    first=block_at(exact_function(src[owner(DISPATCH)],DISPATCH),j,ep[j][1])
    arg=f'ctx,0x{j:08x}u,0x{ep[j][1]:08x}u'
    if first.count(f'undercover::wii::v958::postalarm_handler_dispatch_resume({arg});')!=1 or \
       first.count(f'undercover::wii::v958::before({arg},false);')!=1:
        raise ValueError('held epilogue resume')
    labels={**ep,**vectors};labels.pop(j)
    for a in sorted({a for a,_ in labels.values()}):
        p=owner(a);source=changes.get(p,src[p]);body=exact_function(source,a);out=body
        for pc,(rootpc,w) in sorted(labels.items()):
            if rootpc==a:
                try:out=patch_label(out,pc,w,pc in vectors,a in (DISABLE,RESTORE))
                except ValueError as e:
                    # Bounded role/index and hook counts; no original PCs or words.
                    block=block_at(out,pc,w)
                    role='vector' if a==VECTOR else 'trampoline' if a==TRAMP else 'disable' if a==DISABLE else 'restore' if a==RESTORE else 'dispatcher' if a==DISPATCH else 'epilogue'
                    n=sum(block.count(x) for x in ('v922::before(','v922::second_before(','v922::second_dispatch_before('))
                    print(f'V1244_EPILOGUE_HOOK_REFUSAL role={role} index={(pc-a)//4} legacy={min(n,9)} predicate={min(block.count("v922::active()"),9)} reason={str(e).replace(" ","_") if str(e) in ("held epilogue tick","held epilogue legacy","held epilogue shared","held epilogue block") else "other"}')
                    raise
        changes[p]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    changes[private]=old.replace(macro,macro+'#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n',1)
    changes[result]=render()
    for n in additions:changes[dest/n]=(host/n).read_text()
    for path,value in changes.items():path.write_text(value)
    print(f'V1152_HELD_EPILOGUE_ROUTE installed=1 epilogue_labels={len(ep)} vector_labels=38 trampoline_labels=20 dispatcher_entry=1 resume_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'held epilogue '+s for s in ('tick','legacy','shared','block','geometry','vector','destination','identity','mode','tree','coverage','owner','resume')}
        safe|={'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','resume dispatcher identity','held handler label'}
        print('V1152_HELD_EPILOGUE_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
