# V27: candidate genuine continuous post-time interrupt call seam

Status: IMPLEMENTED FOR TESTING. Do not claim V27 startup advancement
until the owner-original GitHub Actions CI job has actually succeeded.

The V26 cloud-recovered continuous owner test has proved the original
entry 0x8000403C through the original OS time and interrupt helpers and
a test-only stop at 0x805206B4.

This V27 *independent source-only harness* starts with the exact same
verified owner-original V26 private DOL fixture and replaces that test-only
stop with two additional authentic PowerPC instructions, including the
original branch-and-link to __RAS_OSDisableInterrupts_begin. That call
returns to the OSInit fallthrough. A new test-only SC is inserted at
0x805206BC, BEFORE executing the original __OSGetExecParams call.

New C++ native assertions verify:
- guest dispatch from original __start (not direct-entry OSInit)
- the original branch at 0x805206B4 targets 0x805265AC
- 2 authentic interrupt-disable helper calls (one inside system-time code,
  one from OSInit after the original time stores)
- authentic saved OS time words in guest memory before the second disable
- exact syscall callback PC at 0x805206BC
- guest MSR EE cleared by the second interrupt-disable operation
- the original cache/FPR/paired-single/init-data/DBInit/BSS contracts carried
  forward from the independently verified recovered V26 native harness
- no interpreter fallback or undocumented continuation

All original PPC body bytes are read from the owner's SHA-256-verified DOL
at runtime; no original executable, translated C++, private symbol list,
raw logs or assets are committed or uploaded.

Reproduction with privately held game data and pinned NWiiRecomp:
    bash run_v26_recovered_tests.sh /private/NWiiRecomp /private/NfsMWRelease.dol
    bash run_v27_continuous_interrupt.sh /private/NWiiRecomp /private/NfsMWRelease.dol

In hosted CI the V27 run uses the V26 BOOT_PROGRESS report as baseline
and passes --require-progress, --expected-entry 0x8000403C and
--expected-pc 0x805206BC. The only acceptable owner outcome is a genuine
stage=27 observed PC with report status advanced. An unknown output,
failed assertion, wrong stop or timeout must fail the job.

The initial V27 test is not a full OSInit or game startup. Original
__OSGetExecParams and subsequent original OS/IOS/hardware services remain
unexecuted through continuous startup, and no main, frontend, frame or
gameplay is claimed.
