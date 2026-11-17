# Original-free V33 preflight: private next-OSInit control-flow probe

The verified continuous original Wii `__start` test reaches its V32
explicitly synthetic stop at `0x80520818`. The next original code path,
including MEM2 and subsequent Wii OS initialization, remains unimplemented
in the continuous runner.

`probe_next_osinit_v33.py` reads **only** an owner-private, SHA-256-pinned
original Wii DOL staged in the GitHub Actions private runner. It scans a
fixed 512-byte window beginning at `0x80520818`. No PowerPC disassembly,
instruction words, original binary, game-derived generated C++, symbol
table or raw code is emitted. It prints bounded opcode-class counts
and at most twelve guest-address-only direct call edges.

`test_probe_next_osinit_v33.py` uses independent synthetic PowerPC
instructions to validate direct BL signed target decoding, class accounting,
input bounds and rejection behavior. The cloud owner flow runs the probe
**only after** V32's verified original guest-PC checkpoint has passed;
it is static exploration, not a new V33 execution milestone.

Next engineering work is to use the bounded control-flow evidence plus
owner-only original DOL validation to implement real MEM2-related guest
calls in the same continuous original startup dispatcher. New native
execution must retain explicit test-only boundaries and show an
instrumented later guest PC before incrementing the verified stage.

No full native boot, game main, first frame or gameplay is established.
