import unittest
from pathlib import Path
from prepare_v868_handler_suffix import lane,render,patch_ack,patch_return,verify_handler_label
from prepare_v863_combined_callback import patch_binding
HERE=Path(__file__).parent
H=0x80004000;NOP=0x60000000;CALL=0x48000101
class HandlerSuffix(unittest.TestCase):
    def test_lane(self):
        rows=lane(H,[NOP,CALL],H,(2,0,0,((1,1),)))
        self.assertEqual(rows,{H:(NOP,0,0),H+4:(CALL,1,1)})
        self.assertIn('after6',render((rows,rows)))
        with self.assertRaises(ValueError):lane(H,[NOP,CALL],H,(3,0,0,((1,1),)))
    def test_resume_label(self):
        p=H;w=NOP
        label=f'loc_{p:X}: ;\n    // 0x{p:08X}: {w:08X}\n'
        dispatch=f'    undercover::wii::v850::dispatch_resume(ctx,0x{p:08x}u,0x{w:08x}u);\n'
        tick='    ++ctx.inst_count;\n'
        si='    ctx.si_instruction_boundary();\n'
        resume=f'    undercover::wii::v850::handler_resume(ctx,0x{p:08x}u,0x{w:08x}u);\n'
        hook=f'    undercover::wii::v672::before(ctx,0x{p:08x}u,0x{w:08x}u,0u,0u);\n'
        verify_handler_label(label+dispatch+tick+si+resume+hook,p,w,0,0,True)
        verify_handler_label(label+tick+si+hook,p,w,0,0,False)
        for body,is_resume in ((label+tick+si+resume+hook,True),
            (label+dispatch+tick+si+hook+resume,True),
            (label+dispatch+tick+resume+si+hook,True),
            (label+dispatch+tick+si+resume+hook,False),
            (label+tick+si+hook+resume,False),
            (label+dispatch.replace('0x60000000u','0x60000001u')+tick+si+resume+hook,True),
            (label+dispatch+tick+tick+si+resume+hook,True),
            (label+dispatch+tick+si+resume+hook+hook,True)):
            with self.subTest(body=body):
                with self.assertRaises(ValueError):verify_handler_label(body,p,w,0,0,is_resume)
    def test_patch_return(self):
        s=patch_binding((HERE/'wii_callback_return_binding_v850.h').read_text())
        t=patch_return(s)
        self.assertIn('captured_tick=c.inst_count',t)
        self.assertIn('if(!continue_handler())std::_Exit(0);',t)
        with self.assertRaises(ValueError):patch_return(t)
    def test_ack(self):
        s=(HERE/'wii_si_ack_binding_v672.h').read_text().replace('#include "wii_si_binding_v512.h"','#include "wii_si_binding_v512.h"\n#include "wii_si_handler_return_binding_v726.h"').replace('observe(uint32_t,C&){','observe(uint32_t a,C& c){')
        t=patch_ack(s)
        self.assertIn('if(v868::before(c,pc,word,ordinal,kind))return;',t)
        self.assertIn('if(v868::active())return v868::poll(c);',t)
        with self.assertRaises(ValueError):patch_ack(t)
if __name__=='__main__':unittest.main()
