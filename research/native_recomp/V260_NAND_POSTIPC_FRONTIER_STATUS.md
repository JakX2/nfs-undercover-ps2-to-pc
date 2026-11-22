# V260: original NAND callback continues through 64 native IPC-phase guest calls

Date: 2026-11-22. Development branch: `research/wii-native-recomp-preflight`.

**Owner-original + public CI green:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44965033144

## Verified authentic Wii execution

V259 established the restored NAND callback's original translated
IPC helper entry `PC=0x8051906C`, `LR=0x805192EC`.
V260 proceeds through the original Wii guest instruction stream instead
of stopping at that entry. Its candidate-only instrumentation retains
the existing V258 32-call safety check for all other execution phases,
but uses a separate *bounded* 64-call observation window after this
authenticated V259 entry.

Both jobs passed. The private job executed the SHA-verified owner DOL
as NWiiRecomp-generated native C++ and independently verified **16/16**
trials, with these public, non-proprietary markers:

```text
V260_SC_POSTIPC_EVENT verified=1
V260_POSTIPC_RESULT kind=calls trials=16
V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=1 pc=805265d4 lr=8052f92c
PASS: 16 owner-original bounded NAND-to-IPC continuation checkpoints
```

The 64th observed original call entered `0x805265D4`, with guest LR
`0x8052F92C`. Original register/SDA, mapped SYSCONF status and
external interrupt coherence checks held. The original SYSCONF status
byte remained `1` at that exact checkpoint.

**V260 did not observe a new PPCMSG store** before the 64-call bound.
The test terminated at a real guest function entry instead. Therefore
no second IOS request, SYSCONF `IOS_Open` success, NAND callback
completion, native game `main`, frontend, or gameplay is claimed.

## Test design and privacy

- `derive_v260_ipc_ppcmsg_boundary_harness.py`: original IPC entry
  continuation, candidate-only post-entry call-window and read-only
  PPCMSG prewrite observer.
- `derive_v260_ipc_ppcmsg_boundary_runner.py`: exactly sixteen
  independent owner-original trials, mutually exclusive genuine
  PPCMSG-prewrite vs bounded-call outcomes, no synthesized success.
- `test_v260_ipc_ppcmsg_boundary.py`: original-free derivation,
  fail-closed anchors, source mutation checks, source and bash guards.
- `.github/workflows/wii-v260-ipc-ppcmsg-boundary.yml`: dedicated
  original-free and owner-private jobs with ephemeral code and
  original-file cleanup.

The temporary experimental workflows before the green run had
implementation/reporting errors: V258's inherited 32-call limit
prematurely stopped the new route, and a Python f-string regex
misformatted the first 64-call trace reporter. The final workflow
corrects both without tampering with game code, altering guest packet
bytes, faking an IOS response, or suppressing legacy test coverage.

No retail DOL/ELF, translated game source, original packet bytes,
assets, or private execution logs were committed publicly.

## Next actions

1. Analyze the original 64-call window by bounded unique callsite
   and call/return counts, instead of increasing a safety budget blindly.
2. Establish whether the later `0x805265D4` call from
   `0x8052F92C` belongs to a scheduler/reentry loop or a
   legitimately advancing NAND setup phase. Cross-check native
   callbacks and available reference traces.
3. Follow the authentic PowerPC execution to the next actual
   `PPCMSG` MMIO write and compare the physical MEM2 IOS request
   with the earlier, invalid second `/shared2/sys/SYSCONF`
   `IOS_Open` header and the successful first Open.
4. Repair root-cause memory/cache/IPC behavior where verified,
   preserving the original negative `-4` IOS result until a genuine
   correct request is submitted.

The original `main` and any first frame remain unverified. The
existing hourly Undercover development automation remains unchanged.
