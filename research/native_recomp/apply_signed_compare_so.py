#!/usr/bin/env python3
"""Fail-closed signed-immediate compare CR.SO emitter correction.

The pinned NWiiRecomp emitter writes LT/GT/EQ but omits XER.SO for cmpi.
This owner-authored source patch does not read or modify guest code. Apply
only to the supported upstream layout, before recompiling generated code.
"""
import argparse
import re
import unittest
from pathlib import Path

TARGET = Path('nWiiRecomp/src/recompiler.cpp')
# Restrict the match to the signed immediate compare emitter, and require
# the exact known final EQ statement and the next opcode dispatch arm.
ANCHOR = r'(?m)^  \} else if \(ppc_inst\.opcode\(\) == 11\) \{[ \t]*\n'
END = r'(?m)^  \} else if \(ppc_inst\.opcode\(\) == 34\) \{[ \t]*\n'
EQ = ('    out << "    ctx.cr[" << crD << "].eq = ((int32_t)ctx.gpr[" << ppc_inst.ra()\n'
      '        << "] == " << ppc_inst.simm() << ");\\n";\n')
SO = ('    out << "    ctx.cr[" << crD << "].so = ((ctx.xer >> 31u) & 1u) != 0u;\\n";\n')


def rewrite(source):
    starts = list(re.finditer(ANCHOR, source))
    if len(starts) != 1:
        raise ValueError('unsupported signed compare emitter layout')
    lo = starts[0].end()
    # The pinned upstream also has an earlier opcode-34 arm. Restrict
    # the end delimiter to the very next top-level dispatch arm.
    end = re.search(r'(?m)^  \} else if \(', source[lo:])
    if end is None:
        raise ValueError('unsupported signed compare emitter layout')
    hi = lo + end.start()
    if not re.compile(END).match(source, hi):
        raise ValueError('unsupported signed compare emitter layout')
    body = source[lo:hi]
    if (body.count(EQ) != 1 or body.count('uint32_t crD = ppc_inst.rd() >> 2;') != 1
            or body.count('<< crD << "].lt =') != 1
            or body.count('<< crD << "].gt =') != 1):
        raise ValueError('unsupported signed compare emitter layout')
    if body.endswith(EQ + SO) and body.count(SO) == 1 and body.count('].so =') == 1:
        return source
    if not body.endswith(EQ) or '].so =' in body:
        raise ValueError('unsupported signed compare emitter layout')
    return source[:hi] + SO + source[hi:]


def apply(root):
    path = root / TARGET
    source = path.read_text(encoding='utf-8')
    patched = rewrite(source)
    if patched == source:
        return False
    path.write_text(patched, encoding='utf-8')
    return True


class Tests(unittest.TestCase):
    def fixture(self):
        # Synthetic C++ emitter-shaped text, not translated game code.
        return ('  } else if (ppc_inst.opcode() == 11) { \n'
                '    uint32_t crD = ppc_inst.rd() >> 2;\n'
                '    out << "    ctx.cr[" << crD << "].lt = test;\\n";\n'
                '    out << "    ctx.cr[" << crD << "].gt = test;\\n";\n'
                + EQ + '  } else if (ppc_inst.opcode() == 34) { \n')

    def test_exact_insert_idempotent(self):
        original = self.fixture()
        patched = rewrite(original)
        self.assertEqual(patched, original.replace(EQ, EQ + SO))
        self.assertEqual(rewrite(patched), patched)
        self.assertEqual(patched.count(SO), 1)

    def test_missing_duplicate_or_modified_layout_refused(self):
        original = self.fixture()
        for bad in (original + original, original.replace(EQ, ''),
                    original.replace('opcode() == 11', 'opcode() == 10'),
                    original.replace('opcode() == 34', 'opcode() == 35'),
                    original.replace(EQ, EQ + EQ),
                    original.replace(EQ, EQ + SO + SO),
                    original.replace(EQ, EQ + SO.replace('31u', '30u')),
                    original.replace('].lt =', '].other =')):
            with self.subTest(case=bad[:60]):
                with self.assertRaises(ValueError):
                    rewrite(bad)

    def test_earlier_duplicate_opcode_34_arm_is_unchanged(self):
        earlier = '  } else if (ppc_inst.opcode() == 34) { \n'
        original = earlier + self.fixture()
        patched = rewrite(original)
        self.assertEqual(patched, earlier + rewrite(self.fixture()))
        self.assertEqual(rewrite(patched), patched)

    def test_no_other_opcode_changed(self):
        original = self.fixture()
        surrounding = 'unrelated preamble\n' + original + 'other emitter\n'
        self.assertEqual(rewrite(surrounding).replace(SO, ''), surrounding)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream_root', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if args.upstream_root is None:
        parser.error('upstream_root required')
    try:
        changed = apply(args.upstream_root)
    except (OSError, ValueError):
        print('SIGNED_COMPARE_SO_PATCH verified=0')
        return 1
    print(f'SIGNED_COMPARE_SO_PATCH verified=1 changed={int(changed)} original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
