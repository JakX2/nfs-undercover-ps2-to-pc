#!/usr/bin/env python3
"""Owner-free canonical V125 pipeline and overlap guards."""
from pathlib import Path
import unittest
from restore_sc_helper_late_v125 import ENTRY,MAX_SPAN,NEXT_KNOWN
HERE=Path(__file__).resolve().parent

class CanonicalFixture(unittest.TestCase):
    def test_restore_order_and_owner_authentication(self):
        s=(HERE/"make_v125_canonical_fixture.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",s)
        self.assertIn("text_at(fixture,OS_CALL,4)!=text_at(raw,OS_CALL,4)",s)
        self.assertEqual(s.count("text_at(fixture,OS_CALL,4)"),1)
        order=("v86(","v89(","v91(","v93(","v94(","v95(","v96(","v97(","v99(",
               "v100(","v101(","v102(","v103(","v104(","restore_helper(")
        positions=[s.index("fixture="+q) if q=="v86(" else s.index("fixture="+q) if q!="restore_helper(" else s.index("result=restore_helper(")
                   for q in order]
        self.assertEqual(positions,sorted(positions))
        self.assertEqual(NEXT_KNOWN-ENTRY,MAX_SPAN)
        self.assertNotIn("print(raw)",s)
    def test_shell_uses_canonical_fixture_after_v104(self):
        from derive_v125_sc_helper_runner import derive
        s=derive((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn('make_v125_canonical_fixture.py',s)
        self.assertIn('python3 "$here/make_start_to_ipc_ack_v77.py"',s)
        self.assertLess(s.index("V104_STAGE geometry_verified"),s.index("V125_CANONICAL result=verified"))
        self.assertIn('derive_v125_sc_helper_generator.py',s)
        self.assertIn("V125_CANONICAL result=verified",s)
if __name__=="__main__":
    unittest.main()
