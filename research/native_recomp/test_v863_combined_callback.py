import unittest
from pathlib import Path
from prepare_v861_wireless_write import patch_label as write_label,patch_wrapper as write_wrapper,patch_ack as write_ack
from prepare_v863_combined_callback import patch_label,patch_wrapper,patch_ack,patch_binding,patch_write
from test_v850_callback_return import LABEL,SI,OLD,PC,W,HANDLER
from prepare_v813_callback_time import verify_order
HERE=Path(__file__).parent
class Combined(unittest.TestCase):
    def test_shared_restore(self):
        for old in (LABEL+OLD+SI,LABEL+SI+OLD,LABEL+SI):
            new=patch_label(write_label(old,PC,W),PC,W,'restore')
            verify_order(new,PC,W,'v847');verify_order(new,PC,W,'v850')
            if OLD in old:self.assertIn('if(!undercover::wii::v847::active()&&!undercover::wii::v850::active()) '+OLD.strip(),new)
        bad=write_label(LABEL+SI+OLD,PC,W).replace('v847::before','v999::before')
        with self.assertRaises(ValueError):patch_label(bad,PC,W,'restore')
    def test_wrapper(self):
        src=(HERE/'wii_wireless_wrapper_binding_v847.h').read_text()
        new=patch_wrapper(write_wrapper(src))
        self.assertIn('v861::after(c,old,route);',new)
        self.assertIn('if(route.changed()){v850::start(c,pc,w,true);return;}',new)
        self.assertIn('v861::device.held()',new)
        with self.assertRaises(ValueError):patch_wrapper(new)
    def test_write(self):
        src=(HERE/'wii_wireless_write_binding_v861.h').read_text()
        new=patch_write(src)
        self.assertIn('if(!continue_callback())std::_Exit(0);',new)
        with self.assertRaises(ValueError):patch_write(new)
    def test_ack(self):
        s='template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){\n    if(v847::active())v847::reject(3);\nif(v847::observe(a,c))return;'
        new=patch_ack(write_ack(s))
        self.assertLess(new.index('v850::poll'),new.index('v847::route.poll'))
        self.assertIn('if(v850::observe(a,c))return;if(v847::observe(a,c))return;',new)
    def test_binding(self):
        s=(HERE/'wii_callback_return_binding_v850.h').read_text()
        new=patch_binding(s)
        self.assertIn('v861::payload(c)==profile->sram()',new)
        self.assertEqual(new.count('v861::device.observe(c.inst_count)'),2)
        self.assertEqual(new.count('v861::device.observe_dispatch(c.inst_count)'),1)
        self.assertEqual(new.count('si_transfer_device.held_now()'),1)
        with self.assertRaises(ValueError):patch_binding(new)
if __name__=='__main__':unittest.main()
