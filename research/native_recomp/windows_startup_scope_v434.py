"""Select complete-image Windows startup contracts without cross-scope success."""
from importlib import import_module

HARDWARE_PATCHES=('apply_hid_state_v18','apply_fpscr_v19')
CACHE_PATCHES=HARDWARE_PATCHES+('apply_l2cr_v20','apply_mtmsr_resume_v74')
OS_HW_PATCHES=('apply_function_root_v443','apply_perf_sprs_v29')+CACHE_PATCHES+('verify_perf_combo_v29','apply_hid4_continuous_v30')
OS_IPC_PATCHES=OS_HW_PATCHES+('apply_exact_dispatch_v445',)
OS_VECTOR_PATCHES=OS_IPC_PATCHES+('apply_cache_continuous_v39','apply_cache_trace_v44','apply_dcbz_v67','apply_cache_order_v456')
SCOPES={
    'startup':((), 'prepare_v419_full_start.py','audit_v419_full_start'),
    'hardware':(HARDWARE_PATCHES,'prepare_v425_full_hardware.py','audit_v425_full_hardware'),
    'cache':(CACHE_PATCHES,'prepare_v428_full_cache.py','audit_v428_full_cache'),
    'data':(CACHE_PATCHES,'prepare_v430_full_data.py','audit_v430_full_data'),
    'os-entry':(CACHE_PATCHES,'prepare_v433_full_os_entry.py','audit_v433_full_os_entry'),
    'os-time':(CACHE_PATCHES,'prepare_v435_full_os_time.py','audit_v435_full_os_time'),
    'os-hardware':(OS_HW_PATCHES,'prepare_v439_full_os_hardware.py','audit_v439_full_os_hardware'),
    'os-arena':(OS_HW_PATCHES,'prepare_v444_full_os_arena.py','audit_v444_full_os_arena'),
    'os-ipc':(OS_IPC_PATCHES,'prepare_v446_full_os_ipc.py','audit_v446_full_os_ipc'),
    'os-vector':(OS_VECTOR_PATCHES,'prepare_v457_exception_vector.py','audit_v457_exception_vector'),
    'os-pack':(OS_VECTOR_PATCHES,'prepare_v466_exception_pack.py','audit_v466_exception_pack'),
    'os-alarm':(OS_VECTOR_PATCHES,'prepare_v470_alarm_startup.py','audit_v470_alarm_startup'),
    'os-irq':(OS_VECTOR_PATCHES,'prepare_v473_module_irq.py','audit_v473_module_irq'),
    'os-mmio':(OS_VECTOR_PATCHES,'prepare_v476_irq_mmio.py','audit_v476_irq_mmio'),
    'os-irq-return':(OS_VECTOR_PATCHES,'prepare_v483_irq_return.py','audit_v483_irq_return'),
    'os-context':(OS_VECTOR_PATCHES,'prepare_v486_context_startup.py','audit_v486_context_startup'),
    'os-cache-reuse':(OS_VECTOR_PATCHES,'prepare_v488_os_cache_reuse.py','audit_v488_os_cache_reuse'),
    'os-exi-poll':(OS_VECTOR_PATCHES,'prepare_v491_exi_poll.py','audit_v491_exi_poll'),
    'os-exi-handlers':(OS_VECTOR_PATCHES,'prepare_v500_exi_handlers.py','audit_v500_exi_handlers'),
    'os-exi-id':(OS_VECTOR_PATCHES,'prepare_v504_exi_id.py','audit_v504_exi_id'),
    'os-exi-absent':(OS_VECTOR_PATCHES,'prepare_v510_exi_absent.py','audit_v510_exi_absent'),
    'os-si-entry':(OS_VECTOR_PATCHES,'prepare_v520_si_entry.py','audit_v520_si_entry'),
}
PREFIXES=(b'V419_FULL_START_',b'V425_HARDWARE_',b'V428_CACHE_',b'V430_DATA_',b'V433_OS_',b'V435_TIME_',b'V439_HW_',b'V444_ARENA_',b'V446_IPC_',b'V457_VECTOR_',b'V466_PACK_',b'V470_ALARM_',b'V473_IRQ_',b'V476_MMIO_',b'V483_IRQ_RETURN_',b'V486_CONTEXT_',b'V488_REUSE_',b'V491_EXI_POLL_',b'V500_EXI_HANDLER_',b'V504_EXI_ID_',b'V510_EXI_ABSENT_',b'V520_SI_ENTRY_',b'V524_SI_SAMPLE_')
ALLOWED={
    'startup':PREFIXES[:1], 'hardware':PREFIXES[1:2],
    'cache':PREFIXES[1:3], 'data':PREFIXES[1:4], 'os-entry':PREFIXES[1:5], 'os-time':PREFIXES[1:6],
    'os-hardware':PREFIXES[1:7], 'os-arena':PREFIXES[1:8], 'os-ipc':PREFIXES[1:9],
    'os-vector':PREFIXES[1:10], 'os-pack':PREFIXES[1:11],
    'os-alarm':PREFIXES[1:12], 'os-irq':PREFIXES[1:13], 'os-mmio':PREFIXES[1:14], 'os-irq-return':PREFIXES[1:15], 'os-context':PREFIXES[1:16], 'os-cache-reuse':PREFIXES[1:17], 'os-exi-poll':PREFIXES[1:18], 'os-exi-handlers':PREFIXES[1:19], 'os-exi-id':PREFIXES[1:20], 'os-exi-absent':PREFIXES[1:21], 'os-si-entry':PREFIXES[1:22],
}
MAX_LOG=8*1024*1024


def contract(scope,synthetic=False):
    if scope not in SCOPES or (synthetic and scope!='startup'):
        raise ValueError('owner_scope')
    return SCOPES[scope]


def requires_exi_profile(scope):
    contract(scope)
    return scope in ('os-exi-id','os-exi-absent','os-si-entry')


def requires_si_profile(scope):
    contract(scope)
    return scope=='os-si-entry'


def launch_flags(scope,synthetic=False):
    contract(scope,synthetic)
    flags={'UNDERCOVER_V426_SYNTHETIC' if synthetic else 'UNDERCOVER_V419_START':'1'}
    if scope in ('os-mmio','os-irq-return','os-context','os-cache-reuse','os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry'):flags['UNDERCOVER_V475_IRQ_MMIO']='1'
    if scope in ('os-irq-return','os-context','os-cache-reuse','os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry'):flags['UNDERCOVER_V481_IRQ_BANKS']='1'
    if scope in ('os-exi-poll','os-exi-handlers','os-exi-id','os-exi-absent','os-si-entry'):flags['UNDERCOVER_V490_EXI_CONTROLLER']='1'
    if requires_si_profile(scope):flags['UNDERCOVER_V512_SI']='1'
    return flags


def audit(raw,rc,scope):
    _,_,module=contract(scope)
    if len(raw)>MAX_LOG:raise ValueError('log size')
    auditor=import_module(module)
    accepted=getattr(auditor,'MARKERS',ALLOWED[scope])
    for line in raw.splitlines():
        if line.startswith(PREFIXES) and not line.startswith(accepted):
            return f'V434_WINDOWS_SCOPE_REJECT scope={scope} reason=foreign_marker verified=0 boot_verified=0',False
    # Windows returns 32-bit exception codes, not POSIX 8-bit statuses.
    # Never truncate a nonzero code to zero.
    return auditor.inspect(raw,rc if 0<=rc<=255 else 255)
