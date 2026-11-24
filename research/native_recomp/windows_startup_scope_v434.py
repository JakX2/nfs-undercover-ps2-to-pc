"""Select complete-image Windows startup contracts without cross-scope success."""
from importlib import import_module

HARDWARE_PATCHES=('apply_hid_state_v18','apply_fpscr_v19')
CACHE_PATCHES=HARDWARE_PATCHES+('apply_l2cr_v20','apply_mtmsr_resume_v74')
SCOPES={
    'startup':((), 'prepare_v419_full_start.py','audit_v419_full_start'),
    'hardware':(HARDWARE_PATCHES,'prepare_v425_full_hardware.py','audit_v425_full_hardware'),
    'cache':(CACHE_PATCHES,'prepare_v428_full_cache.py','audit_v428_full_cache'),
    'data':(CACHE_PATCHES,'prepare_v430_full_data.py','audit_v430_full_data'),
    'os-entry':(CACHE_PATCHES,'prepare_v433_full_os_entry.py','audit_v433_full_os_entry'),
    'os-time':(CACHE_PATCHES,'prepare_v435_full_os_time.py','audit_v435_full_os_time'),
}
PREFIXES=(b'V419_FULL_START_',b'V425_HARDWARE_',b'V428_CACHE_',b'V430_DATA_',b'V433_OS_',b'V435_TIME_')
ALLOWED={
    'startup':PREFIXES[:1], 'hardware':PREFIXES[1:2],
    'cache':PREFIXES[1:3], 'data':PREFIXES[1:4], 'os-entry':PREFIXES[1:5], 'os-time':PREFIXES[1:],
}
MAX_LOG=8*1024*1024


def contract(scope,synthetic=False):
    if scope not in SCOPES or (synthetic and scope!='startup'):
        raise ValueError('owner_scope')
    return SCOPES[scope]


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
