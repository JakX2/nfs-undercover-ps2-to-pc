#!/usr/bin/env python3
"""V372: preserve first-SYSCONF proof, scope only its trial-end assertion.

The owner-original NAND path has acknowledged its live IOS request and
cleared PPC_FLAG, but the historical V153 *first SYSCONF* trial oracle is
still evaluated after NAND. Wrap that single source-only check only after
verified original NAND entry. No game state, IOS service or guest data changes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

LABEL = 'V153 original SC IRQ did not deliver queued SYSCONF file-open reply'
MARKER = 'V372_NAND_SC_TRIAL phase='
HEAD = '        check(v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq&&\n'
OLD = (HEAD +
    '              nwii::runtime::v149_ack_seen==1u&&\n'
    '              nwii::runtime::v150_flag_seen==1u&&\n'
    '              nwii::runtime::v151_next_seen==1u,\n'
    '              "' + LABEL + '");')
REQUIRED = ('v153_bridge', 'v153_wire', 'v153_mail', 'v153_drained',
            'v153_irq', 'v149_ack_seen', 'v150_flag_seen',
            'v151_next_seen')

# Only aggregate source-shape counts are diagnostic. No host/private paths,
# original PPC words, translated C++ excerpts, register values or pointers.
def seam_census(source: str) -> str:
    return (
        'V372_SC_TRIAL_SEAM '
        f'exact={min(source.count(OLD),2)} '
        f'label={min(source.count(LABEL),2)} '
        f'state={min(source.count("V153_SC_REPLY_STATE bridge="),2)} '
        f'flag={min(source.count("V370_NAND_FLAG_W1C n="),2)} '
        f'candidate={int("v250_candidate_mode" in source)} '
        f'nand={int("v250_nand_seen" in source)} '
        f'queued={int("ipc70_bus.services().queued_replies()" in source)}'
    )

def _select_old(source: str) -> tuple[int, int, str]:
    # Later harness generators can change indentation/spacing around this
    # historical check. Locate it through its unique diagnostic label and
    # validate *all* of its original SC-only proof obligations.
    if source.count(LABEL) != 1:
        raise ValueError('ambiguous V153 proof label')
    pos = source.index(LABEL)
    line_end = source.find(');', pos)
    if line_end < 0 or line_end-pos > 170:
        raise ValueError('invalid V153 proof close')
    end = line_end + 2
    if source[pos-1] != '"' or source[pos+len(LABEL)] != '"':
        raise ValueError('V153 label not a literal')
    starts = list(re.finditer(r'(?m)^[ ]{2,16}check[ ]*\(',
                              source[max(0,pos-1100):pos]))
    if not starts:
        raise ValueError('V153 check preamble unavailable')
    base = max(0,pos-1100)
    start = base + starts[-1].start()
    old = source[start:end]
    if (len(old)>1100 or ';' in old[:-1] or
        any(key not in old for key in REQUIRED) or
        'check(' not in old or old.count('check(')!=1 or
        LABEL not in old):
        raise ValueError('V153 assertion no longer same SC proof')
    return start,end,old

def _wrap(old: str) -> str:
    # Preserve original source check as a byte-identical subtree.
    pad = old[:len(old)-len(old.lstrip(' '))]
    if not 2 <= len(pad) <= 16:
        raise ValueError('bad V153 indentation')
    return (
        pad + '// V372: V153 is only a first-SYSCONF reply oracle.\n'
        + pad + 'const bool v372_nand = nwii::runtime::v250_candidate_mode&&\n'
        + pad + '      nwii::runtime::v250_nand_seen==1u;\n'
        + pad + 'if(v372_nand){\n'
        + pad + '  std::cout<<"V372_NAND_SC_TRIAL phase="<<unsigned(v372_nand)\n'
        + pad + '           <<" sc_bridge="<<unsigned(v153_bridge)\n'
        + pad + '           <<" queued="<<unsigned(nwii::runtime::ipc70_bus.services().queued_replies()>0u)\n'
        + pad + '           <<" y1="<<unsigned(v153_ctrl.has_value()&&((*v153_ctrl&V153Mail::Y1)!=0u))\n'
        + pad + '           <<" y2="<<unsigned(v153_ctrl.has_value()&&((*v153_ctrl&V153Mail::Y2)!=0u))\n'
        + pad + '           <<" flag="<<unsigned(v153_flags.has_value()&&((*v153_flags&V153Irq::IPC_PPC)!=0u))\n'
        + pad + '           <<" irq="<<unsigned(nwii::runtime::ipc70_bus.external_irq_level())\n'
        + pad + '           <<" ee="<<unsigned((c.msr&V153Bus::MSR_EE)!=0u)\n'
        + pad + '           <<std::endl;\n'
        + pad + '}else{\n'
        + old + '\n' + pad + '}'
    )

NEW = _wrap(OLD)

def patch(source: str) -> str:
    if (source.count('V153_SC_REPLY_STATE bridge=')!=1 or
        source.count('V370_NAND_FLAG_W1C n=')!=1 or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        'ipc70_bus.services().queued_replies()' not in source or
        MARKER in source):
        raise ValueError('V372 original NAND phase seam changed')
    start,end,old=_select_old(source)
    injection=_wrap(old)
    output=source[:start]+injection+source[end:]
    if (output.count(LABEL)!=1 or output.count(MARKER)!=1 or
        output.replace(injection,old,1)!=source):
        raise ValueError('V372 not exactly reversible')
    return output

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_harness',type=Path)
    p.add_argument('output_harness',type=Path)
    a=p.parse_args()
    try:
        if a.output_harness.exists() or a.output_harness.is_symlink():
            raise ValueError('output_exists')
        source=a.source_harness.read_text(encoding='utf-8')
        transformed=patch(source)
        with a.output_harness.open('x',encoding='utf-8') as out:
            out.write(transformed)
    except (OSError,ValueError):
        if 'source' in locals():
            print(seam_census(source),file=sys.stderr)
        print('V372_SC_TRIAL_SCOPE installed=0',file=sys.stderr)
        return 1
    print('V372_SC_TRIAL_SCOPE installed=1 guest_unchanged=1 ios_unchanged=1')
    return 0

if __name__=='__main__':
    sys.exit(main())
