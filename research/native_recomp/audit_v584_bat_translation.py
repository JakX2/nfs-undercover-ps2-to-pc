#!/usr/bin/env python3
"""Require exact native BAT/RFI provenance in the private complete-image output."""
import argparse,hashlib,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at
MAPS=((0x805270c4,0x80527144,12),(0x80527144,0x80527218,20),(0x80527550,0x80527568,0))
ROOTS=(0x805270c4,0x80527144,0x80527550)
RESUMES=(0x805275d0,0x80527600)
RFI=0x4c000064
def bat_spr(w):
    if w>>26!=31 or ((w>>1)&1023)!=467:return None
    spr=((w>>16)&31)|(((w>>11)&31)<<5)
    return spr if 528<=spr<=543 or 560<=spr<=575 else None
def geometry(data,digest=OWNER_SHA):
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('identity')
    expected={}
    for lo,hi,count in MAPS:
        words=words_at(data,lo,(hi-lo)//4)
        writes=[(lo+4*i,w,bat_spr(w)) for i,w in enumerate(words) if bat_spr(w) is not None]
        if len(writes)!=count or words[-1]!=RFI or RFI in words[:-1]:raise ValueError('mapper geometry')
        for pc,w,spr in writes:expected[pc]=(w,spr,(w>>21)&31)
        expected[hi-4]=(RFI,None,None)
    return expected
LABEL=re.compile(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n')
def audit_shards(shards,expected):
    hits={pc:0 for pc in expected}
    for s in shards:
        matches=list(LABEL.finditer(s))
        for i,m in enumerate(matches):
            pc=int(m[1],16)
            if pc not in hits:continue
            w,spr,reg=expected[pc]
            if int(m[2],16)!=pc or int(m[3],16)!=w:raise ValueError('original word provenance')
            stop=matches[i+1].start() if i+1<len(matches) else len(s)
            body=s[m.end():stop].split('\n}',1)[0]
            if any(x in body for x in ('interpret_step','micro_interpret','UNIMPLEMENTED','unimplemented mtspr')):
                raise ValueError('native fallback')
            if body.count('++ctx.inst_count;')!=1:raise ValueError('native tick')
            if spr is not None:
                if body.count(f'ctx.write_bat({spr}, ctx.gpr[{reg}]);')!=1 or body.count('ctx.write_bat(')!=1:
                    raise ValueError('native BAT write')
            elif any(body.count(x)!=1 for x in ('ctx.msr = ctx.srr1;', 'ctx.pc = ctx.srr0;', 'ctx.dispatch_saved_ctx = 0;')):
                raise ValueError('native RFI')
            elif 'return;' not in body:raise ValueError('native RFI transfer')
            hits[pc]+=1
    if any(n!=1 for n in hits.values()):
        print(f'V586_BAT_COVERAGE missing={sum(n==0 for n in hits.values())} duplicate={sum(n>1 for n in hits.values())}')
        raise ValueError('unique native coverage')
    return sum(s is not None for _,s,_ in expected.values()),sum(s is None for _,s,_ in expected.values())
def audit_dispatch(source):
    for pc in (*ROOTS,*RESUMES):
        if len(re.findall(r'(?m)^\s*case 0x'+f'{pc:X}'+r': [A-Za-z_][A-Za-z0-9_]*\(ctx\); break;$',source))!=1:
            raise ValueError('native dispatch target')
    if source.count('else if (ctx.pc < 0x80000000) ctx.pc |= 0x80000000;')!=1:
        raise ValueError('physical PC normalization')
def install(data,generated,digest=OWNER_SHA):
    expected=geometry(data,digest)
    shards=sorted(generated.glob('output_*.cpp'))
    paths=shards+[generated/'main_output.cpp']
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths):
        raise ValueError('full-image geometry')
    result=audit_shards((p.read_text(encoding='utf-8') for p in shards),expected)
    audit_dispatch(paths[-1].read_text(encoding='utf-8'))
    if result!=(32,3):raise ValueError('native coverage')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,struct.error) as e:
        reasons={'identity','mapper geometry','original word provenance','native fallback','native tick','native BAT write','native RFI','native RFI transfer','unique native coverage','native dispatch target','physical PC normalization','full-image geometry','native coverage','size'}
        reason=str(e) if str(e) in reasons else 'other'
        print('V584_BAT_TRANSLATION rejected=1 reason='+reason.replace(' ','_'));return 1
    print('V584_BAT_TRANSLATION owner=1 writes=32 rfi=3 dispatch=5 fallback=0 link=0 execution=0 permissions=0 boot_verified=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
