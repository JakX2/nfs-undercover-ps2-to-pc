import unittest
from make_v1245_open_fixture import merge,ROOT,OPEN,STM,SOURCE,BLR,FIRST_OPEN_CALL
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
class Merge(unittest.TestCase):
    def fixture(self):
        vec=tuple(0x60000000+i for i in range(7))
        body={ROOT:(BLR,),OPEN:(0x60000000,BLR)}
        raw=assemble({**body,SOURCE:vec},ROOT)
        csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(body.items()))
        prefix=tuple(0x60000000+i for i in range((FIRST_OPEN_CALL-STM)//4+1))
        stm=assemble({ROOT:(BLR,),STM:prefix+(BLR,)},ROOT)
        return raw,csv,stm,prefix,vec
    def test_preserve(self):
        raw,csv,stm,prefix,vec=self.fixture()
        out,symbols=merge(raw,csv,stm)
        self.assertEqual(words_at(out,ROOT,1),(BLR,))
        self.assertEqual(words_at(out,OPEN,2),(0x60000000,BLR))
        self.assertEqual(words_at(out,SOURCE,7),vec)
        self.assertEqual(words_at(out,STM,24),prefix+(BLR,))
        self.assertIn(f'func_{STM:08X},{STM:08x},96',symbols)
    def test_refuse(self):
        raw,csv,stm,_,_=self.fixture()
        for bad in (csv+csv.splitlines()[1]+'\n',csv.replace(f'func_{OPEN:08X}', 'bad'),
                    csv.splitlines()[0]+'\n'+csv.splitlines()[1]+'\n'):
            with self.assertRaises(ValueError):merge(raw,bad,stm)
if __name__=='__main__':unittest.main()
