import subprocess,tempfile,unittest
from pathlib import Path
from classify_open_compile_v654 import classify
HERE=Path(__file__).parent
class Tests(unittest.TestCase):
    def test_duplicate_copies(self):
        h=(HERE/'open_cache_range_trace_v649.h').read_text()
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);(d/'runtime').mkdir()
            (d/'runtime/cache.h').write_text(h);(d/'cache.h').write_text(h)
            (d/'probe.cpp').write_text('#include "runtime/cache.h"\n#include "cache.h"\nint main(){undercover::wii::OpenCacheRangeTrace t;return int(t.lines());}\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only',str(d/'probe.cpp')],check=True)
    def test_classification(self):
        self.assertEqual(classify(b'error: redefinition of class OpenCacheRangeTrace'),'cache_header_duplicate')
        self.assertEqual(classify(b'undefined reference to private_symbol'),'link')
        self.assertEqual(classify(b'error: has no member named'),'missing_member')
        self.assertEqual(classify(b'error: other private detail'),'compile_other')
if __name__=='__main__':unittest.main()
