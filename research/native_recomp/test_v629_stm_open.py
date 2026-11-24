import struct,unittest
from prepare_v629_stm_open import paths_at,render,patch_probe,INCLUDE,DECL,END,PATHS,expected_scopes,coverage,STM,STM_SIZE,OPEN
from test_v628_startup_census import ALL,log
from audit_v629_stm_open import inspect,STAGES
RESULT=b'V629_STM_RESULT entry=1 open=1 pathname=1 mode=0 native_transport=1 serviced=0 actual_ios=0 fallback=0 boot_verified=0'
class Tests(unittest.TestCase):
    def test_paths(self):
        d=bytearray(256);blob=PATHS[0]+PATHS[1]
        for off,v in ((0x1c,256),(0x64,0x80600000),(0xac,len(blob))):struct.pack_into('>I',d,off,v)
        d+=blob
        self.assertEqual(paths_at(d),[(0x80600000,1),(0x80600000+len(PATHS[0]),2)])
        with self.assertRaises(ValueError):paths_at(d[:-1])
        for x in (b'\0'*len(blob),):
            with self.assertRaises(ValueError):paths_at(d[:256]+x)
        h=render(((1,)*7,(2,), (3,4,5,6),(7,8,9,10),paths_at(d),11))
        self.assertIn('std::array<StmPath,8>{',h)
        self.assertEqual(h.count('StmPath{'),2)
    def test_coverage(self):
        scopes=expected_scopes((1,)*7,(2,)*(STM_SIZE//4),(OPEN,0,0,3))
        self.assertEqual({k:len(v) for k,v in scopes.items()},{'bridge':7,'prefix':23,'open':1,'post':47})
        root=STM;pc=STM+4
        g={'prefix':{pc:(root,0x60000000)},'open':{OPEN:(OPEN,3)}}
        s=f'void fn_{root:08X}(CPUContext& ctx) {{\nloc_{pc:X}: ;\n    // 0x{pc:08X}: 60000000\n    ++ctx.inst_count;\n}}\n'
        self.assertEqual(coverage([s],g),({'prefix':(1,1),'open':(0,1)},0,0))
        self.assertEqual(coverage([s,s],g),({'prefix':(0,1),'open':(0,1)},1,0))
        self.assertEqual(coverage([s.replace('60000000','00000000')],g),({'prefix':(0,1),'open':(0,1)},0,1))
    def test_patch(self):
        old='\n'.join((INCLUDE,DECL,END));s=patch_probe(old)
        self.assertIn('stm_prefix.begin(cpu,true)',s);self.assertEqual(s.count('std::_Exit(0)'),1)
        for bad in (old+old,s,old.replace(END,'')):
            with self.assertRaises(ValueError):patch_probe(bad)
    def test_audit(self):
        good=ALL+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad in (good[:-1],good+[RESULT],good+[b'V425_HARDWARE_FALLBACK hit=1'],
                    good+[b'V625_IPC_STAGE n=19'],ALL+STAGES+[RESULT.replace(b'mode=0',b'mode=1')],
                    ALL+STAGES[::-1]+[RESULT]):
            self.assertFalse(inspect(log(bad),0)[1])
        self.assertFalse(inspect(log(good),121)[1])
        self.assertIn('V629_STM_INVALID reason=5 stage=2',inspect(log(ALL+STAGES[:2]+[b'V629_STM_INVALID reason=5 stage=2']),121)[0])
if __name__=='__main__':unittest.main()
