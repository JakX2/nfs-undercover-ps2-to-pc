import unittest
from prepare_v1169_third_ack import verify_label,verify_bus,render
from prepare_v1097_after_alarm import patch_label,SI
from prepare_v958_second_ack import patch_label as old
from prepare_v1048_third_alarm import hook
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
T='    ++ctx.inst_count;\n'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'+T+SI
class ThirdAckLabels(unittest.TestCase):
    def test_labels(self):
        for guard in (False,True):
            body=old(L+f'    undercover::wii::v672::before({A},0u,0u);\n',H,W,'v672',guard)
            for good in (body,patch_label(body,H,W),patch_label(hook(body,H,W),H,W)):
                verify_label(good,H,W)
                for bad in (good.replace(T,T+T),good.replace(SI,''),good.replace('v958::before','v958::wrong'),
                            good.replace('0x60000000u','0x60000001u'),good+f'    undercover::wii::v958::before({A},false);\n'):
                    with self.assertRaises(ValueError):verify_label(bad,H,W)
    def test_bus(self):
        from pathlib import Path
        from test_v997_composed_success_frontier import first,second,transfer,discovery,sampling,HOST
        s=second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text())))))
        verify_bus(s)
        for bad in (s.replace('held_epilogue.ack_read','held_epilogue.wrong'),s.replace('held_epilogue.ack_write','held_epilogue.wrong'),
                    s.replace('next_device.stage()!=3u','next_device.stage()!=2u'),s.replace('#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK','#ifdef WRONG')):
            with self.assertRaises(ValueError):verify_bus(bad)
    def test_render(self):
        s=render([(H,H+4,0),(H+8,H+12,1)],[(H,H+8)],[(H,W,H,False),(H+8,W,H+8,True)])
        self.assertIn('ThirdAckNativeLabel,2> labels',s)
        self.assertIn('0x80004008u,true}',s)
if __name__=='__main__':unittest.main()
