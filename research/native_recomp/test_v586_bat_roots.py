import unittest
from unittest.mock import patch
from audit_v584_bat_translation import MAPS
import make_v586_bat_roots as p
from apply_bat_roots_v586 import PAIRS
from apply_irq_bootstrap_v475 import rewrite
class Tests(unittest.TestCase):
    def test_plan(self):
        funcs={0x8000403c+4*i:4 for i in range(25000)}
        funcs[MAPS[0][0]]=MAPS[0][1]-MAPS[0][0]
        def words(data,pc,n):return tuple([0x60000000]*n)
        def read(data,pc,n):return list(words(data,pc,n))
        with patch.object(p,'geometry'),patch.object(p.hashlib,'sha256') as sha,patch.object(p,'parse_functions',return_value=funcs),patch.object(p,'words_at',side_effect=words),patch.object(p,'read_words',side_effect=read),patch.object(p,'direct_bl',return_value=0x80527550):
            sha.return_value.hexdigest.return_value='digest'
            out,stats=p.plan(b'dol',b'elf','digest','digest')
            self.assertEqual(stats,(1,32,2))
            self.assertEqual(len(out),len(funcs)+2)
            for a,b,_ in MAPS:self.assertGreaterEqual(out[a],b-a)
            self.assertNotIn(MAPS[1][0],funcs)
            with patch.object(p,'read_words',return_value=[0]):
                with self.assertRaises(ValueError):p.plan(b'dol',b'elf','digest','digest')
    def test_analyzer_patch(self):
        src='\n'.join(a for a,b in PAIRS)
        out=rewrite(src,PAIRS)
        self.assertEqual(rewrite(out,PAIRS),out)
        self.assertEqual(out.count('terminal RFI'),1)
        for bad in (src+src,src.replace(PAIRS[1][0],'')):
            with self.assertRaises(ValueError):rewrite(bad,PAIRS)
if __name__=='__main__':unittest.main()
