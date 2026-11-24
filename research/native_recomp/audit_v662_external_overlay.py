"""Private, translation-only audit for the original installed external vector."""
import argparse, hashlib, re, struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA, MAX_DOL, words_at
from prepare_v453_debug_leaf import VECTORS, data_at, vector_geometry
VECTOR=0x80000500
SOURCE=0x80520ec0
FN='func_80000500'
DEF=f'void {FN}(CPUContext& ctx) {{'
DEFAULT='default: nwii::runtime::interpret_step(ctx); return;'
LABEL=re.compile(r'(?mi)^loc_([0-9a-f]+): ;\n    // 0x([0-9a-f]+): ([0-9a-f]+)\n')
def expected(data):
    if len(data)>MAX_DOL or hashlib.sha256(data).hexdigest()!=OWNER_SHA:raise ValueError('identity')
    if not vector_geometry(data)[0] or struct.unpack('>15I',data_at(data,VECTORS,60))[4]!=0x500:raise ValueError('slot')
    w=list(words_at(data,SOURCE,38));w[22]=0x60000000;w[26]|=4
    return w

def audit_body(source,words):
    if len(words)!=38 or source.count(DEF)!=1:raise ValueError('definition')
    body=source.split(DEF,1)[1].split('\n}\n',1)[0]
    hits=list(LABEL.finditer(body))
    if not 12<=len(hits)<=38:raise ValueError('extent')
    pcs=[]
    for i,m in enumerate(hits):
        pc,comment,word=(int(x,16) for x in m.groups())
        if not VECTOR<=pc<VECTOR+152 or pc&3 or pc!=comment or word!=words[(pc-VECTOR)//4]:raise ValueError('identity')
        block=body[m.end():hits[i+1].start() if i+1<len(hits) else len(body)]
        if block.count('++ctx.inst_count;')!=1:raise ValueError('tick')
        pcs.append(pc)
    if pcs!=sorted(set(pcs)) or pcs[0]!=VECTOR:raise ValueError('coverage')
    if any(x in body.replace(DEFAULT,'') for x in ('interpret_step','micro_interpret','UNIMPLEMENTED','unimplemented')):raise ValueError('fallback')
    return len(pcs)

def audit(root,words):
    shards=list(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('tree')
    dispatch=main.read_text(encoding='utf-8')
    if len(re.findall(r'(?m)^\s*case 0x80000500: func_80000500\(ctx\); break;\s*$',dispatch))!=1:raise ValueError('dispatch')
    owners=[]
    for p in shards:
        s=p.read_text(encoding='utf-8')
        if DEF in s:owners.append(audit_body(s,words))
    if len(owners)!=1:raise ValueError('owner')
    return owners[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        n=audit(a.generated,expected(a.dol.read_bytes()))
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V662_IRQ_TRANSLATION verified=0');return 1
    print(f'V662_IRQ_TRANSLATION verified=1 native_labels={n} full_image=1 link=0 runtime_delivery=0 boot_verified=0');return 0
if __name__=='__main__':raise SystemExit(main())
