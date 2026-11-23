#!/usr/bin/env python3
"""V394 private original NAND _isfsFuncCb entry bounded public audit."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from diagnose_v299_native_log import WINDOW,category,read_edges,size_band
from scan_original_guest_markers import scan_original_guest_markers
ENTRY=re.compile(r'^V394_NAND_ISFS_ENTRY guest=([01]) clear=([01]) masked=([01]) registered=([01]) mapped=([01]) selected=([01]) result=([01]) userdata=([01])$')
TRIAL=re.compile(r'^V394_NAND_ISFS_TRIAL context=([01]) isfs=([01]) completed=([01])$')
def inspect(path:Path,rc:int)->str:
    size,lines,overflow=scan_original_guest_markers(path,(ENTRY,TRIAL))
    entries=trials=0
    mapped_any=selected_any=result_any=userdata_any=0
    valid=True
    for line in lines:
        e=ENTRY.fullmatch(line)
        if e:
            if entries!=trials or entries>=16:valid=False;break
            entries+=1
            guest,clear,masked,registered,mapped,selected,result,userdata=map(int,e.groups())
            valid=valid and bool(guest and clear and masked and registered)
            mapped_any|=mapped;selected_any|=selected
            result_any|=result;userdata_any|=userdata
            continue
        t=TRIAL.fullmatch(line)
        if t:
            if trials>=entries or trials>=16:valid=False;break
            trials+=1
            valid=valid and all(x=='1' for x in t.groups())
    return (
        f'V394_NAND_ISFS_CENSUS rc={rc} kind={category(rc)} '
        f'size_band={size_band(size)} sample_complete={int(size<=WINDOW)} '
        f'entries={entries} trials={trials} mapped_any={mapped_any} '
        f'selected_any={selected_any} result_any={result_any} '
        f'userdata_any={userdata_any} '
        f'isfs_entry_verified={int(bool(not overflow and valid and entries and entries==trials))}'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:print(inspect(a.private_original_log,a.native_exit_code))
    except (OSError,ValueError):
        print('V394_NAND_ISFS_AUDIT verified=0',file=sys.stderr)
        return 1
    print('V394_NAND_ISFS_AUDIT verified=1')
    return 0
if __name__=="__main__":raise SystemExit(main())
