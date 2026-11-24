#!/usr/bin/env python3
"""Keep the immutable installed SC vector direct-call-only in split AOT output."""
import argparse,hashlib,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at
VECTOR=0x80000c00
SOURCE=0x805290a8
FN='func_80000C00'
BOUND='    {0x80000C00, 0x80000C1C, func_80000C00},\n'
CASE='            case 0x80000C00: func_80000C00(ctx); break;\n'
TARGET='        uint32_t target = ctx.pc;\n'
GATE=TARGET+'''        // V572: only authenticated direct SC calls may enter this overlay.
        if (target >= 0x80000C00u && target < 0x80000C1Cu) {
            std::cout << "V572_SC_DIRECT_ONLY rejected=1" << std::endl;
            ctx.is_running = false;
            continue;
        }
'''
DECL='void func_80000C00(nwii::runtime::CPUContext& ctx);'
DEF='void func_80000C00(CPUContext& ctx) {'
DEFAULT='default: nwii::runtime::interpret_step(ctx); return;'
def rewrite(s):
    if any(s.count(x)!=1 for x in (BOUND,CASE,TARGET)) or s.count(FN)!=2 or GATE in s:
        raise ValueError('dispatcher geometry')
    out=s.replace(BOUND,'',1).replace(CASE,'',1).replace(TARGET,GATE,1)
    if FN in out or out.replace(GATE,TARGET,1)!=s.replace(BOUND,'',1).replace(CASE,'',1):
        raise ValueError('dispatcher gate')
    return out
def audit_body(s,words):
    if s.count(DEF)!=1 or s.count(FN+'(')!=1:raise ValueError('unique native vector')
    body=s.split(DEF,1)[1].split('\n}\n',1)[0]
    labels=re.findall(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n',body)
    want=[(VECTOR+4*i,VECTOR+4*i,w) for i,w in enumerate(words)]
    if [(int(a,16),int(b,16),int(c,16)) for a,b,c in labels]!=want:
        raise ValueError('vector instruction provenance')
    if body.count(DEFAULT)!=1 or body.count('++ctx.inst_count;')!=7:
        raise ValueError('vector native instruction coverage')
    if any(x in body.replace(DEFAULT,'') for x in ('interpret_step','micro_interpret','UNIMPLEMENTED')):
        raise ValueError('vector fallback')
    if body.count('ctx.pc = ctx.srr0;')!=1 or body.count('ctx.msr = ctx.srr1;')!=1:
        raise ValueError('vector RFI')
def install(root,words):
    if len(words)!=7:raise ValueError('vector size')
    paths=[root/'functions.h',root/'main_output.cpp',*root.glob('output_*.cpp')]
    if len(paths)<3 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths):
        raise ValueError('generated tree')
    if paths[0].read_text(encoding='utf-8').count(DECL)!=1:raise ValueError('native declaration')
    main=paths[1].read_text(encoding='utf-8');out=rewrite(main)
    n=0
    for p in paths[2:]:
        s=p.read_text(encoding='utf-8')
        if FN+'(' in s:
            audit_body(s,words);n+=1
    if n!=1:raise ValueError('vector definition')
    paths[1].write_text(out,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('generated',type=Path)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--vector',type=Path);g.add_argument('--owner',type=Path)
    a=p.parse_args()
    try:
        if a.owner:
            if a.owner.stat().st_size>MAX_DOL:raise ValueError('size')
            data=a.owner.read_bytes()
            if hashlib.sha256(data).hexdigest()!=OWNER_SHA:raise ValueError('identity')
            words=words_at(data,SOURCE,7)
        else:
            words=struct.unpack('>7I',a.vector.read_bytes())
        install(a.generated,words)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V572_SC_DIRECT_GATE installed=0');return 1
    print('V572_SC_DIRECT_GATE installed=1 labels=7 native=1 dispatcher_entries=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
