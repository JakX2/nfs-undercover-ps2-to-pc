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
def wireless_zero_fixture():
    # Four big-endian 16-bit wireless IDs in extended SRAM. Keep the
    # base profile, boot/configuration bytes and all other fields intact.
    data=bytearray(sram_fixture())
    data[48:56]=bytes(8)
    return bytes(data)
def payload(profile='pattern'):
    if profile not in ('pattern','wireless-zero'):raise ValueError('profile mode')
    return encode(0xbeef0010,1,0x12345678,8,
                  wireless_zero_fixture() if profile=='wireless-zero' else sram_fixture())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--profile',choices=('pattern','wireless-zero'),default='pattern');a=p.parse_args()
    try:create(a.output,payload(a.profile))
    except (OSError,ValueError):
        print('V536_SRAM_TEST_PROFILE created=0');return 1
    print('V536_SRAM_TEST_PROFILE created=1 synthetic=1 bytes=64')
    if a.profile=='wireless-zero':print('V1196_SRAM_PROFILE selected=wireless-zero ids_zero=4 other_bytes_preserved=56 synthetic=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
