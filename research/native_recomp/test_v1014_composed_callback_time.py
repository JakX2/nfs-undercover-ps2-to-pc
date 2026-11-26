import os,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v524_si_sampling import patch_si as sampling
from prepare_v529_si_discovery import patch_si as discovery
from prepare_v672_si_ack_route import patch_si as first
from prepare_v777_transfer_return import patch_si as transfer
from prepare_v958_second_ack import patch_si as second
from prepare_v1014_second_callback_time import hook
import audit_v1014_second_callback_time as audit
HOST=Path(__file__).resolve().parent
TIME=b'V1014_CALLBACK_TIME original_return=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0'
class TimeRoute(unittest.TestCase):
    def test_hook(self):
        base='loc_80004000: ;\n    // 0x80004000: 60000000\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n'
        old='    undercover::wii::v813::before(ctx,0x80004000u,0x60000000u);\n'
        shared='    undercover::wii::v958::before(ctx,0x80004000u,0x60000000u,false);\n'
        q=hook(base+old,0x80004000,0x60000000)
        self.assertEqual(q.count('si_instruction_boundary();'),1)
        self.assertEqual(q.count('v958::before('),1)
        self.assertLess(q.index('v958::before('),q.index('v813::before('))
        self.assertEqual(hook(base+shared,0x80004000,0x60000000,True),base+shared)
        for bad in (base,base+old+old,base+shared+old):
            with self.assertRaises(ValueError):hook(bad,0x80004000,0x60000000)
    def test_audit(self):
        prefix=audit.old.RESULT
        with patch.object(audit.old,'inspect',return_value=('V1009_CALLBACK_CENSUS verified=1 prefix=1 boot_verified=0',True,prefix)):
            self.assertTrue(audit.inspect(prefix+b'\n'+TIME,0)[1])
            for data in (prefix,prefix+b'\n'+TIME+b'\n'+TIME,prefix+b'\n'+TIME.replace(b'reads=3',b'reads=4')):
                self.assertFalse(audit.inspect(data,0)[1])
        with patch.object(audit.old,'inspect',return_value=('V1009_CALLBACK_CENSUS verified=1 prefix=0 boot_verified=0',True,b'')):
            self.assertTrue(audit.inspect(b'',0)[1]);self.assertFalse(audit.inspect(TIME,0)[1])
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_composed_time(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in HOST.glob('*.h'):
                if p.is_file() and not p.is_symlink():shutil.copyfile(p,root/p.name)
            shutil.copyfile(HOST/'test_second_callback_mmio_v1009.cpp',root/'probe.cpp')
            shutil.copyfile(HOST/'synthetic_callback_time_expectations_v1014.h',root/'v813_private_callback_time.h')
            (root/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME 1\n'+(HOST/'synthetic_second_callback_expectations_v1009.h').read_text())
            source=(HOST/'wii_si_binding_v512.h').read_text()
            (root/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling(source))))))
            h=root/'wii_postack_transfer_device_v771.h';s=h.read_text();seam='\n};\n}\n'
            self.assertEqual(s.count(seam),1)
            h.write_text(s.replace(seam,'\n};\ninline thread_local PostAckTransferDevice si_transfer_device{};\n}\n'))
            exe=root/'probe'
            build=subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'probe.cpp'),'-o',str(exe)],capture_output=True,timeout=60)
            self.assertEqual(build.returncode,0,build.stderr.decode(errors='replace'))
            env=os.environ.copy()
            for k in ('V958_SECOND_ACK','V967_POST_ACK','V989_SHARED_COMPLETION','V975_SECOND_TIME','V981_SECOND_FRONTIER','V995_SUCCESS_FRONTIER','V1009_SECOND_CALLBACK','V1014_SECOND_CALLBACK_TIME'):
                env['UNDERCOVER_'+k]='1'
            for mode in ('callback-time','callback-time-offset','callback-time-frame','callback-time-result'):
                with self.subTest(mode=mode):
                    got=subprocess.run([str(exe),mode],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'')
                    self.assertIn(audit.old.RESULT,rows)
                    if mode=='callback-time':
                        self.assertEqual(got.returncode,0,got.stdout);self.assertEqual(rows[-1],TIME)
                    else:
                        self.assertEqual(got.returncode,126,got.stdout);self.assertIsNotNone(re.fullmatch(audit.FAULT,rows[-1]))
if __name__=='__main__':unittest.main()
