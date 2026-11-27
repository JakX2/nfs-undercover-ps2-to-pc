#!/usr/bin/env python3
"""Original-free bounded integer-tail planner tests."""
import unittest
from audit_formatter_report_sixth_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_integer_tail import extend, CAP

NEXT = 0x60000000

def addi(dst, src, imm):
    return (14 << 26) | (dst << 21) | (src << 16) | (imm & 0xffff)

class Tests(unittest.TestCase):
    def setUp(self):
        self.base = AuditInputs('test_instruction_127_constant_reaches_128_input')
        self.base.setUp()

    def fixture(self, tail):
        sixth, *_ = self.base.inputs(next_word=tail[0])
        root = sixth[1][0]
        words = sixth[0][root][:10] + tuple(tail)
        state = [('unknown', None)] * 32
        state[1] = ('stack', 0)
        state[6] = ('const', 0xffff8000)
        return sixth, tuple(state), words

    def test_numeric_chain_and_guard(self):
        tail = [addi(7, 6, 1), addi(7, 7, 2), addi(8, 0, 3), 0x48000004, NEXT]
        fixture, live, words = self.fixture(tail)
        result, reason = extend(fixture, live, words)
        self.assertEqual(reason, 'non_integer')
        self.assertEqual([x.value for x in result.steps], [0xffff8001, 0xffff8003, 3])
        self.assertEqual(result.steps[0].inputs, ((6, 0xffff8000),))
        self.assertEqual(result.steps[1].inputs, ((7, 0xffff8001),))
        self.assertEqual(result.steps[2].inputs, ())
        self.assertEqual(result.next_word, tail[3])
        self.assertEqual(result.blocks[result.root], words[:14] + (GUARD,))
        self.assertEqual({k:v for k,v in result.blocks.items() if k != result.root},
                         {k:v for k,v in fixture[0].items() if k != result.root})

    def test_full_cap_and_end(self):
        tail = [addi(7, 0, 1)] + [addi(7, 7, 1)] * 20
        fixture, live, words = self.fixture(tail)
        result, reason = extend(fixture, live, words)
        self.assertEqual((len(result.steps), reason, result.steps[-1].value),
                         (CAP, 'cap', CAP))
        fixture, live, words = self.fixture(tail[:4])
        result, reason = extend(fixture, live, words)
        self.assertEqual((len(result.steps), reason), (3, 'function_end'))

    def test_refuse_unknown_stack_and_nonvolatile(self):
        for word, expected in ((addi(7, 8, 1), 'caller_integer_inputs'),
                               (addi(7, 1, 1), 'caller_integer_inputs'),
                               (addi(14, 0, 1), 'caller_integer_effects'),
                               (0x48000004, 'non_integer')):
            with self.subTest(word=word):
                fixture, live, words = self.fixture((word, NEXT))
                self.assertEqual(extend(fixture, live, words), (None, expected))

    def test_authentication_and_guard_mutations(self):
        fixture, live, words = self.fixture((addi(7, 0, 1), NEXT))
        root = fixture[1][0]
        for i in range(11):
            altered = words[:i] + (words[i]^1,) + words[i+1:]
            with self.subTest(i=i):
                with self.assertRaises(ValueError):
                    extend(fixture, live, altered)
        bad = ({**fixture[0], root: fixture[0][root][:-1] + (0,)}, fixture[1])
        with self.assertRaises(ValueError):
            extend(bad, live, words)
        altered = list(live); altered[6] = ('const', 0)
        with self.assertRaises(ValueError):
            extend(fixture, altered, words)
        for cap in (0, 17, True):
            with self.assertRaises(ValueError):
                extend(fixture, live, words, cap=cap)
        with self.assertRaises(ValueError):
            extend(fixture, live, words[:-1] + (GUARD,))

if __name__ == '__main__':
    unittest.main(verbosity=2)
