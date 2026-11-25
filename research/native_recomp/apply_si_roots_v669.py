#!/usr/bin/env python3
"""Restrict native SI-dispatch label ownership to authenticated ELF spans."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_bat_roots_v586 import ROOT,READ
from apply_stm_native_open_v632 import OLD as SCANNER
from prepare_v667_si_dispatch import geometry,exact,DISPATCH,HANDLER,SCHED,TIME,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
TRAMP=0x80526ce0
ROOTS=tuple(sorted({DISPATCH,HANDLER,SCHED,TIME,DISABLE,RESTORE,TRAMP}))
TEST_SPANS=tuple((r,4) for r in ROOTS)
def spans(dol,elf,first_helper=False,epilogue=False,transfer_prefix=False,alarm=False,callback=False):
    geometry(dol,elf)
    sizes=parse_functions(elf);out=[]
    for pc in ROOTS:
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3:raise ValueError('SI root extent')
        exact(dol,elf,pc,n//4)
        out.append((pc,n))
    if first_helper:
        from si_helper_geometry_v680 import helper_plan
        (_,target,size,_,_),alias,_=helper_plan(dol,elf)
        if not alias and target not in ROOTS:out.append((target,size))
        from si_second_geometry_v688 import second_plan
        _,target,size,_,_=second_plan(dol,elf)
        if target not in {a for a,_ in out}:out.append((target,size))
        from si_nested_geometry_v693 import nested_plan
        _,target,size,_,_=nested_plan(dol,elf)
        if target not in {a for a,_ in out}:out.append((target,size))
    if epilogue:
        from prepare_owner_scheduler_v722 import plan,E,S
        from prepare_owner_context_v720 import plan as loader,L
        q=plan(dol,elf)[0];code,_=loader(dol,elf)
        for a,words in ((E,q[E]),(S,q[S]),(L,code)):
            if a in {x for x,_ in out}:raise ValueError('epilogue root overlap')
            out.append((a,4*len(words)))
    if transfer_prefix:
        from prepare_owner_transfer_v765 import plan
        q,C,*_=plan(dol,elf)
        if C in {a for a,_ in out}:raise ValueError('transfer root overlap')
        out.append((C,4*len(q[C])))
    if alarm:
        from prepare_owner_head_v782 import plan
        q,C,D,R,T,U,K,*_=plan(dol,elf)
        for a in (C,K):
            if a in {x for x,_ in out}:raise ValueError('alarm root overlap')
            out.append((a,4*len(q[a])))
        for a in (D,R,T,U):
            if (a,4*len(q[a])) not in out:raise ValueError('alarm leaf ownership')
    if callback:
        from prepare_owner_callback_prefix_v797 import plan
        _,C,*_=plan(dol,elf)
        n=sizes.get(C,0)
        if n!=688 or C in {a for a,_ in out}:raise ValueError('callback root overlap')
        exact(dol,elf,C,n//4)
        out.append((C,n))
    return tuple(sorted(out))
def pairs(ranges=TEST_SPANS,alias=0,restore_alias=0,transfer_alias=0,transfer_restore_alias=0,callback_alias=0):
    if not set(ROOTS).issubset(pc for pc,_ in ranges) or len(ranges) not in (7,8,9,10,11,12,13,14,15,16,17) or tuple(sorted(set(pc for pc,_ in ranges)))!=tuple(pc for pc,_ in ranges) or any(n&3 or not 4<=n<=4096 for pc,n in ranges):
        raise ValueError('SI roots')
    if any(a+n>b for (a,n),(b,_) in zip(ranges,ranges[1:])):raise ValueError('SI root overlap')
    aliases=tuple(x for x in (alias,restore_alias,transfer_alias,transfer_restore_alias) if x)
    if len(set(aliases))!=len(aliases) or any(x&3 or not 0x80000000<=x<0x81800000 or any(a<=x<a+n for a,n in ranges) for x in aliases):raise ValueError('first SI alias overlap')
    if callback_alias and callback_alias not in aliases:
        if callback_alias&3 or not 0x80000000<=callback_alias<0x81800000 or any(a<=callback_alias<a+n for a,n in ranges):raise ValueError('callback alias overlap')
        aliases+= (callback_alias,)
    root=ROOT+'''
    // Private ELF-authenticated SI interrupt route ownership.
    const auto si_owner=[](uint32_t a)->uint32_t {
'''+''.join(f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in ranges)+'''      return 0;
    };
    if(si_owner(func_start)&&si_owner(func_start)!=func_start)continue;'''
    read='''        const auto si_root=si_owner(current_pc);
        if((si_root&&si_root!=func_start)||(si_owner(func_start)&&si_root!=func_start))break;
'''+READ
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc in (*[a for a,_ in ranges],*aliases))+')func.hle_hook_name.clear();'
    return ((ROOT,root),(READ,read),(SCANNER,scanner))
def apply(root,ranges,alias=0,restore_alias=0,transfer_alias=0,transfer_restore_alias=0,callback_alias=0):
    p=root/'nWiiAnalyzer/src/analyzer.cpp'
    if p.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old,pairs(ranges,alias,restore_alias,transfer_alias,transfer_restore_alias,callback_alias))
    if new!=old:p.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('--first-ack-helper',action='store_true');p.add_argument('--restore-alias',action='store_true');p.add_argument('--epilogue',action='store_true');p.add_argument('--transfer-prefix',action='store_true');p.add_argument('--transfer-return',action='store_true');p.add_argument('--alarm',action='store_true');p.add_argument('--callback-prefix',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        dol,elf=a.dol.read_bytes(),a.elf.read_bytes()
        if a.alarm and not a.transfer_return:raise ValueError('alarm without transfer')
        if a.callback_prefix and not a.alarm:raise ValueError('callback without alarm')
        ranges=spans(dol,elf,a.first_ack_helper,a.epilogue,a.transfer_prefix,a.alarm,a.callback_prefix);alias=0
        if a.first_ack_helper:
            from si_helper_geometry_v680 import helper_plan
            (_,target,_,_,_),is_alias,_=helper_plan(dol,elf)
            if is_alias:alias=target
        restore_alias=0
        if a.restore_alias:
            if not a.first_ack_helper:raise ValueError('restore without ACK route')
            from prepare_owner_restore_v735 import plan
            restore_alias=plan(dol,elf)[0]
        transfer_alias=0
        if a.transfer_prefix:
            if not a.first_ack_helper:raise ValueError('transfer without ACK route')
            from prepare_owner_pair_v753 import plan as pair
            transfer_alias=pair(dol,elf,4)[0]
        transfer_restore_alias=0
        if a.transfer_return:
            if not a.transfer_prefix:raise ValueError('transfer return without prefix')
            transfer_restore_alias=pair(dol,elf,4)[1]
        callback_alias=0
        if a.callback_prefix:
            from prepare_owner_callback_prefix_v797 import plan
            callback_alias=plan(dol,elf)[2]
        apply(a.root,ranges,alias,restore_alias,transfer_alias,transfer_restore_alias,callback_alias)
    except (OSError,ValueError,UnicodeError) as exc:
        reasons={'first SI dependency not direct':1,'first SI dependency extent':2,'first SI dependency return':3,'word identity':4,'SI root overlap':5,'SI roots':6,'SI root extent':7,'save leaf terminator':8,'save leaf shape':9,'save leaf extent':10,'save leaf sequence':11,'first SI alias containment':12,'first SI alias unsupported kind':13,'first SI alias overlap':14,'second SI call kind':15,'second SI extent':16,'second SI verified shape':17,'second SI verified dependencies':18,'nested first route':19,'nested extent':20,'nested verified shape':21}
        print(f'V682_SI_ANALYZER_REFUSAL category={reasons.get(str(exc),0)}')
        print('V669_SI_ANALYZER installed=0');return 1
    print(f'V669_SI_ANALYZER installed=1 roots={len(ranges)} exact_dol_elf=1 scoped=1 shared_alias={int(bool(alias))}');return 0
if __name__=='__main__':raise SystemExit(main())
