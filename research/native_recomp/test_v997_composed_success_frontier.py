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
class ComposedSuccessFrontier(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_actual_composed_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in HOST.glob('*.h'):
                if p.is_file() and not p.is_symlink():shutil.copyfile(p,root/p.name)
            shutil.copyfile(HOST/'test_success_frontier_mmio_v997.cpp',root/'probe.cpp')
            (root/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1025_PRIVATE_TRANSFER 1\n'+(HOST/'synthetic_success_frontier_expectations_v997.h').read_text())
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
            for mode in ('callback','callback-unknown','callback-unmapped','callback-corrupt','callback-unaligned','callback-unguarded','callback-frame','direct','direct-mismatch','shared-only','error-callback','error-callback-short','error-direct','error-success','error-third','error-third-mismatch','error-third-frame','error-third-stale','error-third-word','error-third-mask','error-third-unarmed','error-third-native','error-third-native-entry','error-third-native-skip','error-third-native-word','error-third-native-abi','error-third-native-data','error-third-native-srr','error-abi-exact','error-abi-tail','error-abi-core','error-abi-changed'):
                with self.subTest(mode=mode):
                    runenv=env.copy()
                    runenv['UNDERCOVER_V967_POST_ACK']='1';runenv['UNDERCOVER_V989_SHARED_COMPLETION']='1'
                    for k in ('UNDERCOVER_V975_SECOND_TIME','UNDERCOVER_V981_SECOND_FRONTIER','UNDERCOVER_V995_SUCCESS_FRONTIER'):
                        runenv.pop(k,None)
                        if mode!='shared-only':runenv[k]='1'
                    if mode.startswith('error-'):
                        runenv['UNDERCOVER_V1015_ERROR_COMPLETION']='1'
                        runenv['UNDERCOVER_V1021_ERROR_FRONTIER']='1'
                    if mode.startswith('error-abi'):
                        runenv['UNDERCOVER_V1034_QUEUE_DETAIL']='1';runenv['UNDERCOVER_V1040_SIX_ARGS']='1'
                    got=subprocess.run([str(exe),mode],env=runenv,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    if mode.startswith('error-abi'):
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        admission={'error-abi-exact':1,'error-abi-tail':2,'error-abi-core':0,'error-abi-changed':0}[mode]
                        self.assertEqual(rows[-1],f'V1040_TRANSFER_ABI admission={admission} timing_only={int(admission==2)} unchanged_slot={int(mode!="error-abi-changed")} call_executed=0 boot_verified=0'.encode())
                        self.assertEqual(got.stderr,b'')
                        continue
                    if mode.startswith('error-third'):
                        from audit_v1015_error_completion import RESULT as ERROR
                        self.assertIn(ERROR,rows)
                        if mode.startswith('error-third-native'):
                            self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                            expected=b'V1030_NATIVE_ROUTE verified=1 entries=4 returns=4 visits=21 token=3 original_execution=0' if mode=='error-third-native' else b'V1030_NATIVE_ROUTE refused=1 original_execution=0'
                            self.assertEqual(rows[-1],expected)
                        elif mode=='error-third':
                            self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                            self.assertEqual(rows[-1],b'V1025_THIRD_HANDOFF original_execution=0 token=3 completed=1 exclusive_device=1 duplicate_refused=1 reads=1 writes=3')
                        elif mode=='error-third-unarmed':
                            self.assertEqual(got.returncode,126,got.stdout)
                            self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=17 stage=5 reason=0 call_reason=0 visits=[0-9]+$')
                        else:
                            self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                            self.assertEqual(rows[-1],b'V1025_THIRD_HANDOFF refused=1 mutation=0 token=2 original_execution=0')
                        self.assertEqual(got.stderr,b'')
                        continue
                    if mode.startswith('error-'):
                        from audit_v1015_error_completion import RESULT as ERROR
                        from audit_v1021_error_frontier import DIRECT,INDIRECT
                        if mode=='error-success':
                            self.assertEqual(got.returncode,126,(got.stdout+got.stderr).decode(errors='replace'))
                            self.assertNotIn(ERROR,rows)
                        else:
                            self.assertEqual(rows[:3],[RESULT,post.replace(b'visits=15',b'visits=130'),ERROR],(got.stdout+got.stderr).decode(errors='replace'))
                            if mode=='error-callback-short':
                                self.assertEqual(got.returncode,126)
                                self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=16 stage=4 reason=0 call_reason=0 visits=[0-9]+$')
                            elif mode=='error-callback':
                                self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                                self.assertEqual(rows[3:],[INDIRECT,b'V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'])
                            else:
                                self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                                self.assertEqual(rows[3:],[time,DIRECT,b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=1 callback_known=1 admitted=1 visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'])
                        self.assertEqual(got.stderr,b'')
                        continue
                    self.assertEqual(rows[:3],[RESULT,shared,post],(got.stdout+got.stderr).decode(errors='replace'))
                    if mode=='shared-only':
                        self.assertEqual(got.returncode,0);self.assertEqual(len(rows),3)
                    elif mode in ('callback-unguarded','callback-frame'):
                        self.assertEqual(got.returncode,126);self.assertEqual(len(rows),4)
                        self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=13 stage=4 reason=[0-5] call_reason=[0-5] visits=[0-9]+$')
                    elif mode.startswith('callback'):
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        category={'callback':2,'callback-unknown':1,'callback-unmapped':3,'callback-corrupt':4,'callback-unaligned':2}[mode]
                        expected=f'V995_CALLBACK_FRONTIER target_class={category} aligned={int(mode!="callback-unaligned")} visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'.encode()
                        self.assertEqual(rows[3:],[expected])
                    else:
                        self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                        match=int(mode=='direct')
                        expected=f'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match={match} callback_known=1 admitted={match} visits=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'.encode()
                        self.assertEqual(rows[3:],[time,expected])
                    self.assertEqual(got.stderr,b'')
if __name__=='__main__':unittest.main()
