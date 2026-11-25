import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v921_capture_join import patch_capture,patch_return
from prepare_v751_cold_capture import patch as first_patch
from prepare_v919_handler_epilogue import patch_binding as epilogue
from prepare_v920_handler_return import patch_binding as returned
import audit_v921_capture_join as a
HERE=Path(__file__).parent
class Join(unittest.TestCase):
    def test_capture(self):
        s=patch_capture(first_patch((HERE/'wii_external_entry_binding_v663.h').read_text()))
        self.assertLess(s.index('v921::join.attach'),s.index('V751_CAPTURE_STAGE n=2'))
        with self.assertRaises(ValueError):patch_capture(s)
    def test_return(self):
        s=patch_return(returned(epilogue((HERE/'wii_handler_suffix_binding_v868.h').read_text())))
        self.assertLess(s.index('v726::witness.resumed'),s.index('v921::join.returned'))
        with self.assertRaises(ValueError):patch_return(s)
    def test_audit(self):
        base=[a.capture.RESULT,a.old.RETURN,a.RETURN]
        with patch('audit_v751_cold_capture.inspect',return_value=('',True)),patch('audit_v920_handler_return.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(base),0)[1])
            for rows in (base[:-1],base[::-1],base+[a.RETURN],base+[a.capture.CAPTURE[0]],[a.RETURN,*base],base+[b'V921_unknown']):
                self.assertFalse(a.inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(base),126)[1])
if __name__=='__main__':unittest.main()
