import unittest,struct
from make_v1243_stm_fixture import data_at,seed_data,extend,SDA,PATHS,BLR
from make_v626_ipc_fixture import assemble
from make_v624_ipc_geometry import ROOT
from prepare_v419_full_start import words_at

class Fixture(unittest.TestCase):
    def test_data(self):
        addr=SDA[13]+16;path=addr+8
        raw=bytearray(256)
        data=b'\x11\x22\x33\x44'+b'\0'*4+PATHS[0]
        for off,v in ((0x1c,256),(0x64,addr),(0xac,len(data))):struct.pack_into('>I',raw,off,v)
        raw+=data
        self.assertEqual(data_at(raw,addr,4),data[:4])
        self.assertIsNone(data_at(raw,addr-8,4))
        ins=(32<<26)|(13<<16)|16
        self.assertEqual(bytes(seed_data(raw,(ins,),[(path,1)])[addr+i] for i in range(4)),data[:4])
        for paths in ([(path,2)],[(path,3)],[(path+1,1)]):
            with self.assertRaises(ValueError):seed_data(raw,(ins,),paths)
    def test_extend(self):
        raw=assemble({ROOT:(BLR,)},ROOT)
        csv=f'Name,Location,Size\nfunc_{ROOT:08X},{ROOT:08x},4\n'
        stm=ROOT+0x100;op=(ROOT+0x200,0,0,0x60000000);prefix=(0x60000000,)*23
        image,symbols=extend(raw,csv,stm,op,prefix)
        self.assertEqual(words_at(image,ROOT,1),(BLR,))
        self.assertEqual(words_at(image,stm,24),prefix+(BLR,))
        self.assertEqual(words_at(image,op[0],2),(op[3],BLR))
        self.assertEqual(len(symbols.splitlines()),4)
        with self.assertRaises(ValueError):extend(raw,csv,ROOT,op,prefix)
        with self.assertRaises(ValueError):extend(raw,csv,stm,op,prefix[:-1])
if __name__=='__main__':unittest.main()
