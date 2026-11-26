"""Fail-closed symbolic audit of a straight-line cooperative PPC save leaf.
No original instructions or values are printed by this module.
"""
BLR=0x4e800020

def audit_save(words):
    if not 1<=len(words)<=128 or words[-1]!=BLR:
        raise ValueError('save terminal')
    regs=[('gpr',i) for i in range(32)]
    saved={}
    def put(off,val):
        if off<0 or off>=0x2c8 or off&3 or off in saved:
            raise ValueError('save store geometry')
        saved[off]=val
    for w in words[:-1]:
        op=w>>26;rt=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023;imm=w&0xffff
        if op in (36,47):
            if regs[ra]!=('gpr',3):raise ValueError('save base')
            for n in range(rt,32 if op==47 else rt+1):put(imm+4*(n-rt),regs[n])
        elif op==14 and ra==0:
            regs[rt]=('const',((imm^0x8000)-0x8000)&0xffffffff)
        elif op==31 and not(w&1):
            if xo==19: # mfcr
                if w&0x001ff800:raise ValueError('save encoding')
                regs[rt]=('cr',0)
            elif xo==83: # mfmsr
                if w&0x001ff800:raise ValueError('save encoding')
                regs[rt]=('msr',0)
            elif xo==339: # mfspr
                spr=(rb<<5)|ra
                if spr not in (1,8,9,*range(912,920)):raise ValueError('save spr')
                regs[rt]=('spr',spr)
            elif xo==444 and rt==rb: # or/mr rA,rS,rS
                regs[ra]=regs[rt]
            else:raise ValueError('save instruction')
        elif w==0x60000000: # nop
            pass
        else:raise ValueError('save instruction')
    expected={4:('gpr',1),8:('gpr',2),12:('const',1),128:('cr',0),132:('spr',8),136:('spr',9),140:('spr',1),408:('spr',8),412:('msr',0)}
    expected.update({i*4:('gpr',i) for i in range(13,32)})
    if any(saved.get(k)!=v for k,v in expected.items()) or regs[3]!=('const',0):
        raise ValueError('save provenance')
    if any(regs[i]!=('gpr',i) for i in (1,2,*range(13,32))):
        raise ValueError('save preserved ABI')
    gqr=0
    for i in range(8):
        off=0x1a4+4*i
        if off in saved:
            if saved[off]!=('spr',912+i):raise ValueError('save gqr provenance')
            gqr|=1<<i
    return gqr
