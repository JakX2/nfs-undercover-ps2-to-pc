#!/usr/bin/env python3
"""Original-free regressions for the private 119 comparison fixture gate."""
import unittest
from unittest.mock import patch
from prepare_formatter_report_compare_fixture import plan

from guarded_continuation import GUARD
from prepare_formatter_report_compare_fixture import promote, render

ROOT = 0x80010000
LOAD = (34 << 26) | (9 << 21) | (7 << 16) | 1
NEXT = 0x60000000
RETURN = ROOT + 0x100


def comparison(op=11, field=3, reg=9, immediate=0x5a):
    return (op << 26) | (field << 23) | (reg << 16) | immediate


def contract(*, word=None, value=0x5a, root=ROOT, load=LOAD, ret=RETURN,
             blocks=None):
    if word is None:
        word = comparison()
    if blocks is None:
        blocks = {root: (load, word, GUARD)}
    return blocks, (root, load, 753, 17, value, root+4, word, ret)


class CompareFixtureTests(unittest.TestCase):
    def test_signed_unsigned_fields_and_all_byte_values(self):
        count = 0
        for op in (10, 11):
            for field in range(8):
                for byte in range(256):
                    prior = contract(word=comparison(op, field, 9, byte),
                                     value=byte)
                    old = {root: words for root, words in prior[0].items()}
                    expanded, fields = promote(prior, NEXT, (9, byte))
                    self.assertEqual(expanded[ROOT],
                                     (LOAD, comparison(op, field, 9, byte),
                                      NEXT, GUARD))
                    self.assertEqual(fields[2:], (ROOT+8, NEXT, 9, byte, RETURN))
                    self.assertEqual(prior[0], old)
                    self.assertIn('source_value=', render((expanded, fields)))
                    count += 1
        self.assertEqual(count, 4096)

    def test_history_and_opcode_refusals(self):
        cases = [
            contract(word=comparison(11, 3, 8)),
            contract(word=comparison(11, 3, 9) | 0x00200000),
            contract(word=comparison(11, 3, 9) | 0x00400000),
            contract(word=comparison(14, 3, 9)),
            contract(value=True),
            contract(value=256),
            contract(root=ROOT+1),
            contract(root=0x817ffff4),
            contract(ret=ROOT+8),
            contract(blocks={ROOT: (LOAD, comparison())}),
            contract(blocks={ROOT: (LOAD, comparison(), NEXT)}),
            contract(blocks={ROOT: (LOAD, comparison(), GUARD),
                             ROOT+8: (GUARD,)}),
        ]
        for item in cases:
            with self.subTest(case=item[1][:2]):
                with self.assertRaises(ValueError):
                    promote(item, NEXT, (9, 0x5a))

    def test_successor_refusals(self):
        for successor in (GUARD, -1, 0x100000000, True, None, 'code'):
            with self.subTest(successor=successor):
                with self.assertRaises(ValueError):
                    promote(contract(), successor, (9, 0x5a))

    def test_plan_reuses_original_byte_contract(self):
        prior=contract(word=comparison(10,4,7,0x8000))
        counts=(1,0,1,0,0,0,1,0,0,0,0)
        source=(7,0x81234567)
        with patch('prepare_formatter_report_compare_fixture.successor_plan',
                   return_value=(prior,('compare_immediate',counts,(), 'supported',source))) as owner, \
             patch('prepare_formatter_report_compare_fixture.parse_functions',
                   return_value={ROOT:16}), \
             patch('prepare_formatter_report_compare_fixture.exact_words',
                   return_value=(LOAD,comparison(10,4,7,0x8000),NEXT)):
            expanded,details=plan(b'fixture',b'elf')
        owner.assert_called_once_with(b'fixture',b'elf',return_input=True,include_byte=True)
        self.assertEqual(details[4:6],source)
        self.assertEqual(expanded[ROOT][-2:],(NEXT,GUARD))

    def test_non_byte_compare_source_and_full_width_value(self):
        # The predecessor byte load changes r9; the comparison reads r7.
        source = (7, 0x81234567)
        prior = contract(word=comparison(10, 4, 7, 0x8000))
        out, fields = promote(prior, NEXT, source)
        self.assertEqual(fields[4:6], source)
        self.assertEqual(out[ROOT], (LOAD, comparison(10,4,7,0x8000), NEXT, GUARD))
        self.assertIn('source_value=0x81234567u', render((out, fields)))

    def test_provenance_mismatch_and_invalid_source(self):
        wrong = contract(word=comparison(11, 3, 7, 5))
        with self.assertRaisesRegex(ValueError, 'input identity'):
            promote(wrong, NEXT, (9, 0x5a))
        for source in ((7, True), (7, -1), (7, 0x100000000),
                       (32, 0), (False, 1), ('7', 1), [7, 1], None):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, 'source provenance'):
                    promote(wrong, NEXT, source)

    def test_callee_guard_isolated_from_siblings(self):
        sibling = ROOT + 0x200
        old = {ROOT: (LOAD, comparison(), GUARD),
               sibling: (0x60000000, GUARD)}
        out, fields = promote(contract(blocks=old), NEXT, (9, 0x5a))
        self.assertEqual(out[sibling], old[sibling])
        self.assertEqual(out[ROOT+0] if ROOT+0 in out else (), out[ROOT])
        self.assertEqual(fields[0], ROOT)
        self.assertEqual(len(out), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
