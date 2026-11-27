#!/usr/bin/env python3
"""Synthetic regressions for the authenticated 123 zero-input addi fixture."""
import unittest
from unittest.mock import patch

from audit_formatter_report_immediate_successor import Tests as AuditInputs
from guarded_continuation import GUARD
from prepare_formatter_report_signext_fixture import promote as promote_signext
from prepare_formatter_report_post_signext_immediate_fixture import (
    decode_li,plan,promote,render,
)

FOLLOWING=0x60000000


def extsb(reg=9):
    return (31<<26)|(reg<<21)|(reg<<16)|(954<<1)


def li(dst=5,value=0xff80):
    return (14<<26)|(dst<<21)|(value&0xffff)


class Original123FixtureTests(unittest.TestCase):
    def setUp(self):
        self.base=AuditInputs('test_constant_written_by_121_is_symbolic_input_to_122')
        self.base.setUp()

    def contracts(self,word=None):
        immediate,copy,predecessor,compare=self.base.inputs(extsb())
        signext=promote_signext(immediate,copy,predecessor,compare,
                               li() if word is None else word)
        return signext,immediate,copy,predecessor,compare

    def test_exact_sixth_word_and_fifth_guard_preserved(self):
        old=self.contracts()
        out=promote(*old,FOLLOWING)
        root=self.base.root
        self.assertEqual(out[0][root],(
            self.base.load,self.base.cmp,self.base.copy_word,
            self.base.imm,extsb(),li(),FOLLOWING,GUARD))
        self.assertEqual(old[0][0][root][-1],GUARD)
        self.assertEqual(out[1],(root,root+20,li(),root+24,
                                 FOLLOWING,5,0xffffff80,root+0x100))
        self.assertIn('formatter_report_post_signext_immediate_private',
                      render(out))
        self.assertIn('value=0xffffff80u',render(out))

    def test_unsigned_and_signed_immediates_and_destinations(self):
        for dst in (0,3,5,9,12):
            for imm,expected in ((0,0),(1,1),(0x7fff,0x7fff),
                                 (0x8000,0xffff8000),(0xff80,0xffffff80),
                                 (0xffff,0xffffffff)):
                with self.subTest(dst=dst,imm=imm):
                    contract=promote(*self.contracts(li(dst,imm)),FOLLOWING)
                    self.assertEqual(contract[1][5:7],(dst,expected))
                    self.assertEqual(decode_li(li(dst,imm)),(dst,expected))
                    render(contract)

    def test_reject_invalid_word_and_following_guard(self):
        for word in (GUARD,-1,0x100000000,True,li(1),
                     (14<<26)|(5<<21)|(1<<16)|3,0x60000000):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    promote(*self.contracts(word),FOLLOWING)
        for word in (GUARD,-1,0x100000000,True):
            with self.assertRaises(ValueError):
                promote(*self.contracts(),word)

    def test_reject_changed_predecessor_and_original_bytes(self):
        signext,immediate,copy,predecessor,compare=self.contracts()
        root=self.base.root
        blocks,fields=signext
        tampered=(
            ({**blocks,root:blocks[root][:-1]+(0,)},fields),
            (blocks,fields[:4]+(0,)+fields[5:]),
            (blocks,fields[:1]+(root+24,)+fields[2:]),
            (blocks,fields[:-1]+(root+28,)),
        )
        for alteration in tampered:
            with self.subTest(contract=alteration[1]):
                with self.assertRaises(ValueError):
                    promote(alteration,immediate,copy,predecessor,compare,
                            FOLLOWING)
        old=self.base.regs[:]
        old[7]=('reg',7)
        with self.assertRaises(ValueError):
            promote(signext,immediate,copy,
                    (predecessor[0],tuple(old),0),compare,FOLLOWING)
        contract=promote(signext,immediate,copy,predecessor,compare,FOLLOWING)
        f=contract[1]
        for modified in (f[:6]+(0,)+f[7:],
                         f[:3]+(root+28,)+f[4:],
                         f[:-1]+(root+28,)):
            with self.assertRaises(ValueError):
                render((contract[0],modified))

    def test_plan_pins_next_original_word_and_extent(self):
        signext,immediate,copy,predecessor,compare=self.contracts()
        root=self.base.root
        original=signext[0][root][:6]+(FOLLOWING,)
        mocks=(
            patch('prepare_formatter_report_post_signext_immediate_fixture.byte_plan',
                  return_value=predecessor),
            patch('prepare_formatter_report_post_signext_immediate_fixture.compare_plan',
                  return_value=compare),
            patch('prepare_formatter_report_post_signext_immediate_fixture.copy_plan',
                  return_value=copy),
            patch('prepare_formatter_report_post_signext_immediate_fixture.immediate_plan',
                  return_value=immediate),
            patch('prepare_formatter_report_post_signext_immediate_fixture.signext_plan',
                  return_value=signext),
            patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                  return_value={root:64}),
            patch('prepare_formatter_report_post_signext_immediate_fixture.exact_words',
                  return_value=original),
        )
        with mocks[0] as b,mocks[1] as c,mocks[2] as d,mocks[3] as e,\
             mocks[4] as f,mocks[5],mocks[6] as words:
            result=plan(b'dol',b'elf')
        self.assertEqual(result[1][6],0xffffff80)
        b.assert_called_once_with(b'dol',b'elf',with_live=True)
        c.assert_called_once_with(b'dol',b'elf',predecessor=predecessor)
        d.assert_called_once_with(b'dol',b'elf',predecessor=predecessor,compare=compare)
        e.assert_called_once_with(b'dol',b'elf',predecessor=predecessor,
                                  compare=compare,copy=copy)
        f.assert_called_once_with(b'dol',b'elf',predecessor=predecessor,
                                  compare=compare,copy=copy,immediate=immediate)
        words.assert_called_once_with(b'dol',b'elf',root,7)
        with patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                   return_value={root:24}):
            with self.assertRaisesRegex(ValueError,'report next immediate extent'):
                plan(b'a',b'b',predecessor=predecessor,compare=compare,
                     copy=copy,immediate=immediate,signext=signext)
        with patch('prepare_formatter_report_post_signext_immediate_fixture.parse_functions',
                   return_value={root:64}),\
             patch('prepare_formatter_report_post_signext_immediate_fixture.exact_words',
                   return_value=original[:5]+(0,FOLLOWING)):
            with self.assertRaisesRegex(ValueError,'report next immediate original'):
                plan(b'a',b'b',predecessor=predecessor,compare=compare,
                     copy=copy,immediate=immediate,signext=signext)


if __name__=='__main__':
    unittest.main()
