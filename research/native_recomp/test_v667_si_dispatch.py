import unittest
from unittest.mock import patch
from prepare_v667_si_dispatch import route_geometry,patch_binding,patch_trace,DISPATCH,SCHED,TIME,DISABLE,RESTORE,BIND_INCLUDE,POLL,OBSERVE,END,TRACE_INCLUDE,TRACE
from audit_v667_si_dispatch import inspect,EVENTS,RESULT
def bl(site,target):return 0x48000001|((target-site)&0x03fffffc)
class Tests(unittest.TestCase):
    def test_geometry(self):
        d=[0x60000000]*(0x2a4//4);s=[0x60000000]*(0x3c//4)
        for pc,t in ((0x80526c80,TIME),(0x80526c94,SCHED)):d[(pc-DISPATCH)//4]=bl(pc,t)
        d[(0x80526ca8-DISPATCH)//4]=0x4e800421
        s[1]=bl(SCHED+4,DISABLE);s[9]=bl(SCHED+36,RESTORE)
        edges,indirect=route_geometry(d,s)
        self.assertEqual([x[1] for x in edges],[TIME,SCHED,DISABLE,RESTORE])
        self.assertEqual(indirect,(0x80526ca8,0x4e800421))
        for i in (0,(0x80526c80-DISPATCH)//4,(0x80526ca8-DISPATCH)//4):
            bad=d[:];bad[i]=0x4e800421 if i==0 else 0
            with self.assertRaises(ValueError):route_geometry(bad,s)
    def test_patches(self):
        raw='\n'.join((BIND_INCLUDE,POLL,OBSERVE,END))
        out=patch_binding(raw)
        self.assertIn('v667::begin(c)',out);self.assertIn('v667::poll(c)',out)
        for bad in (out,raw+raw,raw.replace(END,'')):
            with self.assertRaises(ValueError):patch_binding(bad)
        src=TRACE_INCLUDE+'\n'+TRACE
        self.assertIn('si_dispatch_pi_reads.record',patch_trace(src))
        with self.assertRaises(ValueError):patch_trace(src+src)
    def test_audit(self):
        seq=EVENTS+[RESULT]
        with patch('audit_v667_si_dispatch.inspect_external',return_value=('ok',True)):
            self.assertTrue(inspect(b'\n'.join(seq),0)[1])
            for bad in (seq[:-1],seq+seq,seq[:2]+seq[3:],seq+[b'V425_HARDWARE_FALLBACK hit=1']):
                # A late preceding marker is rejected by the tail comparison.
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(seq),125)[1])
if __name__=='__main__':unittest.main()
