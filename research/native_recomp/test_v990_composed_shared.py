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
class ComposedShared(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_actual_composed_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in HOST.glob('*.h'):
                if p.is_file() and not p.is_symlink():shutil.copyfile(p,root/p.name)
            shutil.copyfile(HOST/'test_shared_completion_mmio_v990.cpp',root/'probe.cpp')
            shutil.copyfile(HOST/'synthetic_shared_completion_expectations_v990.h',root/'v958_private_second_ack.h')
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
            shared=b'V989_SHARED_TIME_RESULT original_time=1 leaves=3 unchanged_msr=2 visits=12 token_preserved=1 saved_fields=38 boot_verified=0'
            post=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=15 handler_instruction_executed=0 boot_verified=0'
            modes=('valid','wrong-leaf','changed-msr','missing-shared','corrupt-abi','frame-after-ack','guard-shared','ack-only','not-enabled')
            for mode in modes:
                with self.subTest(mode=mode):
                    runenv=env.copy()
                    for k in ('UNDERCOVER_V967_POST_ACK','UNDERCOVER_V975_SECOND_TIME','UNDERCOVER_V989_SHARED_COMPLETION'):
                        runenv.pop(k,None)
                    if mode!='ack-only':runenv['UNDERCOVER_V967_POST_ACK']='1'
                    if mode not in ('ack-only','not-enabled'):runenv['UNDERCOVER_V989_SHARED_COMPLETION']='1'
                    got=subprocess.run([str(exe),mode],env=runenv,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    if mode=='valid':
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        self.assertEqual(rows,[RESULT,shared,post])
                    elif mode=='ack-only':
                        self.assertEqual(got.returncode,0);self.assertEqual(rows,[RESULT])
                    else:
                        self.assertEqual(got.returncode,126,(got.stdout+got.stderr).decode(errors='replace'))
                        self.assertEqual(rows[0],RESULT)
                        self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=(?:[1-9]|1[0-2]) stage=4 reason=[0-5] call_reason=[0-5] visits=[0-9]+$')
                        self.assertEqual(shared in rows,mode=='corrupt-abi')
                        if mode in ('guard-shared','frame-after-ack'):
                            self.assertRegex(rows[1],rb'^V989_SHARED_REFUSAL guard=[01] frame=[01] depth=1 visits=6$')
                    self.assertEqual(got.stderr,b'')
if __name__=='__main__':unittest.main()
