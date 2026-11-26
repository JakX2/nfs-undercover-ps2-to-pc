#!/usr/bin/env python3
import unittest
import struct
from unittest.mock import patch
from make_private_elf_symbol_map import HEADER,SECTION
from analyze_formatter_nested_path import nested,immutable_read
from prepare_post_stm_sc_report_formatter_path import const
R=0x80001000;T=0x80002000;L=0x80003000
def ins(op,r,a,v):return (op<<26)|(r<<21)|(a<<16)|(v&0xffff)
def bl(a,z):return 0x48000001|((z-a)&0x03fffffc)
class Nested(unittest.TestCase):
    def setUp(self):
        self.gp=[('reg',i) for i in range(32)]
        self.gp[1]=('stack',-128);self.gp[3]=('stack',-112)
        self.mem={-112+i:('byte',v) for i,v in enumerate((0,0,0,42))}
        self.state=((),{}, {},None,None,0,frozenset())
        self.ws=(ins(37,1,1,-48),0x7c0802a6,ins(36,0,1,52),ins(32,4,3,0),bl(R+16,T))
    def test_inherited_stack_read(self):
        p=nested(R,self.ws,self.gp,self.mem,self.state,(),L)
        self.assertEqual((p[1],p[4],p[5][4]),(48,T,const(42)))
        self.assertEqual(p[6][-112],('byte',0));self.assertEqual(p[6][-121],('byte',0))
        self.assertEqual(len(p[2]),3)
    def test_missing_data(self):
        with self.assertRaisesRegex(ValueError,'stack read provenance'):
            nested(R,self.ws,self.gp,{},self.state,(),L)
    def test_parent_overwrite(self):
        m={**self.mem,-124:('byte',0)}
        with self.assertRaisesRegex(ValueError,'duplicate stack write'):
            nested(R,self.ws,self.gp,m,self.state,(),L)
    def test_outer_linkage(self):
        m={**self.mem,**{4+i:('part',('lr',0),4,i) for i in range(4)}}
        p=nested(R,self.ws,self.gp,m,self.state,(),L)
        self.assertEqual(p[6][7],m[7])
        with self.assertRaisesRegex(ValueError,'nested memory geometry'):
            nested(R,self.ws,self.gp,{**m,8:('byte',0)},self.state,(),L)
    def test_immutable_data(self):
        addr=0x80010000
        ident=b'\x7fELF\x01\x02\x01'+bytes(9)
        def elf(flags):
            return HEADER.pack(ident,2,20,1,0,0,52,0,52,0,0,40,1,0)+SECTION.pack(0,1,flags,addr,92,4,0,0,4,0)+b'\x00\x00\x00\x2a'
        with patch('analyze_formatter_nested_path.data_at',return_value=b'\x00\x00\x00\x2a'):
            self.assertEqual(immutable_read(b'',elf(2),addr,4),b'\x00\x00\x00\x2a')
            for flags in (3,6):
                with self.assertRaisesRegex(ValueError,'not immutable'):
                    immutable_read(b'',elf(flags),addr,4)
        with patch('analyze_formatter_nested_path.data_at',return_value=bytes(4)):
            with self.assertRaisesRegex(ValueError,'data identity'):
                immutable_read(b'',elf(2),addr,4)
    def test_resolved_read(self):
        self.gp[3]=const(0x80010000)
        p=nested(R,self.ws,self.gp,self.mem,self.state,(),L,read_resolver=lambda a,n:bytes((0,0,0,42)))
        self.assertEqual(p[5][4],const(42))
        with self.assertRaisesRegex(ValueError,'data read provenance'):
            nested(R,self.ws,self.gp,self.mem,self.state,((0x80010001,b'x'),),L,read_resolver=lambda a,n:bytes(4))
    def test_out_of_frame(self):
        m={**self.mem,-132:('byte',0)}
        with self.assertRaisesRegex(ValueError,'nested memory geometry'):
            nested(R,self.ws,self.gp,m,self.state,(),L)
if __name__=='__main__':unittest.main(verbosity=2)
