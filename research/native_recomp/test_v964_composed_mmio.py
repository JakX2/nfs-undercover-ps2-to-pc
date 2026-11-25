import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from prepare_v524_si_sampling import patch_si as sampling
from prepare_v529_si_discovery import patch_si as discovery
from prepare_v672_si_ack_route import patch_si as first
from prepare_v777_transfer_return import patch_si as transfer
from prepare_v958_second_ack import patch_si as second
HOST=Path(__file__).resolve().parent
RESULT=b'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=6 reads=1 writes=1 boot_verified=0'
POST=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=2 handler_instruction_executed=0 boot_verified=0'
class ComposedMmio(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_actual_composed_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in HOST.glob('*.h'):
                if p.is_file() and not p.is_symlink():shutil.copyfile(p,root/p.name)
            shutil.copyfile(HOST/'test_second_ack_mmio_v964.cpp',root/'probe.cpp')
            shutil.copyfile(HOST/'synthetic_second_ack_expectations_v959.h',root/'v958_private_second_ack.h')
            source=(HOST/'wii_si_binding_v512.h').read_text()
            (root/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling(source))))))
            h=root/'wii_postack_transfer_device_v771.h';s=h.read_text()
            seam='\n};\n}\n'
            self.assertEqual(s.count(seam),1)
            h.write_text(s.replace(seam,'\n};\ninline thread_local PostAckTransferDevice si_transfer_device{};\n}\n'))
            exe=root/'probe'
            build=subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'probe.cpp'),'-o',str(exe)],capture_output=True,timeout=60)
            self.assertEqual(build.returncode,0,build.stderr.decode(errors='replace'))
            env=os.environ.copy();env['UNDERCOVER_V958_SECOND_ACK']='1'
            for mode in ('valid','mirror','frame','guard','entry','return','read','write','width','offset','default','post','post-return'):
                with self.subTest(mode=mode):
                    runenv=env.copy()
                    runenv.pop('UNDERCOVER_V967_POST_ACK',None)
                    if mode=='default':runenv.pop('UNDERCOVER_V958_SECOND_ACK')
                    if mode in ('post','post-return'):runenv['UNDERCOVER_V967_POST_ACK']='1'
                    got=subprocess.run([str(exe),mode],env=runenv,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    if mode in ('valid','mirror'):
                        self.assertEqual(got.returncode,0,got.stderr.decode(errors='replace'));self.assertEqual(rows,[RESULT])
                    elif mode=='post':
                        self.assertEqual(got.returncode,0,got.stderr.decode(errors='replace'));self.assertEqual(rows,[RESULT,POST])
                    elif mode=='post-return':
                        self.assertEqual(got.returncode,126,got.stderr.decode(errors='replace'));self.assertEqual(rows[0],RESULT)
                        self.assertRegex(rows[1],rb'^V958_ACK_INVALID kind=1 stage=4 reason=0 call_reason=3 visits=[0-9]+$')
                    elif mode=='default':
                        self.assertEqual(got.returncode,0);self.assertEqual(rows,[b'V964_DEFAULT inactive=1'])
                    else:
                        self.assertEqual(got.returncode,126,got.stderr.decode(errors='replace'))
                        self.assertEqual(len(rows),1)
                        self.assertRegex(rows[0],rb'^V958_ACK_INVALID kind=[1-8] stage=[0-3] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}$')
                        if mode in ('width','offset'):self.assertIn(b'kind=8 ',rows[0])
                    self.assertEqual(got.stderr,b'')
            print('V964_COMPOSED_MMIO valid=2 disabled=1 refused=8 actual_binding=1 original_execution=0')
            print('V967_LIVE_POST_ACK valid=1 refused=1 actual_binding=1 original_execution=0')
if __name__=='__main__':unittest.main()
