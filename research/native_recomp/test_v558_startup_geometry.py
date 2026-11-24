import hashlib
import unittest
from unittest.mock import patch
from audit_v558_startup_geometry import inspect
from test_v556_audio_reset import fixture
from test_v468_exception_pack_geometry import digest,put
from prepare_v556_audio_reset import STOP as AUDIO_STOP
from prepare_v549_thread_init import INDIRECT
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_full(self,_):
        raw=fixture()
        self.assertEqual(inspect(raw,digest(raw)),(('si','sram','thread','audio'),'none'))
        for pc,want in ((AUDIO_STOP,(('si','sram','thread'),'audio')),(INDIRECT,(('si','sram'),'thread'))):
            bad=bytearray(raw);put(bad,pc,0)
            self.assertEqual(inspect(bad,digest(bad)),want)
        with self.assertRaises(ValueError):inspect(raw,'0'*64)
    def test_stop_on_failure(self):
        raw=bytes(256);seen=[]
        def yes(d,s):seen.append('yes')
        def no(d,s):raise ValueError('private detail')
        self.assertEqual(inspect(raw,hashlib.sha256(raw).hexdigest(),(('si',yes),('sram',no),('thread',yes))), (('si',),'sram'))
        self.assertEqual(seen,['yes'])
if __name__=='__main__':unittest.main()
