import unittest
from classify_v599_arena_compile import classify
class Tests(unittest.TestCase):
    def test_only_public_basenames_and_categories(self):
        raw='/private/path/arena_cache_range_trace_v596.h:9:1: error: redefinition of confidential class\n/private/output_000.cpp:2:3: error: proprietary body\n/private/test_native_arena_sc_v598.cpp:20:5: error: no matching function private_name\n/private/test_native_arena_sc_v598.cpp:20:5: error: no matching function private_name'
        self.assertEqual(classify(raw),[('arena_cache_range_trace_v596.h',9,'redefinition'),('test_native_arena_sc_v598.cpp',20,'overload')])
if __name__=='__main__':unittest.main()
