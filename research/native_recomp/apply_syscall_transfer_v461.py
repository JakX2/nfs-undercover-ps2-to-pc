#!/usr/bin/env python3
"""Honor syscall-handler control transfer and stopped CPU in both paths.

Requires V26 exact guest syscall PC. Does not implement new syscall IDs,
exception vectors or callback scheduling; retains the handler's PC policy.
"""
import argparse
from pathlib import Path
from apply_syscall_pc_v26 import NEW as EMIT_OLD
EMITTER=Path('nWiiRecomp/src/recompiler.cpp')
INTERPRETER=Path('nWiiRuntime/src/hle/interpreter.cpp')
EMIT_NEW=EMIT_OLD.replace('nwii::runtime::handle_syscall(ctx);','if (nwii::runtime::handle_syscall(ctx) || !ctx.is_running) return;')
INTERP_OLD='''    case 17: 
        handle_syscall(ctx);
        break;'''
INTERP_NEW='''    case 17:
        if (handle_syscall(ctx) || !ctx.is_running) return true;
        break;'''
def rewrite(e,i):
    if e.count(EMIT_NEW)==1 and EMIT_OLD not in e and i.count(INTERP_NEW)==1 and INTERP_OLD not in i:return e,i,False
    if e.count(EMIT_OLD)!=1 or EMIT_NEW in e or i.count(INTERP_OLD)!=1 or INTERP_NEW in i:
        raise ValueError('unknown or mixed syscall transfer source')
    ne=e.replace(EMIT_OLD,EMIT_NEW);ni=i.replace(INTERP_OLD,INTERP_NEW)
    if ne.replace(EMIT_NEW,EMIT_OLD)!=e or ni.replace(INTERP_NEW,INTERP_OLD)!=i:raise ValueError('roundtrip')
    return ne,ni,True
def apply(root):
    ep,ip=root/EMITTER,root/INTERPRETER
    if ep.is_symlink() or ip.is_symlink():raise ValueError('symlink')
    e,i=ep.read_text(encoding='utf-8'),ip.read_text(encoding='utf-8')
    ne,ni,changed=rewrite(e,i)
    if changed:ep.write_text(ne,encoding='utf-8');ip.write_text(ni,encoding='utf-8')
    return changed
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V461_SYSCALL_TRANSFER installed=1 changed={int(apply(a.root))}')
