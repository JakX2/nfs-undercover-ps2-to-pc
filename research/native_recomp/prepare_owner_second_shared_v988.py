#!/usr/bin/env python3
"""Authenticate the completion helper's second call to the shared time root."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge
from prepare_owner_second_alarm_v985 import plan as base_plan,header as base_header,install,patch_analyzer

def admit_shared_time(dol,elf,roots,guard,extra):
    completion,nested=extra[1][1],extra[2][1]
    raw=exact(dol,elf,completion,len(roots[completion]))
    site,dst,w=edge(completion,raw,2)
    if dst!=nested or site not in guard or roots[completion][(site-completion)//4]!=0x4e800020:
        raise ValueError('shared time geometry')
    code=exact(dol,elf,nested,len(roots[nested]))
    if len(code)!=25 or list(code)!=list(roots[nested]):raise ValueError('shared time body')
    roots[completion][(site-completion)//4]=w;guard.remove(site)
    return (site,dst,4*len(code),w,code)

def plan(dol,elf):
    p=base_plan(dol,elf)
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    shared=admit_shared_time(dol,elf,roots,guard,extra)
    q=(roots,edges,indirect,iw,hw,dw,guard,(*extra,shared))
    # Drop the now-admitted guard from the private diagnostic census.
    tail=list(p[1:]);tail[8]=[row for row in tail[8] if row[0]!=shared[0]]
    return (q,*tail),shared[0]

def header(p,site,out):
    base_header(p,out);s=out.read_text()
    old=next(l for l in s.splitlines() if ' AckEdges' in l)
    extra=(*p[0][-1][:13],p[0][-1][-1])
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    s=replace_exact(s,old,'inline constexpr std::array<std::array<uint32_t,2>,14> AckEdges{{'+','.join('std::array<uint32_t,2>{'+fmt((a,b))+'}' for a,b,_,_,_ in extra)+'}};')
    s+=f'inline constexpr uint32_t CompletionTimeCall=0x{site:08x}u;\n'
    out.write_text(s)

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q,site=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:header(q,site,a.output);print('V988_SHARED_GEOMETRY roots=14 extra_edge=1 same_time_root=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        print('V988_SHARED_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in ('shared time geometry','shared time body','native coverage','native owner','hook identity') else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
