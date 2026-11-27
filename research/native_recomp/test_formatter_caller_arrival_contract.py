#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_arrival_contract import extend
from guarded_continuation import GUARD
P=0x80010000;C=0x80020000;LR=P+8;LOAD=0x80610010
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
class Arrival(unittest.TestCase):
    def setUp(self):
        self.call=bl(LR-4,C);self.words=[0x60000000,self.call,LOAD,0x60000000]
        self.blocks={P:(self.words[0],self.call,GUARD),C:(0x4e800020,GUARD)}
        self.fields=(C,LR,C,0x4e800020,48,0,0)
        self.info=(P,LR,GUARD,'load','const')
    def probe(self):return extend((self.blocks,self.fields,tuple(range(97)),tuple(range(32)),(),()),self.info,self.words)
    def test_exact(self):
        blocks,info=self.probe()
        self.assertEqual(info,(P,LR,LOAD,self.call))
        self.assertEqual(blocks[P],(self.words[0],self.call,LOAD,GUARD))
        self.assertEqual(blocks[C],self.blocks[C]);self.assertEqual(self.blocks[P][-1],GUARD)
    def test_guard(self):
        self.blocks[P]=tuple(self.words[:3])
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_call(self):
        self.words[1]^=4
        with self.assertRaisesRegex(ValueError,'call'):self.probe()
    def test_overlap(self):
        self.blocks[P]+= (0x60000000,)
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
    def test_history(self):
        self.words[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_wrong_kind(self):
        self.words[2]=0x60000000
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
    def test_wrong_owner(self):
        self.info=(C,LR,GUARD,'load','const')
        with self.assertRaisesRegex(ValueError,'identity'):self.probe()
    def test_no_following_word(self):
        self.words.pop()
        with self.assertRaisesRegex(ValueError,'guard'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
