import unittest
from windows_startup_scope_v434 import contract,audit,launch_flags,requires_exi_profile,requires_si_profile,SCOPES,PREFIXES,HARDWARE_PATCHES,CACHE_PATCHES,OS_HW_PATCHES,OS_IPC_PATCHES,OS_VECTOR_PATCHES,OS_SRAM_PATCHES,OS_SC_PATCHES,MAX_LOG,requires_sram_profile,requires_sc_overlay,requires_external_overlay,EXTERNAL_SCOPES,FAILURE_PREFIXES
from audit_v419_full_start import STAGES as START,RESULT as START_RESULT
from audit_v425_full_hardware import STAGES as HW,RESULT as HW_RESULT
from audit_v428_full_cache import STAGES as CACHE,RESULT as CACHE_RESULT
from audit_v430_full_data import HELPERS,RESULT as DATA_RESULT
from audit_v433_full_os_entry import DB,RESULT as OS_RESULT
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT
from audit_v439_full_os_hardware import STAGES as OS_HW,RESULT as OS_HW_RESULT,COPY
from audit_v444_full_os_arena import STAGES as ARENA,RESULT as ARENA_RESULT
from audit_v446_full_os_ipc import STAGES as IPC,RESULT as IPC_RESULT
from audit_v457_exception_vector import STAGES as VECTOR,RESULT as VECTOR_RESULT
from audit_v466_exception_pack import STAGES as PACK,RESULT as PACK_RESULT
from audit_v470_alarm_startup import STAGES as ALARM,RESULT as ALARM_RESULT
from audit_v473_module_irq import STAGES as IRQ,RESULT as IRQ_RESULT
from audit_v476_irq_mmio import STAGES as MMIO,RESULT as MMIO_RESULT
from audit_v483_irq_return import STAGES as IRQ_RETURN,RESULT as IRQ_RETURN_RESULT
from audit_v486_context_startup import STAGES as CONTEXT,RESULT as CONTEXT_RESULT
from audit_v488_os_cache_reuse import STAGES as REUSE,RESULT as REUSE_RESULT
from audit_v491_exi_poll import STAGES as POLL,RESULT as POLL_RESULT
from audit_v500_exi_handlers import STAGES as HANDLERS,RESULT as HANDLERS_RESULT
from audit_v504_exi_id import STAGES as ID,RESULT as ID_RESULT
from audit_v510_exi_absent import STAGES as ABSENT,RESULT as ABSENT_RESULT
from audit_v520_si_entry import STAGES as SI_ENTRY,RESULT as SI_ENTRY_RESULT
from audit_v524_si_sampling import STAGES as SI_SAMPLE,RESULT as SI_SAMPLE_RESULT
from audit_v529_si_discovery import STAGES as SI_RETURN,RESULT as SI_RETURN_RESULT
from audit_v534_sram_read import STAGES as SRAM,RESULT as SRAM_RESULT
from audit_v549_thread_init import STAGES as THREAD,RESULT as THREAD_RESULT
from audit_v556_audio_reset import STAGES as AUDIO,RESULT as AUDIO_RESULT
from audit_v559_dsp_stage import STAGES as DSP_STAGE,RESULT as DSP_STAGE_RESULT
from audit_v574_dsp_sc import STAGES as DSP_SC,RESULT as DSP_SC_RESULT
from audit_v581_dsp_return import STAGES as DSP_RETURN,RESULT as DSP_RETURN_RESULT
from audit_v591_memory_init import STAGES as MI,RESULT as MI_RESULT
from audit_v603_boot_report import EVENTS as REPORT
from audit_v609_arena_clear import EVENTS as ARENA_CLEAR
from audit_v663_external_entry import EVENTS as EXT,RESULT as EXT_RESULT
from audit_v667_si_dispatch import EVENTS as SI_DISP,RESULT as SI_DISP_RESULT
from audit_v672_si_ack_route import EVENTS as SI_ACK,RESULT as SI_ACK_RESULT
from audit_v699_si_postack import STAGE as POSTACK, NESTED, RETURN as POSTACK_RETURN, END as POSTACK_END
from audit_v709_os_leaves import LEAVES
from audit_v742_handler_time import STAGES as TIME_STAGES


