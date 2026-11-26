import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from test_v997_composed_success_frontier import HOST,sampling,discovery,first,transfer,second
class LiveThird(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','GCC sanitizer regression')
    def test_live_feature_macro(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for h in HOST.glob('*.h'):
                if h.is_file() and not h.is_symlink():shutil.copyfile(h,root/h.name)
            shutil.copyfile(HOST/'test_success_frontier_mmio_v997.cpp',root/'probe.cpp')
            (root/'v958_private_second_ack.h').write_text(
                '#define UNDERCOVER_V1025_PRIVATE_TRANSFER 1\n#define UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE 1\n'
                +(HOST/'synthetic_success_frontier_expectations_v997.h').read_text()
                +'''
namespace undercover::wii::v958 {
inline constexpr std::array<AckCallSpan,5> third_spans{{{0x80004000u,0x80004020u},{0x80004700u,0x80004750u},{0x80004800u,0x80004804u},{0x80004900u,0x80004904u},{0x80004a00u,0x80004a04u}}};
inline constexpr std::array<AckCallEdge,4> third_edges{{{0x80004014u,0x80004700u},{0x80004700u,0x80004800u},{0x80004704u,0x80004900u},{0x80004708u,0x80004a00u}}};
}
''')
            # These two private MSR sites belong only to the preceding
            # time route; the synthetic third route reuses neither. Use
            # real shared-leaf spans, just as the owner installer does.
            h=root/'v958_private_second_ack.h'
            h.write_text(h.read_text().replace('std::array<AckCallSpan,5> third_spans{{','std::array<AckCallSpan,7> third_spans{{').replace('{0x80004a00u,0x80004a04u}}};','{0x80004a00u,0x80004a04u},{0x80004400u,0x80004408u},{0x80004600u,0x80004608u}}};'))
            (root/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text()))))))
            h=root/'wii_postack_transfer_device_v771.h';s=h.read_text();seam='\n};\n}\n'
            self.assertEqual(s.count(seam),1);h.write_text(s.replace(seam,'\n};\ninline thread_local PostAckTransferDevice si_transfer_device{};\n}\n'))
            exe=root/'probe'
            build=subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'probe.cpp'),'-o',str(exe)],capture_output=True,timeout=90)
            self.assertEqual(build.returncode,0,build.stderr.decode(errors='replace'))
            env={k:v for k,v in os.environ.items() if not k.startswith('UNDERCOVER_V')}
            for key in ('V958_SECOND_ACK','V967_POST_ACK','V989_SHARED_COMPLETION','V975_SECOND_TIME','V981_SECOND_FRONTIER','V995_SUCCESS_FRONTIER','V1015_ERROR_COMPLETION','V1021_ERROR_FRONTIER','V1034_QUEUE_DETAIL','V1040_SIX_ARGS','V1028_THIRD_TRANSFER'):
                env['UNDERCOVER_'+key]='1'
            for mode in ('exact','tail','core','changed','tamper','reg','tick'):
                with self.subTest(mode=mode):
                    got=subprocess.run([str(exe),'error-abi-live-'+mode],env=env,capture_output=True,timeout=10)
                    self.assertEqual(got.returncode,0,(got.stdout+got.stderr).decode(errors='replace'))
                    self.assertEqual(got.stderr,b'')
                    rows=got.stdout.splitlines()
                    if mode in ('exact','tail'):
                        self.assertEqual(rows[-1],b'V1028_THIRD_RETURN original_transfer=1 token=3 pending=0 visits=21 entries=4 returns=4 reads=1 writes=3 saved_fields=38 handler_instruction_executed=0 boot_verified=0')
                    elif mode in ('core','changed'):
                        self.assertTrue(rows[-1].startswith(b'V1040_TRANSFER_ABI admission=0 '),rows[-1])
                    else:self.assertEqual(rows[-1],b'V1043_LIVE_HANDOFF refused=1 unchanged_device=1 original_execution=0')
if __name__=='__main__':unittest.main()
