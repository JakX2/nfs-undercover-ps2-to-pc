#!/usr/bin/env python3
"""Private opt-in continuation after the authenticated V786 alarm return.

No new original target is admitted. The existing handler guard still
refuses linked calls; the extra observer only classifies a refused CTR.
"""
import argparse
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL, replace_exact
from prepare_v668_si_ack import geometry, HANDLER
from prepare_v667_si_dispatch import exact
from audit_callback_deps_v787 import CALLBACK, callback_sites
from make_private_elf_symbol_map import parse_functions


def expectations(dol, elf):
    n, *_ = geometry(dol, elf)
    sites = callback_sites(HANDLER, exact(dol, elf, HANDLER, n))
    if [ordinal for ordinal, _ in sites] != [6, 11]:
        raise ValueError('callback sites')
    size = parse_functions(elf).get(CALLBACK, 0)
    if not 4 <= size <= 4096 or size & 3:
        raise ValueError('callback extent')
    words = exact(dol, elf, CALLBACK, size // 4)
    return CALLBACK, words, tuple(pc for _, pc in sites)


def patch_private(s, candidate, words, sites):
    if (len(sites) != 2 or not 1 <= len(words) <= 1024 or
            not s.endswith('\n}\n') or 'callback_candidate' in s):
        raise ValueError('private header')
    return s[:-2] + (
        f'inline constexpr uint32_t callback_candidate=0x{candidate:08x}u;\n'
        f'inline constexpr std::array<uint32_t,{len(words)}> callback_words{{'
        + ','.join(f'0x{w:08x}u' for w in words) + '};\n'
        'inline constexpr std::array<uint32_t,2> callback_sites{'
        + ','.join(f'0x{pc:08x}u' for pc in sites) + '};\n}\n'
    )


def patch_alarm(s):
    a = '#include "v786_private_alarm.h"'
    s = replace_exact(s, a, a + '\n#include "wii_callback_identity_v796.h"')
    a = 'inline bool active(){return route.stage()>=1&&route.stage()<=3;}'
    s = replace_exact(s, a, a + r'''
inline bool continue_suffix(){
    const char* v=std::getenv("UNDERCOVER_V789_ALARM_SUFFIX");
    return v&&v[0]=='1'&&v[1]=='\0';
}
// Only called after the existing handler guard has refused the instruction.
template<class C>void classify(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    const auto category=classify_callback_identity(c,pc,w,ordinal,kind,callback_candidate,
        callback_words,callback_sites);
    std::cout<<std::dec<<"V789_ALARM_BOUNDARY ordinal="<<ordinal<<" kind="<<kind
        <<" target_class="<<category<<" executed=0"<<std::endl;
}
''')
    a = '<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    return replace_exact(s, a, a.replace('std::_Exit(0);', 'if(!continue_suffix())std::_Exit(0);'))


def patch_handler(s):
    a = '        v786::returned(c,pc,w);\n        return;'
    s = replace_exact(s, a, '''        v786::returned(c,pc,w);
        if(!v786::continue_suffix())std::_Exit(0);
        if(!witness.alarm_returned(c,pc,v786::route.total(),held()))reject(3);''')
    a = '            std::cout<<std::dec<<"V778_NEXT_BOUNDARY ordinal="'
    return replace_exact(s, a, '''            if(v786::continue_suffix()&&v786::route.stage()==4&&
               (witness.completed_calls()&16u))v786::classify(c,pc,w,ordinal,kind);
''' + a)


def install(dol, elf, generated):
    candidate, words, sites = expectations(dol, elf)
    dest = generated / 'nWiiRuntime/include/undercover'
    edits = {
        'v786_private_alarm.h': lambda s: patch_private(s, candidate, words, sites),
        'wii_alarm_return_binding_v786.h': patch_alarm,
        'wii_si_handler_return_binding_v726.h': patch_handler,
    }
    pending = {}
    if dest.is_symlink() or not dest.is_dir():
        raise ValueError('destination')
    for name, patch in edits.items():
        p = dest / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1024 * 1024:
            raise ValueError('destination')
        pending[p] = patch(p.read_text())
    header = dest / 'wii_callback_identity_v796.h'
    if header.exists() or header.is_symlink():
        raise ValueError('destination')
    pending[header] = (Path(__file__).parent / header.name).read_text()
    for p, content in pending.items():
        p.write_text(content)
    print('V789_ALARM_SUFFIX installed=1 callback_sites=2 slot=5 dispatch=0 execution=0')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('dol', type=Path)
    p.add_argument('elf', type=Path)
    p.add_argument('generated', type=Path)
    a = p.parse_args()
    try:
        if a.dol.stat().st_size > MAX_DOL or a.elf.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('size')
        install(a.dol.read_bytes(), a.elf.read_bytes(), a.generated)
    except (OSError, ValueError, UnicodeError, struct.error, IndexError):
        print('V789_ALARM_SUFFIX installed=0')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
