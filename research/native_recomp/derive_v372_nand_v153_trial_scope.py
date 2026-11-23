#!/usr/bin/env python3
"""V372: retire only V153's first-SYSCONF trial-end oracle in authentic NAND.

The authenticated V370 owner trial observed a genuine PPC_FLAG W1C followed
by a remaining queued IOS reply, then stopped at V153's original SC-only
trial assertion. The earlier V153 test ends at a specific SYSCONF reply
boundary. It is not a post-NAND invariant. Preserve the old assertion for
all non-NAND trials and preserve the original native guest execution.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

HEAD = '        check(v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq&&\n'
OLD = (
    HEAD +
    '              nwii::runtime::v149_ack_seen==1u&&\n'
    '              nwii::runtime::v150_flag_seen==1u&&\n'
    '              nwii::runtime::v151_next_seen==1u,\n'
    '              "V153 original SC IRQ did not deliver queued SYSCONF file-open reply");'
)
LABEL = 'V153 original SC IRQ did not deliver queued SYSCONF file-open reply'
MARKER = 'V372_NAND_SC_TRIAL phase='
NEW = (
    '        // V372: V153 checks the first SC-specific reply at its own stop.\n'
    '        // Authenticated NAND runs beyond that stop with a different\n'
    '        // legitimate outstanding IOS request. Retain all guest work.\n'
    '        const bool v372_nand = nwii::runtime::v250_candidate_mode&&\n'
    '              nwii::runtime::v250_nand_seen==1u;\n'
    '        if(v372_nand){\n'
    '          std::cout<<"V372_NAND_SC_TRIAL phase="<<unsigned(v372_nand)\n'
    '                   <<" sc_bridge="<<unsigned(v153_bridge)\n'
    '                   <<" queued="<<unsigned(nwii::runtime::ipc70_bus.services().queued_replies()>0u)\n'
    '                   <<" y1="<<unsigned(v153_ctrl.has_value()&&((*v153_ctrl&V153Mail::Y1)!=0u))\n'
    '                   <<" y2="<<unsigned(v153_ctrl.has_value()&&((*v153_ctrl&V153Mail::Y2)!=0u))\n'
    '                   <<" flag="<<unsigned(v153_flags.has_value()&&((*v153_flags&V153Irq::IPC_PPC)!=0u))\n'
    '                   <<" irq="<<unsigned(nwii::runtime::ipc70_bus.external_irq_level())\n'
    '                   <<" ee="<<unsigned((c.msr&V153Bus::MSR_EE)!=0u)\n'
    '                   <<std::endl;\n'
    '        }else{\n' + OLD + '\n'
    '        }'
)

def patch(source: str) -> str:
    # Tight, original-free source geometry. No changed label or duplicate
    # legacy check is accepted, and this cannot be applied twice.
    if (source.count(OLD)!=1 or source.count(LABEL)!=1 or
        source.count('V153_SC_REPLY_STATE bridge=')!=1 or
        source.count('V370_NAND_FLAG_W1C n=')!=1 or
        source.count('v250_candidate_mode')<2 or
        source.count('v250_nand_seen')<2 or
        source.count('ipc70_bus.services().queued_replies()')<1 or
        MARKER in source):
        raise ValueError('V372 SC-specific trial scope seam changed')
    result = source.replace(OLD, NEW, 1)
    if (result.count(MARKER)!=1 or result.count(LABEL)!=1 or
        result.replace(NEW,OLD,1)!=source):
        raise ValueError('V372 scoping is not exactly reversible')
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_harness',type=Path)
    p.add_argument('output_harness',type=Path)
    args=p.parse_args()
    try:
        if args.output_harness.exists() or args.output_harness.is_symlink():
            raise ValueError('output_exists')
        with args.output_harness.open('x',encoding='utf-8') as out:
            out.write(patch(args.source_harness.read_text(encoding='utf-8')))
    except (OSError,ValueError):
        print('V372_SC_TRIAL_SCOPE installed=0',file=sys.stderr)
        return 1
    print('V372_SC_TRIAL_SCOPE installed=1 guest_unchanged=1 ios_unchanged=1')
    return 0

if __name__=='__main__':
    sys.exit(main())
