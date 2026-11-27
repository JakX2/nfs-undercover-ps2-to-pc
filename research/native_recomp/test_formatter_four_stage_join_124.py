#!/usr/bin/env python3
"""Joined original-free execution-model regression for formatter 121..124.

Tests the *same* authenticated predecessor through four consecutive integer
steps, rather than treating each private fixture as an independent snapshot.
The PPC words and addresses below are fabricated synthetic test inputs.
This is never an original-Wii execution test.
"""
import unittest

from audit_formatter_report_second_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_report_third_immediate_fixture import promote


def run_chain(contracts):
    """Replay the four guarded operations, recording all intermediate states."""
    second, signext, first, copy, predecessor, compare = contracts
    byte, regs, saved = predecessor
    gpr = list(regs)
    load, byte_value = byte[1][1], byte[1][4]
    gpr[(load >> 21) & 31] = ('const', byte_value)
    gpr = tuple(gpr)
    after_compare, compare_inputs = step(
        byte[1][6], gpr, saved_mask=saved)
    after_copy, copy_inputs = step(
        copy[1][2], after_compare,
        saved_mask=saved, allow_stack_copy=True)
    after_121, first_inputs = step(
        first[1][2], after_copy, saved_mask=saved)
    after_122, signed_inputs = step(
        signext[1][2], after_121, saved_mask=saved)
    after_123, second_inputs = step(
        second[1][2], after_122, saved_mask=saved)
    return ((after_compare, after_copy, after_121, after_122, after_123),
            (compare_inputs, copy_inputs, first_inputs,
             signed_inputs, second_inputs))


class FourStageJoinedState(unittest.TestCase):
    def setUp(self):
        self.audit = AuditInputs(
            'test_second_immediate_constant_reaches_next_original_word')
        self.audit.setUp()
        self.root = self.audit.base.root

    def run_promoted(self, next_word=None, source=9, following=0x60000000):
        if next_word is None:
            next_word = self.audit.addi(6, 0, 0xff80)
        original = self.audit.inputs(next_word=next_word, source=source)
        contract = promote(*original, following)
        stages, read_traces = run_chain(original)
        _, after_124_inputs = step(
            next_word, stages[-1], saved_mask=original[4][2])
        return original, contract, stages, read_traces, after_124_inputs

    def test_exact_join_and_frame_lease(self):
        original, output, stages, traces, inputs = self.run_promoted()
        second, signext, first, copy, predecessor, compare = original
        self.assertEqual(len(output[0][self.root]), 9)
        self.assertEqual(output[0][self.root][-2:], (0x60000000, GUARD))
        self.assertEqual(output[0][self.root][:-2],
                         second[0][self.root][:-1])
        self.assertEqual(stages[0][1], ('stack', -864))
        self.assertEqual(stages[1][10], ('stack', -864))
        self.assertEqual(stages[2][3], ('const', 0xfffffffe))
        self.assertEqual(stages[3][9], ('const', 0x5a))
        self.assertEqual(stages[4][11], ('const', 0xfffffffe))
        self.assertEqual(traces[1:], ((), (), ((9, 0x5a),), ()))
        self.assertEqual(inputs, ())
        after_124, _ = step(
            output[1][2], stages[-1], saved_mask=predecessor[2])
        self.assertEqual(after_124[6], ('const', output[1][6]))
        self.assertEqual(output[1][6], 0xffffff80)
        self.assertEqual(after_124[1], ('stack', -864))

    def test_all_byte_values_survive_original_step_order(self):
        for byte in range(256):
            with self.subTest(byte=byte):
                blocks, fields = self.audit.base.byte
                self.audit.base.byte = (
                    blocks, fields[:4] + (byte,) + fields[5:])
                original, contract, stages, traces, inputs = self.run_promoted()
                expected = byte if byte < 128 else 0xffffff00 | byte
                self.assertEqual(stages[3][9], ('const', expected))
                self.assertEqual(traces[3], ((9, byte),))
                self.assertEqual(stages[4][11], ('const', 0xfffffffe))
                self.assertEqual(contract[1][6], 0xffffff80)
                self.assertEqual(inputs, ())

    def test_121_to_122_alias_and_later_overwrite_are_ordered(self):
        # The 122 extsb may source 121's destination (r3), or the
        # earlier authenticated load (r9). 123 can overwrite r9 AFTER 122.
        self.audit.base.imm = self.audit.addi(3, 0, 0x80)
        self.audit.original_123 = self.audit.addi(9, 0, 0xfffe)
        for source in (3, 9):
            with self.subTest(source=source):
                original, contract, stages, traces, _ = self.run_promoted(
                    next_word=self.audit.addi(9, 0, 0x7fff),
                    source=source)
                self.assertEqual(stages[3][source],
                                 ('const', 0xffffff80) if source == 3 else
                                 ('const', 0x5a))
                self.assertEqual(stages[4][9], ('const', 0xfffffffe))
                after, _ = step(contract[1][2], stages[-1],
                                saved_mask=original[4][2])
                self.assertEqual(after[9], ('const', 0x7fff))
                self.assertEqual(after[3], ('const', 0xffffff80))
                self.assertEqual(contract[1][6], 0x7fff)

    def test_unknown_successor_is_guarded_not_speculatively_executed(self):
        original, output, stages, traces, _ = self.run_promoted(
            following=0xffffffff)
        self.assertEqual(output[0][self.root][-2:],
                         (0xffffffff, GUARD))
        self.assertEqual(stages[-1][11], ('const', 0xfffffffe))
        self.assertEqual(output[1][4], 0xffffffff)
        for word in (GUARD, -1, 0x100000000, True):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*original, word)

    def test_overlapping_return_or_tampered_old_word_rejected(self):
        original = self.audit.inputs(next_word=self.audit.addi(6, 0, 0xff80))
        second, signext, immediate, copy, predecessor, compare = original
        blocks, fields = second
        for position in range(7):
            forged = list(blocks[self.root])
            forged[position] ^= 1
            if position == 7:
                continue
            with self.subTest(position=position):
                with self.assertRaises(ValueError):
                    promote(({**blocks, self.root: tuple(forged)}, fields),
                            signext, immediate, copy, predecessor, compare,
                            0x60000000)
        with self.assertRaises(ValueError):
            promote((blocks, fields[:-1] + (self.root + 32,)),
                    signext, immediate, copy, predecessor, compare,
                    0x60000000)


if __name__ == '__main__':
    unittest.main()
