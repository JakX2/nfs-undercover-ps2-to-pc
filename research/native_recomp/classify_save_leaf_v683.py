"""Independent recognition of compiler register-save leaf aliases.

Only public PPC instruction semantics are encoded. No game bytes are
embedded or exported. This classifier alone never authorizes translation.
"""
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
from prepare_v419_full_start import words_at
from audit_v264_osinit_retry_elf import read_words
BLR=0x4e800020
def classify_suffix(words):
    # Register-save alias: one or more contiguous nonvolatile GPR or FPR
    # stores into a fixed stack/frame base, ending at the original BLR.
    # No calls, loads, branches, MSR changes, or arbitrary memory operands.
    if not 2<=len(words)<=19 or words[-1]!=BLR:raise ValueError('save leaf terminator')
    op=words[0]>>26;base=(words[0]>>16)&31;reg=(words[0]>>21)&31
    if op not in (36,54) or base not in (1,11) or not 14<=reg<=31:raise ValueError('save leaf shape')
    stride=4 if op==36 else 8
    disp=((words[0]&0xffff)^0x8000)-0x8000
    if disp>=0 or disp%stride or disp<-512 or len(words)!=33-reg:raise ValueError('save leaf extent')
    for i,w in enumerate(words[:-1]):
        d=((w&0xffff)^0x8000)-0x8000
        if w>>26!=op or (w>>16)&31!=base or (w>>21)&31!=reg+i or d!=disp+i*stride or d>=0:
            raise ValueError('save leaf sequence')
    return dict(kind=1 if op==36 else 2,registers=32-reg,base=base)
def symbol_evidence(elf,address):
    if len(elf)<HEADER.size:raise ValueError('ELF header')
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf):raise ValueError('ELF section table')
    rows=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    result=dict(sized_func=0,zero_func=0,notype=0,other=0)
    for _,kind,_,_,at,size,_,_,_,entsize in rows:
        if kind!=2:continue
        if entsize!=SYMBOL.size or size%entsize or size>16*1024*1024 or at+size>len(elf):raise ValueError('ELF symbol table')
        for pos in range(at,at+size,entsize):
            _,addr,length,info,_,shndx=SYMBOL.unpack_from(elf,pos)
            if addr!=address or not 0<shndx<len(rows):continue
            section=rows[shndx]
            if not section[2]&4 or not section[3]<=addr<section[3]+section[5]:continue
            typ=info&15
            k='sized_func' if typ==2 and length else 'zero_func' if typ==2 else 'notype' if typ==0 else 'other'
            result[k]+=1
    return result
def inspect_suffix(dol,elf,address):
    if address&3:raise ValueError('save leaf alignment')
    words=[]
    for i in range(19):
        a=address+4*i
        w=words_at(dol,a,1)
        if w!=tuple(read_words(elf,a,1)):raise ValueError('save leaf identity')
        words.append(w[0])
        if w[0]==BLR:break
    return classify_suffix(words)
