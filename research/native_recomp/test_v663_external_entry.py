import unittest
from prepare_v663_external_entry import patch_probe,patch_ios,HEADER,PROBE,START,CALLBACK,IOS_INCLUDE
class Tests(unittest.TestCase):
    def test_patch(self):
        s='\n'.join((HEADER,PROBE,START))
        out=patch_probe(s)
        self.assertIn('v663::observe(addr,cpu)',out)
        self.assertIn('v663::begin(cpu,irq_cause,irq_mask)',out)
        self.assertIn(START,out)
        for x in (out,s+s,s.replace(START,'')):
            with self.assertRaises(ValueError):patch_probe(x)
        t=IOS_INCLUDE+'\n'+CALLBACK
        self.assertIn('return undercover::wii::v663::poll(ctx);',patch_ios(t))
        with self.assertRaises(ValueError):patch_ios(t+t)
if __name__=='__main__':unittest.main()
