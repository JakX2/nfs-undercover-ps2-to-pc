import unittest
from prepare_v668_si_ack import shape,patch_binding,HANDLER,INCLUDE,WRITE,is_word_store
class Tests(unittest.TestCase):
    def test_geometry(self):
        words=[0x90030000,0x48000009,0x4e800421,0x4e800020]
        stores,calls,indirect=shape(HANDLER,words)
        self.assertEqual(stores,(HANDLER,))
        self.assertEqual(calls,((HANDLER+4,HANDLER+12),))
        self.assertEqual(indirect,(HANDLER+8,))
        self.assertTrue(is_word_store(0x94030004))
        self.assertFalse(is_word_store(0x80030000))
        for bad in ([],[0x60000000]*4,[0]*1025):
            with self.assertRaises(ValueError):shape(HANDLER,bad)
    def test_seam(self):
        src=INCLUDE+'\n'+WRITE+'si_sampling_trace.si(true,*off,value);si_discovery_trace.mmio(true,*off,value);'
        out=patch_binding(src)
        self.assertIn('si_completion_ack_trace.write(active_->controller_,*off,value);',out)
        self.assertIn('si_discovery_trace.mmio',out)
        for bad in (out,src+src,src.replace(WRITE,'')):
            with self.assertRaises(ValueError):patch_binding(bad)
if __name__=='__main__':unittest.main()
