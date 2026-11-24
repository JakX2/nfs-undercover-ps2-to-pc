#!/usr/bin/env python3
"""Explicit nonzero owner-test SRAM profile; no console dump or persistence."""
import argparse
from pathlib import Path
from write_exi_profile_v505 import encode,create
def sram_fixture():
    data=bytearray((17*i+7)&255 for i in range(64))
    data[60]=0x12
    data[61]=0
    return bytes(data)
def payload():
    return encode(0xbeef0010,1,0x12345678,8,sram_fixture())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
    try:create(a.output,payload())
    except (OSError,ValueError):
        print('V536_SRAM_TEST_PROFILE created=0');return 1
    print('V536_SRAM_TEST_PROFILE created=1 synthetic=1 bytes=64');return 0
if __name__=='__main__':raise SystemExit(main())
