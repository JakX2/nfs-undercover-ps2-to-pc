import unittest,struct
from make_v626_ipc_fixture import assemble,NOP,backward_polls
from prepare_v419_full_start import words_at
class Tests(unittest.TestCase):
    def test_poll_geometry(self):
        p=0x80510000
        # Hand-authored independent instructions: forward, backward,
        # self, out-of-function, and absolute branches.
        b=lambda d:0x48000000|(d&0x03fffffc)
        bc=lambda d:0x41820000|(d&0xfffc)
        self.assertEqual(backward_polls({p:(b(4),bc(-4),b(0),b(-32),b(0)|2,0x4e800020)}),[p+4,p+8])
        self.assertEqual(backward_polls({p:(NOP,0x4e800020),p+16:(b(-16),0x4e800020)}),[])
        with self.assertRaises(ValueError):backward_polls({p:(b(0),)*129})
    def test_isolated_sections(self):
        start=0x80510000
        blocks={start:(0x4e800020,),start+16:(0x4e800020,)}
        d=assemble(blocks,start)
        self.assertEqual(struct.unpack_from('>I',d,0xe0)[0],start)
        self.assertEqual(words_at(d,start,5),(0x4e800020,NOP,NOP,NOP,0x4e800020))
        for b,e in (({},start),(blocks,start+4),({start:(1,2),start+4:(3,)},start),
                    ({start:(1,),start+0x50000:(2,)},start),({start:()},start)):
            with self.assertRaises(ValueError):assemble(b,e)
if __name__=='__main__':unittest.main()
