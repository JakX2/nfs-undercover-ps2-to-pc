#!/usr/bin/env python3
"""Count native instruction visits at labels, including goto/resume entries."""
import argparse
from pathlib import Path

FILE=Path('nWiiRecomp/src/recompiler.cpp')
BEFORE='    out << "    ++ctx.inst_count;\\n";\n    emit_instruction(out, inst, func);'
AFTER='    emit_instruction(out, inst, func);'
LABEL='''  out << "loc_" << std::hex << std::uppercase << inst.address << std::dec
      << ": ;\\n";
  out << "    // 0x" << std::hex << std::setfill('0') << std::setw(8)
      << inst.address << ": ";
  out << std::setfill('0') << std::setw(8) << inst.opcode << std::dec << "\\n";'''
LABEL_TICK=LABEL+'\n  out << "    ++ctx.inst_count;\\n";'
TICK='out << "    ++ctx.inst_count;\\n";'

def rewrite(source):
    if source.count(LABEL_TICK)==1 and BEFORE not in source and source.count(TICK)==1:
        if source.count(AFTER)!=1 or source.count(LABEL)!=1:raise ValueError('ambiguous patched emitter')
        return source
    if source.count(BEFORE)!=1 or source.count(AFTER)!=1 or source.count(LABEL)!=1 or source.count(TICK)!=1 or LABEL_TICK in source:
        raise ValueError('unknown emitter tick geometry')
    out=source.replace(BEFORE,AFTER,1).replace(LABEL,LABEL_TICK,1)
    if out.replace(LABEL_TICK,LABEL,1).replace(AFTER,BEFORE,1)!=source:raise ValueError('roundtrip')
    return out

def apply(root):
    path=root/FILE
    if path.is_symlink():raise ValueError('source symlink')
    source=path.read_text(encoding='utf-8');out=rewrite(source)
    if out!=source:path.write_text(out,encoding='utf-8')
    return out!=source

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:changed=apply(a.root)
    except (ValueError,OSError,UnicodeError):
        print('V438_NATIVE_TICK installed=0');return 1
    print(f'V438_NATIVE_TICK installed=1 changed={int(changed)} dispatch_unchanged=1');return 0
if __name__=='__main__':raise SystemExit(main())
