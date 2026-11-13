#!/usr/bin/env python3
"""Source-only fix for malformed NWiiRecomp non-split dispatcher emission.

Never reads or writes original game assets. Idempotent, fail closed if emitter
source differs. Upstream's split path already uses _setjmp and a matching else.
"""
import argparse
from pathlib import Path

FILE = Path('nWiiRecomp/src/recompiler.cpp')
OLD_START = '    out << "      try {\\n";'
NEW_START = '    out << "      if (_setjmp(ctx.exception_jmp_buf) == 0) {\\n";'
OLD_END = '''    out << "        }\\n";
    out << "    }\\n";
    out << "    std::cout << \\"[DEBUG] PC History before 0x0:\\n\\";\\n";'''


def apply(root: Path):
    path = root / FILE
    old = path.read_text()
    if OLD_START not in old:
        if old.count(NEW_START) != 2:
            raise ValueError('unexpected upstream code, neither known old nor new state')
        return False
    if old.count(OLD_START) != 1:
        raise ValueError('expected unique malformed non-split try block')
    end_marker = '    out << "    std::cout << \\"[DEBUG] PC History before 0x0:'
    index = old.find(end_marker, old.index('UNKNOWN DISPATCH TO'))
    if index == -1:
        raise ValueError('unexpected missing non-split dispatcher end')
    before = '''    out << "        }\\n";
    out << "    }\\n";
'''
    pos = old.rfind(before, 0, index)
    if pos == -1 or index - pos != len(before):
        raise ValueError('unexpected non-split dispatcher closing brace layout')
    new = old.replace(OLD_START, NEW_START, 1)
    pos = new.find(before, new.find('UNKNOWN DISPATCH TO'))
    if pos == -1:
        raise ValueError('unexpected non-split end position')
    closing = '''    out << "        }\\n";
    out << "      } else {\\n";
    out << "          continue;\\n";
    out << "      }\\n";
    out << "    }\\n";
'''
    new = new[:pos] + closing + new[pos + len(before):]
    path.write_text(new)
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('upstream',type=Path)
    a=p.parse_args()
    print('Patched non-split dispatcher:', apply(a.upstream))
