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
    def test_explicit_sc_extension_cap(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(53)}
        d=assemble(blocks,start,max_roots=53)
        self.assertEqual(words_at(d,start,53),(0x4e800020,)*53)
        for cap in (32,51,52,62):
            with self.subTest(cap=cap),self.assertRaises(ValueError):
                assemble(blocks,start,max_roots=cap)
        with self.assertRaises(ValueError):
            assemble({**blocks,start+53*4:(0x4e800020,)},start,max_roots=53)
    def test_version_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(55)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=55),start,55),(0x4e800020,)*55)
        for cap in (53,54,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
    def test_report_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(56)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=56),start,56),(0x4e800020,)*56)
        for cap in (54,55,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
    def test_report_helper_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(57)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=57),start,57),(0x4e800020,)*57)
        for cap in (55,56,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
    def test_report_resume_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(58)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=58),start,58),(0x4e800020,)*58)
        for cap in (56,57,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
    def test_formatter_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(59)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=59),start,59),(0x4e800020,)*59)
        for cap in (57,58,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
    def test_formatter_continuation_roots(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(60)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=60),start,60),(0x4e800020,)*60)
        for cap in (32,59,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
        with self.assertRaises(ValueError):assemble({**blocks,start+60*4:(0x4e800020,)},start,max_roots=60)
    def test_explicit_next_callee_root(self):
        start=0x80510000
        blocks={start+4*i:(0x4e800020,) for i in range(61)}
        self.assertEqual(words_at(assemble(blocks,start,max_roots=61),start,61),(0x4e800020,)*61)
        for cap in (32,60,62):
            with self.assertRaises(ValueError):assemble(blocks,start,max_roots=cap)
        with self.assertRaises(ValueError):
            assemble({**blocks,start+61*4:(0x4e800020,)},start,max_roots=61)
        with self.assertRaises(ValueError):
            assemble({**blocks,start+0x50000:(0x4e800020,)},start,max_roots=61)
        with self.assertRaises(ValueError):
            assemble({**blocks,start+4:(0x4e800020,0x4e800020)},start,max_roots=61)
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
