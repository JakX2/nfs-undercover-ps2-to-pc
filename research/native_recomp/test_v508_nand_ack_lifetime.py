import unittest
from derive_v508_nand_ack_lifetime import *
from test_v478_nand_post_return import OWNER,SIZES,CPP,RAW,HARNESS
SOURCE=HARNESS+'\n'+'\n'.join((STATE,RESET,ACK,POST,FINAL,GUARD))
HISTORY=(b'V389_NAND_FLAG_ACK before=1 wrote=1 cleared=1 down=1 y1=1 guest=1 registered=1\n'
         b'V390_NAND_POST_ACK guest=1 clear=1 registered=1 masked=1 cache=1 context=0\n'
         b'V388_NAND_BOUNDED_TRIAL kind=1 calls=44 stopped=1 completed=1\n'
         b'V389_NAND_FLAG_TRIAL y1=1 flag=1 completed=0\n')
CONTROL=HISTORY+RAW.replace(b'owner=1',b'owner=0').replace(b'V402 extended original guest frontier incomplete',ACK_GUARD.encode())
class Tests(unittest.TestCase):
    def test_route(self):
        p=eligible(OWNER,OWNER,SIZES,CPP,SOURCE,CONTROL)
        new=patch(SOURCE)
        for s in (ACK,POST,GUARD):self.assertIn(s,new)
        self.assertIn('v508_final_clear',new)
        self.assertNotIn('ctx.gpr[',new)
        self.assertNotIn('ctx.mmu.write',new)
        self.assertNotIn('ctx.pc=',new)
        for old in (STATE,RESET,ACK,POST,FINAL,GUARD):
            with self.assertRaises(ValueError):patch(SOURCE.replace(old,''))
            with self.assertRaises(ValueError):patch(SOURCE+'\n'+old)
        with self.assertRaises(ValueError):patch(new)
        for bad in (RAW,CONTROL.replace(b'down=1',b'down=0'),CONTROL.replace(b'owner=0',b'owner=1'),CONTROL.replace(b'masked=1',b'masked=0')):
            with self.assertRaises(ValueError):eligible(OWNER,OWNER,SIZES,CPP,SOURCE,bad)
        for clear in (0,1):
            marker=f'V508_NAND_ACK_TRIAL history=1 final_clear={clear} completed=1\n'.encode()
            good=CONTROL+marker
            self.assertIn(f'history=1 final_clear={clear}',outcome(good,134,OWNER,OWNER,SIZES,p))
            for bad in (CONTROL,good+marker,good.replace(b'history=1',b'history=0'),good.replace(b'call=44 pc=',b'call=45 pc=')):
                with self.assertRaises(ValueError):outcome(bad,134,OWNER,OWNER,SIZES,p)
    def test_next_guard(self):
        from tempfile import TemporaryDirectory
        label='V390 original NAND guest never left Hollywood ACK for next callee'
        source='check(ok, "'+label+'");'
        raw=('terminate called after throwing an instance of std::runtime_error\\n  what():  '+label+'\\n').encode().replace(b'\\n',b'\n')
        with TemporaryDirectory() as tmp:
            host=Path(tmp)
            (host/'derive_public.py').write_text(source,encoding='utf-8')
            (host/'test_secret.py').write_text(source,encoding='utf-8')
            rows=next_guard(raw,134,source,host,('derive_public.py','test_secret.py','../secret.py'))
            self.assertIn('class=post_ack matches=1',rows[0])
            self.assertIn('file=derive_public.py line=1',rows[1])
            self.assertNotIn(label,' '.join(rows))
            self.assertIn('matches=0',next_guard(raw,134,source,host,('test_secret.py',))[0])
            self.assertIn('class=unknown',next_guard(b'what(): private-data\n',134,source,host,('derive_public.py',))[0])
            self.assertNotIn('private-data',' '.join(next_guard(b'what(): private-data\n',134,source,host,())))
            self.assertEqual(next_guard(raw,0,source,host,()),('V517_NAND_NEXT_GUARD aborted=0 boot_verified=0',))
if __name__=='__main__':unittest.main()
