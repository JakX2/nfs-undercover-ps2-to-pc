import unittest
from prepare_v1261_ipc_dispatch import render,analyzer,DISPATCH,SCHED,TIME,DISABLE,RESTORE
from prepare_v1260_scheduler_vector import ANALYZE_ROOT,READ
class Dispatch(unittest.TestCase):
    def test_render_and_ownership(self):
        handler=0x80519318
        roots={DISPATCH:[0]*169,SCHED:[0]*15,TIME:[0]*5,DISABLE:[0]*5,RESTORE:[0]*8,handler:[0,0]}
        rows=[(TIME,0x80526c84,1,2),(SCHED,0x80526c98,1,2),(DISABLE,0x80529400,1,2),(RESTORE,0x80529420,1,2)]
        g=(roots,rows,0x80526ca8,0x4e800421,handler,2,3,{handler,handler+4},-12)
        out=render(g)
        self.assertIn('counter_disp=-12',out)
        self.assertIn('handler=0x80519318u',out)
        src=ANALYZE_ROOT+'\n'+READ
        result=analyzer(src,g)
        self.assertIn('a<0x80526ce0u)return 0x80526a3cu',result)
        self.assertIn('ipc_dispatch_owner',result)
        self.assertEqual(analyzer(result,g),result)
if __name__=='__main__':unittest.main()
