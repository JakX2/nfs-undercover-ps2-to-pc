import unittest,struct
from make_v626_ipc_fixture import assemble,NOP
from prepare_v419_full_start import words_at
class Tests(unittest.TestCase):
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
