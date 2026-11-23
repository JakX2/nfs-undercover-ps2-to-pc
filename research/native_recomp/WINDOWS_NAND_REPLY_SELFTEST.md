# Windows native Wii NAND IPC and Y1 exception self-test

The **original-free C++20 tests** exercise two distinct native runtime
milestones in the Undercover Wii/PS2-to-PC recompilation project:

- **V374:** Submit genuine Broadway IPC/X1 requests, service native
  Starlet ACKs, acknowledge Y2 and Hollywood PPC_FLAG, publish queued Y1
  replies in FIFO order, and retain a negative IOS error without converting
  it into success.
- **V376:** Deliver a real native Y1 after a completed IOS request,
  reject unsupported interrupt states, confirm exact installed vector
  bytes, save the next guest PC to SRR0 and masked MSR to SRR1, preserve
  registers, and leave the IRQ latch for the original guest handler.
  A second fixture checks that an existing Y1 remains interruptible while
  another validated IOS completion remains queued.

**These are original-free host/runtime tests, not execution of the
proprietary Wii game, guest vector body, OS IRQ handler or frontend.**
Only authenticated owner-original CI can establish those milestones.

On Windows, use a **Visual Studio 2022 Developer Command Prompt** or
a terminal with **MinGW-w64 g++** installed. Check out the latest
\`research/wii-native-recomp-preflight\` branch and, from the repository
root, run:

\`\`\`bat
research\native_recomp\windows_nand_reply_selftest.bat
\`\`\`

The script builds both test programs as native Windows executables
and cleans its isolated temporary build directory. No game executable,
ISO, keys, NAND, or asset files are required.

Expected final messages:

\`\`\`text
PASS: V374 authentic ACK, Y2/flag, queued Y1 and negative IOS reply
PASS: V376 authentic IOS Y1 exception entry saves guest SRRs and keeps reply latched
PASS: Windows C++20 V374 and V376 native IPC/IRQ regressions.
\`\`\`

If the script fails, share the console output, compiler version and the
final FAIL message. Do **not** share private game binaries, extracted
assets, or game-derived translated source code.

The private authenticated NAND boot experiment must additionally prove
entry through the original PowerPC vector and later dispatch to the
installed guest handler before any full boot claim is possible.
