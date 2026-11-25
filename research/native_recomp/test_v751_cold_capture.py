import unittest
from unittest.mock import patch as mock
from pathlib import Path
from prepare_v751_cold_capture import patch
from audit_v751_cold_capture import inspect,CAPTURE,EVENTS,RESULT
HOST=Path(__file__).parent
class Capture(unittest.TestCase):
    def test_installer(self):
        src=(HOST/'wii_external_entry_binding_v663.h').read_text()
        out=patch(src)
        self.assertIn('route.poll(c,pi_intsr.load(),pi_intmr.load(),capture)',out)
        self.assertIn('route.poll(c,pi_intsr.load(),pi_intmr.load());',out)
        self.assertIn('capture.witness().saved_integer(c,ColdExternalEntry::Thread)',out)
        self.assertLess(out.index('saved_integer'),out.index('V663_EXTERNAL_RESULT'))
        self.assertIn('std::_Exit(0);',out)
        for bad in (out,src+src,src.replace('if(route.stage()==6)','if(route.stage()==5)')):
            with self.assertRaises(ValueError):patch(bad)
    def test_audit_order(self):
        rows=EVENTS[:2]+CAPTURE[:1]+EVENTS[2:]+CAPTURE[1:]+[RESULT]
        with mock('audit_v663_external_entry.inspect_arena',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-2]+[RESULT],rows+[CAPTURE[0]],CAPTURE+EVENTS+[RESULT],rows[:2]+rows[3:]+[CAPTURE[0]]):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(rows),124)[1])
if __name__=='__main__':unittest.main()