def log(lines):return b'\n'.join(lines)+b'\n'
DATA=CACHE+[b'V430_DATA_BEGIN before_nonzero=0']+HELPERS+[DATA_RESULT]
OS=DATA+[b'V433_OS_BEGIN arena_hi_nonzero=1 boot_info_nonzero=0',DB,OS_RESULT]
OS_TIME=OS+TIME+[TIME_RESULT]
OS_HARDWARE=OS_TIME+[b'V439_HW_BEGIN copy=0']+OS_HW+[OS_HW_RESULT]
OS_ARENA=OS_HARDWARE+[b'V444_ARENA_BEGIN boot_path=1 direct_low=0']+ARENA+[ARENA_RESULT]
OS_IPC=OS_ARENA+[b'V446_IPC_BEGIN clamp=0']+IPC+[IPC_RESULT]
OS_VECTOR=OS_IPC+[b'V457_VECTOR_BEGIN debug_needed=1',b'V457_VECTOR_PRELUDE n=1']+VECTOR+[VECTOR_RESULT]
OS_PACK=OS_VECTOR+PACK+[PACK_RESULT]
OS_ALARM=OS_PACK+ALARM+[ALARM_RESULT]
OS_IRQ=OS_ALARM+IRQ+[IRQ_RESULT]
OS_MMIO=OS_IRQ+MMIO+[MMIO_RESULT]
OS_IRQ_RETURN=OS_MMIO+IRQ_RETURN+[IRQ_RETURN_RESULT]
OS_CONTEXT=OS_IRQ_RETURN+CONTEXT+[CONTEXT_RESULT]
OS_REUSE=OS_CONTEXT+REUSE+[REUSE_RESULT]
OS_EXI_POLL=OS_REUSE+POLL+[POLL_RESULT]
OS_EXI_HANDLERS=OS_EXI_POLL+HANDLERS+[HANDLERS_RESULT]
OS_EXI_ID=OS_EXI_HANDLERS+ID+[ID_RESULT]
OS_EXI_ABSENT=OS_EXI_ID+ABSENT+[ABSENT_RESULT]
OS_SI_ENTRY=OS_EXI_ABSENT+SI_ENTRY+[SI_ENTRY_RESULT]
OS_SI_SAMPLE=OS_SI_ENTRY+SI_SAMPLE+[SI_SAMPLE_RESULT]
OS_SI_RETURN=OS_SI_SAMPLE+SI_RETURN+[SI_RETURN_RESULT]
OS_SRAM=OS_SI_RETURN+SRAM+[SRAM_RESULT]
OS_THREAD=OS_SRAM+THREAD+[THREAD_RESULT]
OS_AUDIO=OS_THREAD+AUDIO+[AUDIO_RESULT]
OS_DSP_STAGE=OS_AUDIO+DSP_STAGE+[DSP_STAGE_RESULT]
OS_DSP_SC=OS_DSP_STAGE+DSP_SC+[DSP_SC_RESULT]
OS_DSP_RETURN=OS_DSP_SC+DSP_RETURN+[DSP_RETURN_RESULT]
OS_REPORT=OS_DSP_RETURN+MI+[MI_RESULT]+REPORT+[b'V603_REPORT_RESULT reports=10 getters=6 native_console=1 computed=0 returned=1 output_backend=0 fallback=0 boot_verified=0']
OS_ARENA_CLEAR=OS_REPORT+ARENA_CLEAR+[b'V609_ARENA_RESULT lanes=2 reset=2 getters=6 zeros=20000 flush=16384 vectors=2 returned=1 hardware_cache=0 fallback=0 boot_verified=0']
OS_EXTERNAL=OS_ARENA_CLEAR+EXT+[EXT_RESULT]
OS_SI_DISPATCH=OS_EXTERNAL+SI_DISP+[SI_DISP_RESULT]
OS_SI_ACK=OS_SI_DISPATCH+SI_ACK+[SI_ACK_RESULT]
OS_SI_OS_LEAVES=OS_SI_DISPATCH+SI_ACK[:1]+[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]+[b'V688_SI_SECOND_STAGE n=1',b'V688_SI_SECOND_STAGE n=2',b'V688_SI_SECOND_ACK n=1']+SI_ACK[1:]+[SI_ACK_RESULT,POSTACK,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',b'V719_POSTACK_LOOP_POLL n=2',POSTACK_RETURN,POSTACK_END]
OS_SI_HANDLER_TIME=OS_SI_OS_LEAVES+TIME_STAGES+[b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=43 handler_return=0 boot_verified=0']
LOGS={name:log(lines) for name,lines in (
    ('startup',START+[START_RESULT]),('hardware',HW+[HW_RESULT]),
    ('cache',CACHE+[CACHE_RESULT]),('data',DATA),('os-entry',OS),
    ('os-time',OS_TIME),('os-hardware',OS_HARDWARE),('os-arena',OS_ARENA),('os-ipc',OS_IPC),('os-vector',OS_VECTOR),('os-pack',OS_PACK),('os-alarm',OS_ALARM),('os-irq',OS_IRQ),('os-mmio',OS_MMIO),('os-irq-return',OS_IRQ_RETURN),('os-context',OS_CONTEXT),('os-cache-reuse',OS_REUSE),('os-exi-poll',OS_EXI_POLL),('os-exi-handlers',OS_EXI_HANDLERS),('os-exi-id',OS_EXI_ID),('os-exi-absent',OS_EXI_ABSENT),('os-si-entry',OS_SI_ENTRY),('os-si-sample',OS_SI_SAMPLE),('os-si-return',OS_SI_RETURN),('os-sram',OS_SRAM),('os-thread',OS_THREAD),('os-audio',OS_AUDIO),('os-dsp-stage',OS_DSP_STAGE),('os-dsp-sc',OS_DSP_SC),('os-dsp-return',OS_DSP_RETURN),('os-report',OS_REPORT),('os-arena-clear',OS_ARENA_CLEAR),('os-external-entry',OS_EXTERNAL),('os-si-dispatch',OS_SI_DISPATCH),('os-si-ack',OS_SI_ACK),('os-si-os-leaves',OS_SI_OS_LEAVES),('os-si-handler-time',OS_SI_HANDLER_TIME))}


class Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(contract('startup',True),((),'prepare_v419_full_start.py','audit_v419_full_start'))
        self.assertEqual(contract('hardware')[0],HARDWARE_PATCHES)
        for scope in ('cache','data','os-entry','os-time'):
            self.assertEqual(contract(scope)[0],CACHE_PATCHES)
            with self.assertRaises(ValueError):contract(scope,True)
        self.assertEqual(contract('os-hardware'),(OS_HW_PATCHES,'prepare_v439_full_os_hardware.py','audit_v439_full_os_hardware'))
        self.assertEqual(contract('os-arena')[0],OS_HW_PATCHES)
        self.assertEqual(contract('os-ipc')[0],OS_IPC_PATCHES)
        self.assertEqual(OS_HW_PATCHES,('apply_function_root_v443','apply_perf_sprs_v29')+CACHE_PATCHES+('verify_perf_combo_v29','apply_hid4_continuous_v30'))
        self.assertEqual(OS_IPC_PATCHES,OS_HW_PATCHES+('apply_exact_dispatch_v445',))
        self.assertEqual(OS_VECTOR_PATCHES,OS_IPC_PATCHES+('apply_cache_continuous_v39','apply_cache_trace_v44','apply_dcbz_v67','apply_cache_order_v456'))
        self.assertEqual(contract('os-vector'),(OS_VECTOR_PATCHES,'prepare_v457_exception_vector.py','audit_v457_exception_vector'))
        self.assertEqual(contract('os-pack'),(OS_VECTOR_PATCHES,'prepare_v466_exception_pack.py','audit_v466_exception_pack'))
        self.assertEqual(contract('os-alarm'),(OS_VECTOR_PATCHES,'prepare_v470_alarm_startup.py','audit_v470_alarm_startup'))
        self.assertEqual(contract('os-irq'),(OS_VECTOR_PATCHES,'prepare_v473_module_irq.py','audit_v473_module_irq'))
        self.assertEqual(contract('os-mmio'),(OS_VECTOR_PATCHES,'prepare_v476_irq_mmio.py','audit_v476_irq_mmio'))
        self.assertEqual(contract('os-irq-return'),(OS_VECTOR_PATCHES,'prepare_v483_irq_return.py','audit_v483_irq_return'))
        self.assertEqual(contract('os-context'),(OS_VECTOR_PATCHES,'prepare_v486_context_startup.py','audit_v486_context_startup'))
        self.assertEqual(contract('os-cache-reuse'),(OS_VECTOR_PATCHES,'prepare_v488_os_cache_reuse.py','audit_v488_os_cache_reuse'))
        self.assertEqual(contract('os-exi-poll'),(OS_VECTOR_PATCHES,'prepare_v491_exi_poll.py','audit_v491_exi_poll'))
        self.assertEqual(contract('os-exi-handlers'),(OS_VECTOR_PATCHES,'prepare_v500_exi_handlers.py','audit_v500_exi_handlers'))
        self.assertEqual(contract('os-exi-id'),(OS_VECTOR_PATCHES,'prepare_v504_exi_id.py','audit_v504_exi_id'))
        self.assertEqual(contract('os-exi-absent'),(OS_VECTOR_PATCHES,'prepare_v510_exi_absent.py','audit_v510_exi_absent'))
        self.assertEqual(contract('os-si-entry'),(OS_VECTOR_PATCHES,'prepare_v520_si_entry.py','audit_v520_si_entry'))
        self.assertEqual(contract('os-si-sample'),(OS_VECTOR_PATCHES,'prepare_v524_si_sampling.py','audit_v524_si_sampling'))
        self.assertEqual(contract('os-si-return'),(OS_VECTOR_PATCHES,'prepare_v529_si_discovery.py','audit_v529_si_discovery'))
        self.assertEqual(OS_SRAM_PATCHES,OS_VECTOR_PATCHES+('apply_data_cache_invalidate_v532',))
        self.assertEqual(contract('os-sram'),(OS_SRAM_PATCHES,'prepare_v534_sram_read.py','audit_v534_sram_read'))
        self.assertEqual(contract('os-thread'),(OS_SRAM_PATCHES,'prepare_v549_thread_init.py','audit_v549_thread_init'))
        self.assertEqual(contract('os-audio'),(OS_SRAM_PATCHES,'prepare_v556_audio_reset.py','audit_v556_audio_reset'))
        self.assertEqual(contract('os-dsp-stage'),(OS_SRAM_PATCHES,'prepare_v559_dsp_stage.py','audit_v559_dsp_stage'))
        self.assertEqual(contract('os-dsp-sc'),(OS_SC_PATCHES,'prepare_v574_dsp_sc.py','audit_v574_dsp_sc'))
        self.assertEqual(contract('os-dsp-return'),(OS_SC_PATCHES,'prepare_v581_dsp_return.py','audit_v581_dsp_return'))
        self.assertEqual(OS_SC_PATCHES,OS_SRAM_PATCHES+('apply_native_lowmem_v63','apply_syscall_pc_v26','apply_syscall_transfer_v461'))
        for scope in ('os-hardware','os-arena','os-ipc','os-vector','os-pack','os-alarm','os-irq','os-mmio','os-irq-return','os-context','os-cache-reuse','os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return'):
            with self.assertRaises(ValueError):contract(scope,True)
        self.assertEqual(contract('os-report'),(OS_SC_PATCHES+('apply_bat_registers_v65',),'prepare_v603_boot_report.py','audit_v603_boot_report'))
        with self.assertRaises(ValueError):contract('os-report',True)
        self.assertEqual(contract('os-arena-clear'),(OS_SC_PATCHES+('apply_bat_registers_v65',),'prepare_v609_arena_clear.py','audit_v609_arena_clear'))
        with self.assertRaises(ValueError):contract('os-arena-clear',True)
        for name,auditor in zip(EXTERNAL_SCOPES,('audit_v663_external_entry','audit_v667_si_dispatch','audit_v672_si_ack_route','audit_v709_os_leaves','audit_v742_handler_time')):
            self.assertEqual(contract(name),(OS_SC_PATCHES+('apply_bat_registers_v65',),'prepare_v616_irq_enable.py',auditor))
            with self.assertRaises(ValueError):contract(name,True)
        self.assertEqual(set(LOGS),set(SCOPES))
        for scope in ('', 'bogus', 'CACHE'):
            with self.assertRaises(ValueError):contract(scope)
    def test_launch_flags(self):
        self.assertEqual(launch_flags('startup',True),{'UNDERCOVER_V426_SYNTHETIC':'1'})
        for scope in SCOPES:
            self.assertEqual(requires_external_overlay(scope),scope in EXTERNAL_SCOPES)
            if scope in EXTERNAL_SCOPES:
                self.assertTrue(all(f(scope) for f in (requires_sram_profile,requires_sc_overlay,requires_exi_profile,requires_si_profile)))
                expected={**launch_flags('os-arena-clear'),'UNDERCOVER_V616_IRQ':'1','UNDERCOVER_V663_EXTERNAL':'1'}
                if scope in EXTERNAL_SCOPES[1:]:expected['UNDERCOVER_V667_SI_DISPATCH']='1'
                if scope in EXTERNAL_SCOPES[2:]:expected['UNDERCOVER_V672_SI_ACK']='1'
                if scope in ('os-si-os-leaves','os-si-handler-time'):expected.update(UNDERCOVER_V699_SI_POSTACK='1',UNDERCOVER_V709_OS_LEAVES='1')
                if scope=='os-si-handler-time':expected.update(UNDERCOVER_V726_HANDLER_RETURN='1',UNDERCOVER_V742_HANDLER_TIME='1')
                self.assertEqual(launch_flags(scope),expected)
                continue
            if scope=='os-arena-clear':
                self.assertTrue(all(f(scope) for f in (requires_sram_profile,requires_sc_overlay,requires_exi_profile,requires_si_profile)))
                self.assertEqual(launch_flags(scope),{**launch_flags('os-report'),'UNDERCOVER_V609_ARENA':'1'})
                continue
            if scope=='os-report':
                self.assertTrue(all(f(scope) for f in (requires_sram_profile,requires_sc_overlay,requires_exi_profile,requires_si_profile)))
                self.assertEqual(launch_flags(scope),{**launch_flags('os-dsp-return'),'UNDERCOVER_V591_MI':'1','UNDERCOVER_V612_MAPPING':'1','UNDERCOVER_V603_REPORT':'1'})
                continue
            self.assertEqual(requires_sram_profile(scope),scope in ('os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return'))
            self.assertEqual(requires_sc_overlay(scope),scope in ('os-dsp-sc','os-dsp-return'))
            self.assertEqual(requires_exi_profile(scope),scope in ('os-exi-id','os-exi-absent','os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return'))
            self.assertEqual(requires_si_profile(scope),scope in ('os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return'))
            self.assertEqual(launch_flags(scope),{'UNDERCOVER_V419_START':'1',**({'UNDERCOVER_V475_IRQ_MMIO':'1'} if scope in ('os-mmio','os-irq-return','os-context','os-cache-reuse','os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V481_IRQ_BANKS':'1'} if scope in ('os-irq-return','os-context','os-cache-reuse','os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V490_EXI_CONTROLLER':'1'} if scope in ('os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V512_SI':'1'} if scope in ('os-si-entry','os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V522_VICLK':'0'} if scope in ('os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V537_ACR':'1'} if scope in ('os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V574_SC':'1'} if scope in ('os-dsp-sc','os-dsp-return') else {}),**({'UNDERCOVER_V581_DSP':'1'} if scope=='os-dsp-return' else {})})
        with self.assertRaises(ValueError):launch_flags('os-mmio',True)
    def test_all_scope_pairs(self):
        for scope in SCOPES:
            for source,raw in LOGS.items():
                with self.subTest(scope=scope,source=source):
                    self.assertEqual(audit(raw,0,scope)[1],scope==source)
    def test_optional_copy_and_hex_rejection(self):
        prefix=OS_TIME+[b'V439_HW_BEGIN copy=1']+OS_HW[:1]+[COPY]+OS_HW[1:]+[OS_HW_RESULT]
        for scope,tail in (('os-hardware',[]),('os-arena',OS_ARENA[len(OS_HARDWARE):]),('os-ipc',OS_IPC[len(OS_HARDWARE):]),('os-vector',OS_VECTOR[len(OS_HARDWARE):]),('os-pack',OS_PACK[len(OS_HARDWARE):]),('os-alarm',OS_ALARM[len(OS_HARDWARE):]),('os-irq',OS_IRQ[len(OS_HARDWARE):]),('os-mmio',OS_MMIO[len(OS_HARDWARE):]),('os-irq-return',OS_IRQ_RETURN[len(OS_HARDWARE):]),('os-context',OS_CONTEXT[len(OS_HARDWARE):]),('os-cache-reuse',OS_REUSE[len(OS_HARDWARE):]),('os-exi-poll',OS_EXI_POLL[len(OS_HARDWARE):]),('os-exi-handlers',OS_EXI_HANDLERS[len(OS_HARDWARE):]),('os-exi-id',OS_EXI_ID[len(OS_HARDWARE):]),('os-exi-absent',OS_EXI_ABSENT[len(OS_HARDWARE):]),('os-si-entry',OS_SI_ENTRY[len(OS_HARDWARE):]),('os-si-sample',OS_SI_SAMPLE[len(OS_HARDWARE):]),('os-si-return',OS_SI_RETURN[len(OS_HARDWARE):]),('os-sram',OS_SRAM[len(OS_HARDWARE):]),('os-thread',OS_THREAD[len(OS_HARDWARE):]),('os-audio',OS_AUDIO[len(OS_HARDWARE):]),('os-dsp-stage',OS_DSP_STAGE[len(OS_HARDWARE):]),('os-dsp-sc',OS_DSP_SC[len(OS_HARDWARE):]),('os-dsp-return',OS_DSP_RETURN[len(OS_HARDWARE):])):
            good=log(prefix+tail)
            self.assertTrue(audit(good,0,scope)[1])
            self.assertFalse(audit(good.replace(b'V439_HW_STAGE n=10 valid=1',b'V439_HW_STAGE n=a valid=1'),0,scope)[1])
            self.assertFalse(audit(good.replace(COPY+b'\n',b''),0,scope)[1])
    def test_postack_order_and_poll_markers(self):
        raw=LOGS['os-si-os-leaves']
        self.assertTrue(audit(raw,0,'os-si-os-leaves')[1])
        for bad in (raw.replace(LEAVES[0],LEAVES[1]),raw.replace(b'V719_POSTACK_LOOP_POLL n=2',b'V719_POSTACK_LOOP_POLL n=3'),raw.replace(POSTACK_RETURN,b'V688_SI_SECOND_INVALID reason=6 stage=2 trace=0'),raw+b'V718_POSTACK_REFUSAL kind=1 region=2 backward=1 masked=1 second=2 nested=4 leaves=3\n'):
            self.assertFalse(audit(bad,0,'os-si-os-leaves')[1])
        self.assertTrue(audit(raw.replace(b'V719_POSTACK_LOOP_POLL n=1\nV719_POSTACK_LOOP_POLL n=2\n',b''),0,'os-si-os-leaves')[1])
    def test_original_windows_handler_time_installer_order(self):
        from pathlib import Path
        build=(Path(__file__).parent /
               'windows_full_build_v426.py').read_text(encoding='utf-8')
        guard="if scope=='os-si-handler-time':"
        baseline="if scope in ('os-si-os-leaves','os-si-handler-time'):"
        prior="run_stage('si_os_leaf_observer'"
        follow="run_stage('handler_return_observer'"
        time="run_stage('handler_time_observer'"
        self.assertIn(baseline,build)
        self.assertEqual(build.count(guard),2)
        self.assertEqual(build.count(follow),1)
        self.assertEqual(build.count(time),1)
        self.assertTrue(build.index(prior)<build.index(follow)<build.index(time))
        self.assertIn("from audit_v742_handler_time import diagnostic",build)
        self.assertIn('if handler_time_diagnostic(line):print(line.decode(),flush=True)',build)

    def test_handler_time_scoped_native_marker_contract(self):
        raw=LOGS['os-si-handler-time']
        self.assertIn(b'V726_HANDLER_STAGE n=2',raw)
        self.assertIn(b'V742_TIME_LEAF ordinal=3 n=3',raw)
        self.assertTrue(audit(raw,0,'os-si-handler-time')[1])
        self.assertFalse(audit(raw,0,'os-si-os-leaves')[1])
        self.assertFalse(audit(LOGS['os-si-os-leaves'],0,'os-si-handler-time')[1])
        self.assertFalse(audit(raw.replace(b'V742_TIME_STAGE n=2',
                                           b'V742_TIME_STAGE n=3',1),0,
                               'os-si-handler-time')[1])
        self.assertFalse(audit(raw+b'V742_TIME_INVALID reason=3 stage=2 '
                               b'leaf=2 witness=1 trace=0\n',0,
                               'os-si-handler-time')[1])
        self.assertFalse(audit(raw+b'V726_HANDLER_INVALID kind=3 '
                               b'witness=4 stage=2 visits=20 polls=0\n',
                               0,'os-si-handler-time')[1])
        for prior in ('os-si-ack','os-si-dispatch','os-external-entry'):
            with self.subTest(prior=prior):
                self.assertFalse(audit(raw,0,prior)[1])

    def test_exit_and_duplicates(self):
        for scope,raw in LOGS.items():
            for rc in (1,124,134,256,0xc0000005,-1,-1073741819):
                self.assertFalse(audit(raw,rc,scope)[1])
            self.assertFalse(audit(raw+raw.splitlines()[-1]+b'\n',0,scope)[1])
            self.assertFalse(audit(log(raw.splitlines()[:-1]),0,scope)[1])
            self.assertTrue(audit(b'private non-marker line\n'+raw,0,scope)[1])
    def test_foreign_markers_and_bounds(self):
        for scope,raw in LOGS.items():
            for prefix in PREFIXES+FAILURE_PREFIXES:
                self.assertFalse(audit(raw+prefix+b'UNEXPECTED\n',0,scope)[1])
        with self.assertRaises(ValueError):audit(b'x'*(MAX_LOG+1),0,'startup')
        with self.assertRaises(ValueError):audit(b'',0,'bad')
if __name__=='__main__':unittest.main()
