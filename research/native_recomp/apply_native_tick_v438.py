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
# Both split and non-split run_game wrappers currently count host-side
# dispatch as though it were a PowerPC instruction. Once V438 counts each
# native instruction label, those host increments create unobserved holes
# in SI/EXI completion tick sequences across returns, indirect edges and RFI.
# Keep the existing 100k diagnostic but never fabricate a guest tick.
DISPATCH_BEFORE='    out << "        uint32_t target = ctx.pc;\\n        if ((++ctx.inst_count % "'
DISPATCH_AFTER='    out << "        uint32_t target = ctx.pc;\\n        if (ctx.inst_count && (ctx.inst_count % "'

def rewrite(source, *, require_dispatch=False):
    if type(source) is not str or type(require_dispatch) is not bool:
        raise ValueError('native tick source')
    # Synthetic miniature emitters may omit run_game. The real pinned
    # emitter must contain the split and non-split dispatch wrappers.
    if source.count(LABEL_TICK)==1 and BEFORE not in source and source.count(TICK)==1:
        if source.count(AFTER)!=1 or source.count(LABEL)!=1:
            raise ValueError('ambiguous patched emitter')
        out=source
    else:
        if (source.count(BEFORE)!=1 or source.count(AFTER)!=1 or
                source.count(LABEL)!=1 or source.count(TICK)!=1 or
                LABEL_TICK in source):
            raise ValueError('unknown emitter tick geometry')
        out=source.replace(BEFORE,AFTER,1).replace(LABEL,LABEL_TICK,1)
        if out.replace(LABEL_TICK,LABEL,1).replace(AFTER,BEFORE,1)!=source:
            raise ValueError('label tick roundtrip')
    old,new=out.count(DISPATCH_BEFORE),out.count(DISPATCH_AFTER)
    if (old,new)==(2,0):
        updated=out.replace(DISPATCH_BEFORE,DISPATCH_AFTER,2)
        if updated.replace(DISPATCH_AFTER,DISPATCH_BEFORE,2)!=out:
            raise ValueError('dispatch tick roundtrip')
        out=updated
    elif (old,new)==(0,2):
        pass  # idempotent on a fully patched emitter
    elif (old,new)==(0,0) and not require_dispatch:
        pass  # isolated label-emitter test without run_game
    else:
        raise ValueError('ambiguous host dispatcher ticks')
    if require_dispatch and out.count(DISPATCH_AFTER)!=2:
        raise ValueError('missing host dispatch wrappers')
    return out


def apply(root):
    path=root/FILE
    if path.is_symlink():raise ValueError('source symlink')
    source=path.read_text(encoding='utf-8');out=rewrite(source,require_dispatch=True)
    if out!=source:path.write_text(out,encoding='utf-8')
    return out!=source

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:changed=apply(a.root)
    except (ValueError,OSError,UnicodeError):
        print('V438_NATIVE_TICK installed=0');return 1
    print(f'V438_NATIVE_TICK installed=1 changed={int(changed)} dispatch_guest_tick=0');return 0
if __name__=='__main__':raise SystemExit(main())
