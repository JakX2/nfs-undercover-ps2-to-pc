import unittest
from pathlib import Path
from classify_reply_compile_v1290 import classify
class Diagnostics(unittest.TestCase):
    def test_public(self):
        self.assertEqual(classify(b'/repo/test_native_scheduler_postack_v1256.cpp:861:14: error: conflicting declaration private\n'),('redeclaration','harness',861))
        self.assertEqual(classify(b'/repo/wii_reply_processor_v1280.h:24:4: error: no matching function private'),('overload','reply_witness',24))
    def test_private(self):
        self.assertEqual(classify(b'/tmp/output_12.cpp:999:8: error: cannot convert private'),('conversion','other',0))
        self.assertEqual(classify(b'/tmp/cpu_context.h:99:5: error: has no member named private'),('member','runtime_context',0))
        self.assertEqual(classify(b'private: undefined reference to original'),('link','other',0))
        self.assertEqual(classify(b'private source with no failure'),('unknown','other',0))
    def test_source_scope(self):
        s=(Path(__file__).resolve().parent/'test_native_scheduler_postack_v1256.cpp').read_text()
        self.assertIn('const auto e=v624::expected_client.edges[0];',s)
        self.assertIn('const auto reply_edge=*std::find_if',s)
        self.assertIn('JoinedIpcReplyEntry entry(v1255::handler,ReadLeaf,reply_edge,',s)
        self.assertNotIn('auto e=*std::find_if(v1255::edges',s)
if __name__=='__main__':unittest.main()
