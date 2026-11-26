import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from write_sram_profile_v536 import sram_fixture,wireless_zero_fixture
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
            shutil.copyfile(HOST/'synthetic_callback_time_expectations_v1014.h',root/'v813_private_callback_time.h')
            shutil.copyfile(HOST/'synthetic_callback_frontier_v1111.h',root/'v831_private_callback_frontier.h')
            shutil.copyfile(HOST/'synthetic_wireless_wrapper_v1118.h',root/'v847_private_wireless_wrapper.h')
            shutil.copyfile(HOST/'synthetic_postalarm_suffix_v1123.h',root/'v1123_private_postalarm_suffix.h')
            shutil.copyfile(HOST/'synthetic_postalarm_return_v1132.h',root/'v1132_private_postalarm_return.h')
            shutil.copyfile(HOST/'synthetic_postalarm_handler_v1139.h',root/'v1139_private_postalarm_handler.h')
            shutil.copyfile(HOST/'synthetic_postalarm_handler_return_v1145.h',root/'v1145_private_postalarm_handler_return.h')
            shutil.copyfile(HOST/'synthetic_held_epilogue_v1151.h',root/'v1151_private_held_epilogue.h')
            shutil.copyfile(HOST/'synthetic_held_dispatch_v1158.h',root/'v1158_private_held_dispatch.h')
            shutil.copyfile(HOST/'synthetic_third_ack_v1167.h',root/'v1167_private_third_ack.h')
            shutil.copyfile(HOST/'synthetic_ack_helper_v1175.h',root/'v1175_private_ack_helper.h')
            (root/'v958_private_second_ack.h').write_text(
                '#define UNDERCOVER_V1025_PRIVATE_TRANSFER 1\n#define UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE 1\n#define UNDERCOVER_V1049_PRIVATE_ABI_PROVEN 1\n#define UNDERCOVER_V1048_PRIVATE_THIRD_ALARM 1\n#define UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1\n#define UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1\n#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1\n#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1\n#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1\n#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1\n#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1\n#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1\n#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n#define UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH 1\n#define UNDERCOVER_V1167_PRIVATE_THIRD_ACK 1\n#define UNDERCOVER_V1175_PRIVATE_ACK_HELPER 1\n#define UNDERCOVER_V1180_PRIVATE_ACK_CALLBACK 1\n#define UNDERCOVER_V1184_PRIVATE_ACK_PREFIX 1\n#define UNDERCOVER_V1189_PRIVATE_ACK_TIME 1\n#define UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER 1\n#define UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS 1\n#define UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX 1\n#define UNDERCOVER_V1205_PRIVATE_ACK_RETURN 1\n#define UNDERCOVER_V1210_PRIVATE_ACK_HANDLER 1\n#define UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN 1\n#define UNDERCOVER_V1217_PRIVATE_ACK_FINAL 1\n#define UNDERCOVER_V1220_PRIVATE_ACK_RESUME 1\n#define UNDERCOVER_V1227_PRIVATE_ACK_LEAF 1\n#define UNDERCOVER_V1230_PRIVATE_ACK_IPC 1\n#define UNDERCOVER_V1235_PRIVATE_ACK_IPC_COMPLETE 1\n#define UNDERCOVER_V1240_PRIVATE_ACK_STM 1\n#define UNDERCOVER_V1246_PRIVATE_ACK_OPEN 1\n'
                +(HOST/'synthetic_success_frontier_expectations_v997.h').read_text().replace('context=0x80009000u','context=0x806f5318u')
                +'''
namespace undercover::wii::v958 {
inline constexpr std::array<AckCallSpan,5> third_spans{{{0x80004000u,0x80004020u},{0x80004700u,0x80004750u},{0x80004800u,0x80004804u},{0x80004900u,0x80004904u},{0x80004a00u,0x80004a04u}}};
inline constexpr std::array<AckCallEdge,4> third_edges{{{0x80004014u,0x80004700u},{0x80004700u,0x80004800u},{0x80004704u,0x80004900u},{0x80004708u,0x80004a00u}}};
}
#include "wii_handler_suffix_guard_v868.h"
#include <cstdlib>
namespace undercover::wii::v958 {
// Synthetic test metadata only: model the original owner route,
 // where status MMIO is not consumed before the callback return.
inline const std::array<HandlerSuffixLabel,4> third_alarm_suffix=[]{
    const char* v=std::getenv("UNDERCOVER_V1139_SYNTHETIC_NO_PRIOR_STATUS");
    const bool empty=v&&v[0]=='1'&&v[1]==0;
    return std::array<HandlerSuffixLabel,4>{{{0x80004018u,0x60000000u,0,0},{0x8000401cu,empty?0x60000000u:0x80830038u,0,0},{0x80004020u,empty?0x60000000u:0x90830038u,0,0},{0x80004024u,0x48000addu,5,1}}};
}();
inline constexpr std::array<HandlerSuffixLabel,2> third_postalarm_suffix{{{0x80004028u,0x60000000u,0,0},{0x8000402cu,0x4e800421u,6,2}}};
inline constexpr uint32_t third_postalarm_save_root=0x8000d100u;
inline constexpr std::array<uint32_t,6> third_postalarm_prefix{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,0x480000f1u,0x60000000u};
inline constexpr std::array<uint32_t,3> third_postalarm_save{0x93cbfff8u,0x93ebfffcu,0x4e800020u};
inline constexpr auto third_postalarm_words=third_postalarm_prefix;
inline constexpr std::array<uint32_t,2> third_postalarm_sites{0x8000402cu,0x80004030u};
}
''')
            # Independent synthetic alarm, never copied from the owner image.
            (root/'v786_private_alarm.h').write_text("""
#pragma once
#include "wii_alarm_cancel_return_v782.h"
namespace undercover::wii::v786 {
inline constexpr AlarmCancelExpectation expected{
0x80004024u,0x48000addu,0x80004b00u,0x80004b14u,0,0,0x8000e000u,0x8000e004u,
{{{0x80004b00u,0x80004c00u,0x80004c08u,0x48000101u},{0x80004b08u,0x80004d00u,0x80004d08u,0x480001f9u}}},{}
};
}
""")
            # These two private MSR sites belong only to the preceding
            # time route; the synthetic third route reuses neither. Use
            # real shared-leaf spans, just as the owner installer does.
            h=root/'v958_private_second_ack.h'
            h.write_text(h.read_text().replace('std::array<AckCallSpan,5> third_spans{{','std::array<AckCallSpan,7> third_spans{{').replace('{0x80004a00u,0x80004a04u}}};','{0x80004a00u,0x80004a04u},{0x80004400u,0x80004408u},{0x80004600u,0x80004608u}}};'))
            (root/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text()))))))
            h=root/'wii_postack_transfer_device_v771.h';s=h.read_text();seam='\n};\n}\n'
            self.assertEqual(s.count(seam),1);h.write_text(s.replace(seam,'\n};\ninline thread_local PostAckTransferDevice si_transfer_device{};\n}\n'))
            (root/'v1199_test_sram.h').write_text('#pragma once\n#include <array>\n#include <cstdint>\nnamespace v1199_test {\n'+''.join('inline constexpr std::array<uint8_t,64> '+name+'{'+','.join(map(str,blob))+'};\n' for name,blob in (('pattern',sram_fixture()),('zero',wireless_zero_fixture())))+'}\n')
            (root/'v1227_private_ack_leaf.h').write_text("""
#pragma once
#include "wii_irq_leaf_finish_v927.h"
#include "wii_ipc_client_witness_v623.h"
#include <cstdlib>
namespace undercover::wii::v1227 {
inline bool ipc_fixture(){const char* v=std::getenv("UNDERCOVER_V1233_IPC_FIXTURE");return v&&v[0]=='1'&&v[1]==0;}
inline constexpr uint32_t ipc_bl=0x48000001u|((IpcClientWitness::Root-IpcClientWitness::Call)&0x03fffffcu);
inline const IrqLeafFinishExpectation expected{0x80005000u,(21u<<26)|(3u<<16)|(17u<<11)|(31u<<6)|(31u<<1),
    ipc_fixture()?IpcClientWitness::Call:0x80006000u,ipc_fixture()?ipc_bl:0x60000000u};
}
""")
            (root/'v1230_private_ack_ipc.h').write_text("""
#pragma once
#include "wii_post_ack_ipc_join_v1229.h"
namespace undercover::wii::v624 {
inline const IpcClientExpectations expected_client=[]{
    IpcClientExpectations e{};
    if(v1227::ipc_fixture()){
        e.edges[0]={IpcClientWitness::Root,IpcClientWitness::Return,v1227::ipc_bl,0x60000000u};
        // Remaining edges are independently chosen synthetic locations.
        for(unsigned i=1;i<17;++i)e.edges[i]={0x80540000u+16u*i,0x80550004u+16u*i,0x48000001u,0x60000000u};
        e.handler=0x80519094u;e.handler_word=0x1234u;e.return_word=0x60000000u;
    }
    return e;
}();
}
namespace undercover::wii::v1230 {
inline const IpcEntryJoinExpectation expected=v1227::ipc_fixture()?
    IpcEntryJoinExpectation{IpcClientWitness::Call,IpcClientWitness::Root,v1227::ipc_bl,0x60000000u}:
    IpcEntryJoinExpectation{0x80006000u,0x80007000u,0x48001001u,0x60000000u};
}
""")
            (root/'v1240_private_ack_stm.h').write_text("""
#pragma once
#include "wii_post_ack_stm_join_v1239.h"
namespace undercover::wii::v629 {
inline constexpr StmPrefixExpectations expected_stm=[]{
    using S=StmPrefixWitness;StmPrefixExpectations e{};
    e.bridge.fill(0x60000000u);e.bridge.back()=0x48000001u|((S::Stm-(S::Begin+24u))&0x03fffffcu);
    e.stm={S::Stm,S::Begin+28u,e.bridge.back(),0x60000000u};
    e.open={S::Open,0x8052b090u,0x48000001u|((S::Open-0x8052b08cu)&0x03fffffcu),0x60000000u};
    e.paths[0]={0x80601000u,1};e.paths[1]={0x80602000u,2};e.path_count=2;e.irq_handler=0x80519094u;
    return e;
}();
}
""")
            (root/'v574_private_sc_expectations.h').write_text('#pragma once\n#include <array>\nnamespace undercover::wii::v574 { inline constexpr std::array<uint8_t,28> expected_vector{}; }\n')
            (root/'v1246_private_ack_open.h').write_text("""
#pragma once
#include "wii_post_ack_open_join_v1242.h"
namespace undercover::wii::v639 {
using O=OpenRequestWitness;using R=OpenScRoute;
inline constexpr OpenRequestExpectations expected_open{v629::expected_stm.open,
 {O::Profile,0x8051998cu,3,4},{O::Disable,0x8051ab64u,5,6},{O::Restore,0x8051ad14u,7,8},
 {O::Flush,R::Caller,9,10},{O::Submit,0x80519a3cu,11,12},13,0x44000002u,14};
}
""")
            exe=root/'probe'
            build=subprocess.run([cc,'-DUNDERCOVER_V1199_TEST_SRAM=1','-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'probe.cpp'),'-o',str(exe)],capture_output=True,timeout=90)
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
            env['UNDERCOVER_V1048_THIRD_ALARM']='1'
            for fault in ('','-label','-skip','-frame','-missing','-value','-queue'):
                with self.subTest(alarm=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'')
                    self.assertIn(b'V1028_THIRD_RETURN original_transfer=1 token=3 pending=0 visits=21 entries=4 returns=4 reads=1 writes=3 saved_fields=38 handler_instruction_executed=0 boot_verified=0',rows)
                    expected_handoff=(b'V1087_ALARM_HANDOFF started=0 first=0 stage=0 reason=1' if fault=='-label' else
                                      b'V1087_ALARM_HANDOFF started=1 first=1 stage=1 reason=0')
                    self.assertIn(expected_handoff,rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane=0 timer=0 calls=3 visits=9 suffix_visits=4 status_reads=1 status_writes=1 token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V958_ACK_INVALID kind=19 stage=5 reason=0 call_reason=0 visits=[0-9]+$')
                        self.assertFalse(any(x.startswith(b'V1048_THIRD_ALARM_RETURN') for x in rows))
            env['UNDERCOVER_V1095_AFTER_ALARM']='1'
            for fault in ('','-word','-frame','-target','-poll','-stack'):
                with self.subTest(after_alarm=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'')
                    self.assertTrue(any(x.startswith(b'V1048_THIRD_ALARM_RETURN ') for x in rows),rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=9 writes=4 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1095_AFTER_ALARM_FAULT route=[1-6] prefix=[0-4] stage=[0-2]$')
            env['UNDERCOVER_V1103_POSTALARM_TIME']='1'
            for fault in ('','-offset','-frame','-tick','-device','-word','-entry','-poll','-result','-changed-offset'):
                with self.subTest(postalarm_time=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=9 writes=4 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1103_POSTALARM_TIME_RETURN original_return=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1103_POSTALARM_TIME_FAULT route=[7-9] witness=[0-7] stage=[34]$')
            env['UNDERCOVER_V1111_POSTALARM_FRONTIER']='1'
            for fault in ('','-identity','-frame','-tick','-device','-entry','-poll','-channel','-store'):
                with self.subTest(postalarm_frontier=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1103_POSTALARM_TIME_RETURN original_return=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1111_POSTALARM_FRONTIER ordinal=3 visits=4 writes=1 zero_id=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1111_POSTALARM_FRONTIER_FAULT route=(0|10|11) witness=[0-7] stage=[56]$')
            env['UNDERCOVER_V1118_POSTALARM_WIRELESS']='1'
            for fault in ('','-changed','-pattern','-zero-profile','-identity','-entry','-frame','-tick','-device','-poll','-store','-abi'):
                with self.subTest(postalarm_wireless=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1111_POSTALARM_FRONTIER ordinal=3 visits=4 writes=1 zero_id=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0',rows)
                    if fault in ('','-zero-profile'):
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1118_POSTALARM_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=11 stores=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1118_POSTALARM_WIRELESS_FAULT route=(0|12|13|14) witness=[0-7] stage=[78]$')
                        if fault=='-pattern':self.assertEqual(rows[-1],b'V1118_POSTALARM_WIRELESS_FAULT route=12 witness=0 stage=7')
            env['UNDERCOVER_V1123_POSTALARM_SUFFIX']='1'
            for fault in ('','-identity','-frame','-tick','-device','-entry','-early-poll','-store','-missing-poll','-double-poll'):
                with self.subTest(postalarm_suffix=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1118_POSTALARM_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=11 stores=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1123_POSTALARM_SUFFIX ordinal=13 target_class=0 visits=4 writes=1 polls=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1123_POSTALARM_SUFFIX_FAULT route=(0|15|16|17) witness=[0-7] stage=(9|10)$')
            env['UNDERCOVER_V1132_POSTALARM_RETURN']='1'
            for fault in ('','-identity','-entry','-frame','-tick','-device','-slot','-poll','-double-poll','-dispatch','-abi'):
                with self.subTest(postalarm_return=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1123_POSTALARM_SUFFIX ordinal=13 target_class=0 visits=4 writes=1 polls=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1132_POSTALARM_RETURN original_restore=1 original_return=1 visits=12 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1132_POSTALARM_RETURN_FAULT route=(0|18|19|20|21) witness=[0-6] stage=(11|12)$')
            env['UNDERCOVER_V1139_POSTALARM_HANDLER']='1'
            for fault in ('','-not-taken','-prior-status','-identity','-frame','-tick','-poll','-entry','-address','-missing-read','-load-value','-missing-write','-branch'):
                with self.subTest(postalarm_handler=fault):
                    e=env.copy()
                    if fault!='-prior-status':e['UNDERCOVER_V1139_SYNTHETIC_NO_PRIOR_STATUS']='1'
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler'+fault],env=e,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1132_POSTALARM_RETURN original_restore=1 original_return=1 visits=12 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0',rows)
                    if fault in ('','-not-taken'):
                        self.assertEqual(got.returncode,0,got.stdout)
                        taken=int(fault=='')
                        self.assertEqual(rows[-1],f'V1139_POSTALARM_HANDLER ordinal=12 branch_taken={taken} visits={16-taken} stores=0 status_reads=1 status_writes=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0'.encode())
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1139_POSTALARM_HANDLER_FAULT route=(0|22|23) witness=[0-6] stage=(13|14)$')
            env['UNDERCOVER_V1145_POSTALARM_HANDLER_RETURN']='1'
            env['UNDERCOVER_V1139_SYNTHETIC_NO_PRIOR_STATUS']='1'
            for fault in ('','-identity','-entry','-frame','-tick','-device','-slot','-poll','-double-poll','-dispatch','-abi'):
                with self.subTest(postalarm_handler_return=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1139_POSTALARM_HANDLER ordinal=12 branch_taken=1 visits=15 stores=0 status_reads=1 status_writes=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1145_POSTALARM_HANDLER_RETURN original_restore=1 original_return=1 visits=21 restored_gprs=15 token=3 held=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1145_POSTALARM_HANDLER_RETURN_FAULT route=(0|25|26|27|28) witness=[0-5] native=[0-6] stage=(15|16)$')
            env['UNDERCOVER_V1151_HELD_EPILOGUE']='1'
            for fault in ('','-entry','-frame','-tick','-gqr','-image','-outer-poll','-saved'):
                with self.subTest(held_epilogue=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1145_POSTALARM_HANDLER_RETURN original_restore=1 original_return=1 visits=21 restored_gprs=15 token=3 held=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertIn(b'V1151_HELD_PENDING_RFI native_rfi=1 pending_exception=1 visits=11 token=3 held=1 resumed_instruction_executed=0 boot_verified=0',rows)
                        self.assertEqual(rows[-1],b'V1151_HELD_VECTOR_JOIN original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=2 trampoline_visits=2 token=3 held=1 dispatcher_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=[1-4] reason=[1-5] epilogue=[0-9] reentry=[0-9]+$')
            env['UNDERCOVER_V1158_HELD_DISPATCH']='1'
            for fault in ('','-owner','-busy','-tick','-frame','-trace','-guard','-value','-missing','-duplicate','-entry','-handler'):
                with self.subTest(held_dispatch=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1151_HELD_VECTOR_JOIN original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=2 trampoline_visits=2 token=3 held=1 dispatcher_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1158_HELD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits=10 entries=5 pi_reads=2 polls=4 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=[56] reason=[0-8] epilogue=[0-9] reentry=[0-9]+$')
            env['UNDERCOVER_V1167_THIRD_ACK']='1'
            for fault in ('','-mirror','-unarmed','-frame','-tick','-guard','-entry','-width','-offset','-value','-w1c','-write','-post-frame'):
                with self.subTest(third_ack=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1158_HELD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits=10 entries=5 pi_reads=2 polls=4 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0',rows)
                    if fault in ('','-mirror'):
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1167_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response=1 visits=8 entries=2 returns=1 reads=1 writes=1 saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=8 reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1175_ACK_HELPER']='1'
            for fault in ('','-tick','-frame','-bus','-word','-guard','-entry','-msr','-abi'):
                with self.subTest(ack_helper=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1167_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response=1 visits=8 entries=2 returns=1 reads=1 writes=1 saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1175_ACK_HELPER_RETURN original_helper=1 visits=15 entries=6 returns=6 msr=2 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=10 reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1180_ACK_CALLBACK']='1'
            for fault in ('','-target','-unaligned','-channel','-frame','-word','-siteword','-tick','-bus','-guard'):
                with self.subTest(ack_callback=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1175_ACK_HELPER_RETURN original_helper=1 visits=15 entries=6 returns=6 msr=2 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1180_ACK_CALLBACK_FRONTIER target_class=2 aligned=1 visits=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=12 reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1184_ACK_PREFIX']='1'
            for fault in ('','-identity','-frame','-bus','-tick','-poll','-double-poll','-guard','-stack','-entry','-slot'):
                with self.subTest(ack_prefix=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1180_ACK_CALLBACK_FRONTIER target_class=2 aligned=1 visits=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1184_ACK_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=4 visits=9 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(13|14) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1189_ACK_TIME']='1'
            for fault in ('','-identity','-frame','-tick','-device','-bus','-guard','-entry','-poll','-result','-offset'):
                with self.subTest(ack_time=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1184_ACK_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=4 visits=9 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1189_ACK_TIME_RETURN original_time=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(15|16) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1193_ACK_FRONTIER']='1'
            for fault in ('','-identity','-frame','-tick','-device','-bus','-entry','-poll','-guard','-channel','-store'):
                with self.subTest(ack_frontier=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1189_ACK_TIME_RETURN original_time=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1193_ACK_WIRELESS_FRONTIER ordinal=3 visits=4 writes=1 zero_id=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(17|18) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1197_ACK_WIRELESS']='1'
            for fault in ('','-changed','-identity','-entry','-frame','-tick','-device','-bus','-poll','-guard','-store','-abi'):
                with self.subTest(ack_wireless=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1193_ACK_WIRELESS_FRONTIER ordinal=3 visits=4 writes=1 zero_id=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1197_ACK_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=11 stores=1 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(19|20) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1201_ACK_SUFFIX']='1'
            for fault in ('','-identity','-frame','-tick','-device','-bus','-entry','-early-poll','-guard','-store','-missing-poll','-double-poll'):
                with self.subTest(ack_suffix=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1197_ACK_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=11 stores=1 token=3 saved_fields=38 pi_cleared=1 continuation_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1201_ACK_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=4 writes=1 polls=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(21|22) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1205_ACK_RETURN']='1'
            for fault in ('','-identity','-entry','-frame','-tick','-device','-bus','-slot','-guard','-poll','-double-poll','-dispatch','-abi'):
                with self.subTest(ack_return=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1201_ACK_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=4 writes=1 polls=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1205_ACK_CALLBACK_RETURN original_restore=1 original_return=1 visits=8 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(23|24) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1210_ACK_HANDLER']='1'
            for fault in ('','-identity','-frame','-tick','-poll','-entry','-bus','-address','-guard','-missing-read','-load-value','-missing-write','-write-value','-branch'):
                with self.subTest(ack_handler=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1205_ACK_CALLBACK_RETURN original_restore=1 original_return=1 visits=8 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1210_ACK_HANDLER ordinal=12 branch_taken=1 visits=15 stores=0 status_reads=1 status_writes=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(25|26) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1214_ACK_HANDLER_RETURN']='1'
            for fault in ('','-identity','-entry','-frame','-tick','-device','-bus','-slot','-guard','-poll','-double-poll','-dispatch','-abi'):
                with self.subTest(ack_handler_return=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1210_ACK_HANDLER ordinal=12 branch_taken=1 visits=15 stores=0 status_reads=1 status_writes=1 token=3 saved_fields=38 pi_cleared=1 call_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1214_ACK_HANDLER_RETURN original_restore=1 original_return=1 visits=21 restored_gprs=15 token=3 saved_fields=38 pi_cleared=1 dispatcher_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(27|28) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1217_ACK_FINAL']='1'
            for fault in ('','-counter','-entry','-frame','-tick','-bus','-device','-early-poll','-guard','-restore','-gqr','-rfi-tick','-second-gqr'):
                with self.subTest(ack_final=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1214_ACK_HANDLER_RETURN original_restore=1 original_return=1 visits=21 restored_gprs=15 token=3 saved_fields=38 pi_cleared=1 dispatcher_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1217_ACK_FINAL_RFI native_rfi=1 restored_context=1 visits=11 polls=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(29|30) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1220_ACK_RESUME']='1'
            for fault in ('','-missing-dispatch-tick','-extra-dispatch-tick','-pc','-srr0','-mask','-missing-dispatch','-double-dispatch','-integer','-gqr','-word','-extra-label-tick','-missing-label-tick','-guard'):
                with self.subTest(ack_resume=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final-resume'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1217_ACK_FINAL_RFI native_rfi=1 restored_context=1 visits=11 polls=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1220_ACK_FINAL_RESUME original_resume=1 restored_context=1 dispatch_ticks=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(31|32) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            env['UNDERCOVER_V1227_ACK_LEAF']='1'
            for fault in ('','-leaf-word','-caller-word','-extract','-tick','-mask','-bus','-guard','-abi','-poll','-double-poll','-dispatch','-target','-gqr'):
                with self.subTest(ack_leaf=fault):
                    got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final-resume-leaf'+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1220_ACK_FINAL_RESUME original_resume=1 restored_context=1 dispatch_ticks=2 token=3 pi_cleared=1 resumed_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-1],b'V1227_ACK_LEAF_RETURN original_extract=1 original_blr=1 osinit_resume=1 previous_ee=0 integer_state=1 gqr=1 token=3 pi_cleared=1 caller_instruction_executed=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertRegex(rows[-1],rb'^V1151_HELD_EPILOGUE_FAULT stage=(33|34) reason=[0-9]+ epilogue=[0-9]+ reentry=[0-9]+$')
            # Existing live fixture has no real IPC heap or IOS transport.
            env['UNDERCOVER_V1230_ACK_IPC']='1'
            got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final-resume-leaf'],env=env,capture_output=True,timeout=10)
            self.assertEqual(got.returncode,126,got.stdout+got.stderr)
            self.assertEqual(got.stderr,b'')
            self.assertRegex(got.stdout.splitlines()[-1],rb'^V1230_ACK_IPC_INVALID stage=0 reason=1 cold=1 refusal=[1-9][0-9]{0,4} join=0$')
            # Positive end-to-end live observer path, with a native IOS
            # transport, dense guest RAM and synthetic direct BL effects.
            env['UNDERCOVER_V1233_IPC_FIXTURE']='1'
            got=subprocess.run([str(exe),'error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final-resume-leaf-ipc-valid'],env=env,capture_output=True,timeout=10)
            self.assertEqual(got.returncode,0,got.stdout+got.stderr)
            self.assertEqual(got.stderr,b'')
            self.assertEqual(got.stdout.splitlines()[-1],b'V1230_ACK_IPC_ENTRY original_bl=1 original_target=1 cold_prerequisites=1 same_tick=1 token=3 pi_cleared=1 ipc_instruction_executed=0 boot_verified=0')
            env['UNDERCOVER_V1235_ACK_IPC_COMPLETE']='1'
            mode='error-abi-live-alarm-callback-time-frontier-wireless-suffix-return-handler-return-epilogue-dispatch-ack-helper-callback-prefix-time-frontier-wireless-suffix-return-handler-return-final-resume-leaf-ipc-valid'
            for fault in ('','-ipc-pending','-ipc-si','-ipc-heap','-ipc-mask','-ipc-missing-control'):
                with self.subTest(ipc_complete=fault):
                    got=subprocess.run([str(exe),mode+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1230_ACK_IPC_ENTRY original_bl=1 original_target=1 cold_prerequisites=1 same_tick=1 token=3 pi_cleared=1 ipc_instruction_executed=0 boot_verified=0',rows)
                    if not fault:
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-18:-1],[f'V1235_ACK_IPC_STAGE n={n}'.encode() for n in range(3,20)])
                        self.assertEqual(rows[-1],b'V1235_ACK_IPC_RETURN calls=17 heap=1 handler=1 mailbox=1 returned=1 token=3 si_quiescent=1 queued=0 serviced=0 actual_ios=0 boot_verified=0')
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertTrue(rows[-1].startswith(b'V1235_ACK_IPC_INVALID '),rows[-1])
            env['UNDERCOVER_V1240_ACK_STM']='1'
            for fault in ('-stm-immediate','-stm-eventhook','-stm-path','-stm-si','-stm-transport','-stm-tick','-stm-bridge'):
                with self.subTest(stm=fault):
                    got=subprocess.run([str(exe),mode+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    self.assertIn(b'V1235_ACK_IPC_RETURN calls=17 heap=1 handler=1 mailbox=1 returned=1 token=3 si_quiescent=1 queued=0 serviced=0 actual_ios=0 boot_verified=0',rows)
                    if fault in ('-stm-immediate','-stm-eventhook'):
                        self.assertEqual(got.returncode,0,got.stdout)
                        self.assertEqual(rows[-4:-1],[f'V1240_ACK_STM_STAGE n={n}'.encode() for n in range(1,4)])
                        kind=1 if fault=='-stm-immediate' else 2
                        self.assertEqual(rows[-1],f'V1240_ACK_STM_OPEN original_bridge=1 original_stm=1 original_open_entry=1 path={kind} mode=0 token=3 si_quiescent=1 serviced=0 open_instruction_executed=0 boot_verified=0'.encode())
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertTrue(rows[-1].startswith(b'V1240_ACK_STM_INVALID '),rows[-1])
            env['UNDERCOVER_V1247_ACK_OPEN']='1'
            for fault in ('-open-immediate','-open-eventhook','-open-cache','-open-vector','-open-syscall','-open-request','-open-si','-open-transport'):
                with self.subTest(open=fault):
                    got=subprocess.run([str(exe),mode+fault],env=env,capture_output=True,timeout=10)
                    rows=got.stdout.splitlines()
                    self.assertEqual(got.stderr,b'',got.stdout)
                    if fault in ('-open-immediate','-open-eventhook'):
                        self.assertEqual(got.returncode,0,got.stdout)
                        kind=1 if fault=='-open-immediate' else 2
                        from audit_v1247_ack_open import EVENTS,RESULTS
                        self.assertEqual(tuple(rows[-12:]),EVENTS+(RESULTS[kind-1],))
                    else:
                        self.assertEqual(got.returncode,126,got.stdout)
                        self.assertTrue(rows[-1].startswith(b'V1247_ACK_OPEN_INVALID '),rows[-1])
if __name__=='__main__':unittest.main()
