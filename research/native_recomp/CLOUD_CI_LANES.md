# Three Wii native recompilation CI lanes

These are three specialized **GitHub Actions workflows**, not new hourly
ChatGPT tasks. The existing Undercover hourly development task stays active.

## 1. Wii Continuous Startup Checks

Automatic source-only run: the boot checkpoint parser tests plus real
NWiiRecomp synthetic V25 startup compilation and native dispatch.

Manual owner-original run (research branch only): SHA-pinned Wii DOL,
actual V25 bounded continuous __start test, private C++ generation,
native execution, exact ownership and safety checks. This V25 harness
does NOT claim the V26 0x805206B4 stop or V68 direct OSInit continuation:
the V26 source-only harness remains incomplete in the public branch.
The private V25 test currently emits no verified BOOT_PROGRESS line.
Successful results MUST be called passed_uninstrumented.

The next native-engineering task is recovering the missing V26 harness,
joining it to V68's directly executed original OSInit code and measuring
the next authentic __start stop.

## 2. Wii PowerPC Runtime Tests

Original-free synthetic C++20 executable tests, using pinned upstream
NWiiRecomp revision 595f176f1d24cc54ff2e8389feed12d7fb553cc2.
The V5 lane verifies indexed paired-single memory operations, signed
GQR and SPRG registers, reciprocal estimates and native CPU context.
An isolated V19 lane verifies synthetic FPR/FPSCR initialization and
inter-function native dispatch. V44 cache-trace patch guards are also
executed. No owner Wii file or credential is required.

These tests do not prove hardware-exact cache/MMU timings or Wii service
completeness.

## 3. Wii Full Recompilation Build Probe

Fast source-only synthetic ELF32 PPC symbol reader regression tests run
automatically when the research branch changes.

Optional manual owner-private full-image trial obtains the exact DOL and
unstripped ELF via existing two GitHub Actions secrets, validates both
SHA-256 fingerprints, generates an anonymized privately held symbol CSV,
applies existing original-free V4/V5/V6 translator patches, and invokes
the complete owner Wii DOL translation into generated C++ shards. It
checks for explicit unsupported-opcode traps and compiles generated C++
in syntax-only mode. The manual input named scope can be sample (first,
last and dispatcher) or all (every generated numbered shard).

The full-image path is an experimental, fail-closed translation/syntax
probe. It can expose existing upstream or game-version gaps on its
first original trial. A successful syntax check is NOT a linked complete
Windows executable, complete original __start, main, frontend, first
frame or gameplay.

## Manual Actions setup

Workflow dispatch buttons require a matching workflow file on default
main. The default branch will contain three independent, source-only
registration stubs. When choosing Run workflow, select branch
research/wii-native-recomp-preflight to execute the real workflows
and NOT the default-branch registration stubs.

Original-private lanes use the ALREADY configured Actions secrets
WII_ORIGINAL_DOL_ID and WII_ORIGINAL_ELF_ID and Actions repository
variable WII_GHIDRA_PRIVATE_ENABLED=true. Original game files,
derived source, symbol map, binary outputs and diagnostic logs are
never published or cached. Only aggregate PASS/FAIL results are logged.
The native runtime workflow uses no game files, private variables or
Drive credentials.

The Ghidra workflow and existing private V68 OSInit regression remain
separate. The verified continuous V26 __start checkpoint is still
0x805206B4; direct V68 OSInit is 0x804EFA34. Do not combine their
milestones or infer game boot from independent subtest passes.
