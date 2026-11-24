import unittest
from pathlib import Path
import tempfile
from apply_irq_bootstrap_v475 import MAIN_PAIRS,STUB_PAIRS,rewrite,apply
from apply_native_ios_mmio_v418 import PAIRS as MMIO,HEADERS
from apply_native_ios_width_v421 import PAIRS as WIDTH
from apply_hollywood_mmio_v62 import OLD
class Tests(unittest.TestCase):
    def test_roundtrip(self):
        for pairs in (MAIN_PAIRS,STUB_PAIRS):
            source='\n'.join(a for a,_ in pairs)
            out=rewrite(source,pairs)
            self.assertEqual(rewrite(out,pairs),out)
            for a,b in reversed(pairs):out=out.replace(b,a,1)
            self.assertEqual(out,source)
            for a,_ in pairs:
                for bad in (source.replace(a,'missing',1),source+'\n'+a):
                    with self.assertRaises(ValueError):rewrite(bad,pairs)
    def test_atomic_composition(self):
        with tempfile.TemporaryDirectory() as td:
            rt=Path(td)/'nWiiRuntime'
            main=rt/'src/core/main.cpp';stubs=rt/'src/core/os_hle_stubs.cpp'
            ctx=rt/'include/runtime/cpu_context.h';dest=rt/'include/undercover'
            main.parent.mkdir(parents=True);ctx.parent.mkdir(parents=True);dest.mkdir()
            source={main:'\n'.join(a for a,_ in MAIN_PAIRS),
                    stubs:'\n'.join(a for a,_ in MMIO)+'\n'+STUB_PAIRS[-1][0],
                    ctx:OLD+'\n'+'\n'.join(a for a,_ in WIDTH)}
            for path,data in source.items():path.write_text(data,encoding='utf-8')
            (dest/'wii_exception_vector_witness_v457.h').write_text('original-free predecessor')
            host=Path(__file__).parent
            bad=dest/HEADERS[0];bad.write_text('conflicting header')
            with self.assertRaises(ValueError):apply(Path(td),host)
            self.assertEqual({p:p.read_text() for p in source},source)
            bad.unlink()
            apply(Path(td),host)
            self.assertIn('irq_boot_trace.record',stubs.read_text())
            self.assertIn('NativeIosBinding::check_cpu_access',ctx.read_text())
            self.assertIn('NativeIosTransport transport',main.read_text())
            self.assertTrue(all((dest/n).read_bytes()==(host/n).read_bytes() for n in (*HEADERS,'wii_irq_bootstrap_v475.h')))
    def test_opt_in(self):
        main=rewrite('\n'.join(a for a,_ in MAIN_PAIRS),MAIN_PAIRS)
        self.assertIn('UNDERCOVER_V419_START',main)
        self.assertIn('NativeIosBinding binding(transport)',main)
        self.assertNotIn('service_at_guest_boundary',main)
        self.assertEqual(main.count('run_game(*ctx);'),2)
        stubs=rewrite('\n'.join(a for a,_ in STUB_PAIRS),STUB_PAIRS)
        self.assertIn('record(addr,val,32u,true)',stubs)
        self.assertIn('record(addr,val,32u,false)',stubs)
        self.assertIn('record(addr,val,16u,false)',stubs)
if __name__=='__main__':unittest.main()
