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

# An instruction-count milestone may be visited repeatedly by host dispatch
# without another translated guest instruction (e.g. callback/RFI churn).
# Report each milestone once per run_game invocation, never once per host edge.
HISTORY='    out << "    static uint32_t pc_history[10] = {0};\\n";'
HISTORY_ONCE='    out << "    uint64_t last_dispatch_diagnostic_count = 0;\\n";\n'+HISTORY
DIAGNOSTIC='           "100000) == 0) std::cout << \\"Dispatcher PC: 0x\\" << std::hex << "'
DIAGNOSTIC_ONCE='           "100000) == 0 && ctx.inst_count != last_dispatch_diagnostic_count) { last_dispatch_diagnostic_count = ctx.inst_count; std::cout << \\"Dispatcher PC: 0x\\" << std::hex << "'
DIAGNOSTIC_END='           "target << std::endl;\\n";'
DIAGNOSTIC_END_ONCE='           "target << std::endl; }\\n";'

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
    if out.count(DISPATCH_AFTER)==2:
        state=(out.count(HISTORY),out.count(HISTORY_ONCE),
               out.count(DIAGNOSTIC),out.count(DIAGNOSTIC_ONCE),
               out.count(DIAGNOSTIC_END),out.count(DIAGNOSTIC_END_ONCE))
        if state==(2,0,2,0,2,0):
            updated=(out.replace(HISTORY,HISTORY_ONCE,2)
                        .replace(DIAGNOSTIC,DIAGNOSTIC_ONCE,2)
                        .replace(DIAGNOSTIC_END,DIAGNOSTIC_END_ONCE,2))
            if (updated.replace(DIAGNOSTIC_END_ONCE,DIAGNOSTIC_END,2)
                       .replace(DIAGNOSTIC_ONCE,DIAGNOSTIC,2)
                       .replace(HISTORY_ONCE,HISTORY,2))!=out:
                raise ValueError('dispatcher diagnostic roundtrip')
            out=updated
        elif state!=(2,2,0,2,0,2):
            raise ValueError('ambiguous dispatcher diagnostic geometry')
    elif any(x in out for x in (HISTORY_ONCE,DIAGNOSTIC_ONCE,
                                DIAGNOSTIC_END_ONCE)):
        raise ValueError('orphan dispatcher diagnostic patch')
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
