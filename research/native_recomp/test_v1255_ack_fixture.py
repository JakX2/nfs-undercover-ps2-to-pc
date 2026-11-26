import unittest
from make_v1255_ack_fixture import extend,analyzer,ROOT,SOURCE,IPC,ALLOWED,FORBIDDEN,BLR,ANALYZE_ROOT,READ,SCANNER
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at
class Ack(unittest.TestCase):
    def test_merge(self):
        native={pc:(0x60000000,BLR) for pc in ALLOWED}
        stop={pc:(0x60000000,) for pc in FORBIDDEN}
        raw=assemble({ROOT:(BLR,),SOURCE:(0x60000000,)*7,ALLOWED[-1]:native[ALLOWED[-1]]},ROOT)
        csv='Name,Location,Size\n'+f'func_{ROOT:08X},{ROOT:08x},4\nfunc_{ALLOWED[-1]:08X},{ALLOWED[-1]:08x},8\n'
        image,syms=extend(raw,csv,native,stop)
        for pc,ws in native.items():self.assertEqual(words_at(image,pc,len(ws)),ws)
        for pc,ws in stop.items():self.assertEqual(words_at(image,pc,2),ws+(BLR,))
        self.assertIn(f'func_{IPC:08X},{IPC:08x},8',syms)
        with self.assertRaises(ValueError):extend(raw,csv,{**native,ALLOWED[-1]:(BLR,)},stop)
        self.assertEqual(words_at(raw,ROOT,1),(BLR,))
    def test_analyzer(self):
        native={pc:(BLR,) for pc in ALLOWED};stop={pc:(BLR,) for pc in FORBIDDEN}
        src='\n'.join((ANALYZE_ROOT,READ,SCANNER))
        out=analyzer(src,native,stop)
        self.assertEqual(analyzer(out,native,stop),out)
        for pc in (*ALLOWED,*FORBIDDEN):self.assertIn(f'func.start_address==0x{pc:08x}u',out)
        with self.assertRaises(ValueError):analyzer(src,{},stop)
if __name__=='__main__':unittest.main()
