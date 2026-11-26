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
class ComposedSecondCallback(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_actual_composed_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in HOST.glob('*.h'):
                if p.is_file() and not p.is_symlink():shutil.copyfile(p,root/p.name)
            shutil.copyfile(HOST/'test_second_callback_mmio_v1009.cpp',root/'probe.cpp')
            shutil.copyfile(HOST/'synthetic_second_callback_expectations_v1009.h',root/'v958_private_second_ack.h')
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
            time=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=12 handler_instruction_executed=0 boot_verified=0'
            for mode in ('callback','callback-unknown','callback-unmapped','callback-corrupt','callback-unaligned','callback-unguarded','callback-frame','callback-channel','callback-no-poll','callback-stack','callback-save-corrupt','direct','direct-mismatch','shared-only'):
                with self.subTest(mode=mode):
                    runenv=env.copy()
                    runenv['UNDERCOVER_V967_POST_ACK']='1';runenv['UNDERCOVER_V989_SHARED_COMPLETION']='1'
                    for k in ('UNDERCOVER_V975_SECOND_TIME','UNDERCOVER_V981_SECOND_FRONTIER','UNDERCOVER_V995_SUCCESS_FRONTIER'):
                        runenv.pop(k,None)
                        if mode!='shared-only':runenv[k]='1'
                    runenv['UNDERCOVER_V1009_SECOND_CALLBACK']='1' if mode!='shared-only' else '0'
                    got=subprocess.run([str(exe),mode],env=runenv,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(rows[:3],[RESULT,shared,post],(got.stdout+got.stderr).decode(errors='replace'))
                    if mode=='shared-only':
                        self.assertEqual(got.returncode,0);self.assertEqual(len(rows),3)
                    elif mode in ('callback-unguarded','callback-frame'):
                        self.assertEqual(got.returncode,126);self.assertEqual(len(rows),4)
                        self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=13 stage=4 reason=[0-5] call_reason=[0-5] visits=[0-9]+$')
                    elif mode in ('callback-channel','callback-no-poll','callback-stack','callback-save-corrupt'):
                        self.assertEqual(got.returncode,126,(got.stdout+got.stderr).decode(errors='replace'))
                        self.assertEqual(len(rows),5)
                        self.assertRegex(rows[3],rb'^V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0$')
                        self.assertRegex(rows[4],rb'^V958_ACK_INVALID kind=14 stage=4 reason=[0-5] call_reason=[0-5] visits=[0-9]+$')
                    elif mode.startswith('callback'):
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        category={'callback':2,'callback-unknown':1,'callback-unmapped':3,'callback-corrupt':4,'callback-unaligned':2}[mode]
                        expected=f'V995_CALLBACK_FRONTIER target_class={category} aligned={int(mode!="callback-unaligned")} visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'.encode()
                        if mode=='callback':
                            self.assertEqual(rows[3:],[expected,b'V1009_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=8 visits=13 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0'])
                        else:self.assertEqual(rows[3:],[expected])
                    else:
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        match=int(mode=='direct')
                        expected=f'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match={match} callback_known=1 admitted={match} visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'.encode()
                        self.assertEqual(rows[3:],[time,expected])
                    self.assertEqual(got.stderr,b'')
if __name__=='__main__':unittest.main()
