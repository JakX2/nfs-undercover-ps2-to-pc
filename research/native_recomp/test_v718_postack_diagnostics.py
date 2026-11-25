import unittest
from audit_v709_os_leaves import public_diagnostic
from prepare_v709_os_leaves import patch_poll

class Diagnostics(unittest.TestCase):
    def test_private_output_allowlist(self):
        valid=[
            b'V672_SI_ACK_INVALID reason=4 trace=0',
            b'V672_SI_ACK_INVALID reason=5 trace=11',
            b'V673_SI_ACK_CALL ordinal=0 kind=0',
            b'V718_POSTACK_REFUSAL kind=1 region=2 backward=1 masked=1 second=2 nested=4 leaves=3',
            b'V718_POSTACK_REFUSAL kind=2 region=0 backward=0 masked=1 second=2 nested=4 leaves=3',
        ]
        for line in valid:
            self.assertTrue(public_diagnostic(line))
            self.assertFalse(public_diagnostic(line+b' pc=0x80000000'))
            self.assertFalse(public_diagnostic(b'private '+line))
        for line in (valid[-1].replace(b'region=0',b'region=4'),
                     valid[-1].replace(b'leaves=3',b'leaves=4'),
                     valid[-1].replace(b'kind=2',b'kind=0'),
                     valid[-1].replace(b'masked=1',b'masked=2')):
            self.assertFalse(public_diagnostic(line))
    def test_exact_patch_and_no_relaxed_guard(self):
        source=('template<class C>bool poll(C& c){\n    reject(4);\n}\n'
                'template<class C>void observe(uint32_t a,C& c){if(v680::observe(a,c)||v688::observe(a,c))return;reject(5);}')
        result=patch_poll(source)
        self.assertIn('postack_refusal(c,c.pc,1);\n    reject(4);',result)
        self.assertIn('postack_refusal(c,a,2);reject(5);',result)
        self.assertIn('if(v709::active)return v709::poll(c);',result)
        with self.assertRaises(ValueError):patch_poll(result)

if __name__=='__main__':unittest.main()
