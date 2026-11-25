#!/usr/bin/env python3
"""Install both previously authenticated routes into the same full image."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v738_handler_restore import install as restore
from prepare_v742_handler_time import install as time
from prepare_v756_combined_handler import after_restore
def install(dol,elf,root,host):
    restore(dol,elf,root,host)
    time(dol,elf,root,host,handler_patch=after_restore)
    print('V760_COMBINED_ROUTE installed=1 time_slot=3 restore_slot=12 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError):
        print('V760_COMBINED_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
