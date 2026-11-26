#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_queue import render
class Queue(unittest.TestCase):
    def test_header(self):
        p=((0x80001000,0x80001020,0x80002000,0x8000102c,0x60000000,0x80003000),
           (0x80003000,8),[(0x80001000,0x80001020,0x60000000)],(2,1))
        s=render(p)
        self.assertIn('std::array<undercover::wii::IpcDispatchWord,1>',s)
        self.assertIn('AllocatorRange{0x80003000u,0x00000008u}',s)
        self.assertIn('ScQueueExpectation expected',s)
if __name__=='__main__':unittest.main(verbosity=2)
