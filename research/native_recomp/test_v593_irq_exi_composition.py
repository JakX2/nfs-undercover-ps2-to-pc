import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from apply_exi_controller_v490 import PAIRS,MAIN_PAIRS,apply
from apply_irq_bootstrap_v475 import rewrite
HOST=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_real_updated_header(self):
        old=(HOST/'wii_irq_bank_binding_v481.h').read_text()
        new=rewrite(old,PAIRS)
        self.assertIn('MiProtect,MiAux,Exi0,Exi1,Exi2,ExiFull,Ai',new)
        self.assertIn('if(active_->banks_.mi_boot()',new)
        self.assertIn('case Reg::MiProtect:',new)
        self.assertIn('case Reg::MiAux:',new)
        self.assertEqual(rewrite(new,PAIRS),new)
        for bad in (old+old,old.replace('MiProtect,MiAux,',''),old.replace('Exi0,Exi1','Exi1,Exi0')):
            with self.assertRaises(ValueError):rewrite(bad,PAIRS)
        with TemporaryDirectory() as d:
            root=Path(d);dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
            main=root/'nWiiRuntime/src/core/main.cpp';main.parent.mkdir(parents=True)
            (dest/'wii_irq_bank_binding_v481.h').write_text(old)
            main.write_text('\n'.join(a for a,_ in MAIN_PAIRS))
            apply(root,HOST)
            self.assertEqual((dest/'wii_irq_bank_binding_v481.h').read_text(),new)
            self.assertEqual((dest/'wii_exi_controller_v489.h').read_bytes(),(HOST/'wii_exi_controller_v489.h').read_bytes())
            apply(root,HOST)
if __name__=='__main__':unittest.main()
