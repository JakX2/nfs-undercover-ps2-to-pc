#!/usr/bin/env python3
"""Source-verified Windows saved-context bridge for eventual native RFI.

Compose the already tested original V751 cold SI snapshot and V921
saved-frame join against the full translated Windows binding headers.
Default mode is a read-only compatibility preflight. --install explicitly
writes guarded native observers; the original Windows RFI is NOT enabled.

No owner DOL, ELF, asset, translated game body or private execution trace
is copied into the repository.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from prepare_v419_full_start import replace_exact
from prepare_v751_cold_capture import patch as patch_capture
from prepare_v921_capture_join import patch_capture as patch_join_capture

HEADERS=('wii_external_return_v706.h',
         'wii_cold_return_capture_v741.h',
         'wii_saved_context_join_v921.h')


def patch_external(s: str) -> str:
    """Capture pre-exception registers and join the same saved frame."""
    if type(s) is not str or 'V751_CAPTURE_STAGE n=1' in s:
        raise ValueError('context external duplicate')
    return patch_join_capture(patch_capture(s))


def patch_handler(s: str) -> str:
    """Join on the original V920 return only if the capture was requested.

    All existing 11- to 15-stage Windows execution flags leave this disabled.
    """
    if type(s) is not str or 'windows_context_bridge_enabled' in s:
        raise ValueError('context handler duplicate')
    include='#include "v920_private_handler_resume.h"'
    s=replace_exact(s,include,include+'\n#include "wii_saved_context_join_v921.h"')
    anchor='template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){'
    helper='''inline bool windows_context_bridge_enabled(){
    const char* v=std::getenv("UNDERCOVER_V751_CAPTURE");
    return v&&v[0]=='1'&&v[1]=='\\0';
}
'''
    s=replace_exact(s,anchor,helper+anchor)
    marker='    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;'
    join='''    if(windows_context_bridge_enabled()){
        if(!v921::join.returned(c,v921::join.context()))reject(6);
        std::cout<<"WINDOWS_RFI_CONTEXT_JOIN original_snapshot=1 original_handler_return=1 saved_gprs=32 special=6 same_cpu=1 rfi=0 boot_verified=0"<<std::endl;
    }
'''
    return replace_exact(s,marker,marker+'\n'+join)


def plan(generated: Path, host: Path) -> dict[Path,str]:
    if not isinstance(generated,Path) or not isinstance(host,Path):
        raise ValueError('context arguments')
    dest=generated/'nWiiRuntime/include/undercover'
    external=dest/'wii_external_entry_binding_v663.h'
    handler=dest/'wii_handler_suffix_binding_v868.h'
    if (dest.is_symlink() or not dest.is_dir() or
            any(p.is_symlink() or not p.is_file() for p in (external,handler))):
        raise ValueError('context binding tree')
    result={
        external:patch_external(external.read_text(encoding='utf-8')),
        handler:patch_handler(handler.read_text(encoding='utf-8')),
    }
    for name in HEADERS:
        file=dest/name
        reference=host/name
        if reference.is_symlink() or not reference.is_file():
            raise ValueError('context reference')
        contents=reference.read_text(encoding='utf-8')
        if file.is_symlink() or (file.exists() and
                (not file.is_file() or file.read_text(encoding='utf-8')!=contents)):
            raise ValueError('context header conflict')
        if not file.exists():
            result[file]=contents
    return result


def install(generated:Path,host:Path,*,write:bool=False)->int:
    if type(write) is not bool:raise ValueError('context install option')
    changes=plan(generated,host)
    if write:
        for path,contents in changes.items():path.write_text(contents,encoding='utf-8')
    return len(changes)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('generated',type=Path)
    parser.add_argument('--install',action='store_true')
    a=parser.parse_args()
    try:
        count=install(a.generated,Path(__file__).resolve().parent,write=a.install)
    except (OSError,ValueError,UnicodeError):
        print('WINDOWS_RFI_CONTEXT_BRIDGE ready=0 execution=0 boot_verified=0')
        return 1
    print(f'WINDOWS_RFI_CONTEXT_BRIDGE ready=1 files={count} installed={int(a.install)} '
          'pre_exception=1 saved_frame=1 handler_join=1 native_rfi=0 '
          'execution=0 boot_verified=0')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
