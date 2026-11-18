# V102 candidate: original SC pathname preparation

V101 verified the original system configuration loader selects its
0x8051E71C path-building child. V102 restores that child and the
original 0x80544AC0 strlen function, retaining the previously restored
0x8054B4B4 strcpy. The owner-original execution is checked for
bounded string lengths, original guest string copy bytes and authentic
continuation to 0x8051E3DC.

No private pathname is printed or copied to public source. The
inherited pending STM event, FS/ES descriptor state and running
thread must remain unchanged. This is not an SC configuration
file-load completion.
