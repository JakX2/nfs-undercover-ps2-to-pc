# V109 candidate: native nonempty Wii System Configuration pathname

After authentic owner DOL initialized data restoration (V108),
the original SC path at 0x8051E71C takes an additional string-copy
edge 0x8051E798 -> 0x8054B4B4, returning to 0x8051E79C.
V109 executes the *real translated leaf* with the actual guest r3/r4
input pointers, checks the complete NUL-terminated result against
pre-call bytes, and stops at the next original strlen edge
0x8051E7A0 -> 0x80544AC0.

The earlier empty-reduced-fixture V104 async-submit path remains
independent; this tests the authenticated nonempty original branch,
not simulated path contents, fabricated IOS success, or a game boot.
The owner DOL/ELF and generated translated code remain private.
