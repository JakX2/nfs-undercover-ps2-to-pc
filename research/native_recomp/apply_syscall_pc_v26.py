#!/usr/bin/env python3
"""Fix NWiiRecomp system-call entry PC before HLE handler dispatch.

Prior emitter leaves ctx.pc at the most recent branch return address for a
fall-through `sc`. Set ctx.pc to the actual guest instruction address.
Original-free, idempotent, fail-closed patch against known upstream emitter.
"""
import argparse
from pathlib import Path

OLD = '''  } else if (ppc_inst.opcode() == 17) { 
    out << "    // sc (System Call)\\n";
    out << "    nwii::runtime::handle_syscall(ctx);\\n";
'''
NEW = '''  } else if (ppc_inst.opcode() == 17) { 
    out << "    // sc (System Call)\\n";
    out << "    ctx.pc = 0x" << std::hex << std::uppercase << inst.address << std::dec
        << "; // exact guest syscall instruction PC\\n";
    out << "    nwii::runtime::handle_syscall(ctx);\\n";
'''

def apply(root:Path):
    path=root/'nWiiRecomp/src/recompiler.cpp'
    data=path.read_text(encoding='utf-8')
    if NEW in data and OLD not in data:
        return 'already applied'
    if data.count(OLD)!=1 or NEW in data:
        raise ValueError('recompiler opcode-17 emitter changed; refuse unsafe patch')
    path.write_text(data.replace(OLD,NEW,1),encoding='utf-8')
    return 'installed'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('upstream',type=Path)
    a=p.parse_args()
    print('V26 syscall PC patch:',apply(a.upstream))
