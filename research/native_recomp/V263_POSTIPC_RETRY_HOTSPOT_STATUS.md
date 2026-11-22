# V263: original Wii post-IPC retry hot path identified

Date: 2026-11-22. Branch `research/wii-native-recomp-preflight`.

**Green original-game plus public original-free CI:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44969123404

## Verified 16-trial native result

V263 reuses V262's original PowerPC execution fixture and 64 guest-call
limit; it does not add guest instructions, modify CPU registers or host
memory, publish a new IPC message, or synthesize an IOS result.
All 16 owner-original trials completed with the same callsite and
IRQ observations:

```text
V263_HOTSPOT verified=1
V263_HOTSPOT trials=16 calls=64 stable=1 unique_pc=8 unique_pairs=10 max_freq=19 restore_hits=20 disable_hits=20 total_guest_inst=887 irq_ever=0 request_ever=0 sc_stable=1
V263_PAIR rank=1 pc=805265ac lr=8052f84c freq=19 first=9 last=63 first32=8 last32=11 ee_on=19 ee_off=0 gap_min=32 gap_med=32 gap_max=32
V263_PAIR rank=2 pc=805265d4 lr=8052f92c freq=19 first=10 last=64 first32=8 last32=11 ee_on=0 ee_off=19 gap_min=32 gap_med=32 gap_max=32
V263_PAIR rank=3 pc=8052f830 lr=80520970 freq=19 first=8 last=62 first32=9 last32=10 ee_on=19 ee_off=0 gap_min=32 gap_med=32 gap_max=32
PASS: V263 owner original callsite recurrence classified for 16 trials
```

Earlier Wii startup verification associates original PowerPC
`0x805265AC` with `OSDisableInterrupts` and `0x805265D4`
with `OSRestoreInterrupts`. Original `0x8052F830` is called
from the return site `0x80520970`. These three exact caller/callee
pairs recur every **32 guest instructions**, 19 times each in the
sampled post-NAND window. The three pairs account for 57 of 64 observed
calls; the other helper callsites occur during entry to this window.

The original-game timebase implementation in pinned NWiiRecomp
(`nWiiRuntime/include/runtime/cpu_context.h`) returns
`CPUContext.inst_count` by default; optional `NWII_WALLTB=1`
uses host monotonic time. The original PowerPC `mftb/mftbu` AOT
emission reads this source. In this native window, 887 guest
instructions elapse overall. A time-sensitive retry or polling loop
is a strong hypothesis, but the actual comparison operand, exit
condition and duration have **not** been verified.

V262 already established that external IRQ was never asserted,
no native IOS request was pending and the reply queue stayed empty
during the same 64-entry window. Thus the 32-instruction recurrence
must not be mistaken for a successful second IOS submission,
SYSCONF completion, full native boot, frontend or gameplay.

## Implementation and test design

- `analyze_v263_hotspot.py` correlates the 16 complete private
  V261/V262 original guest traces and computes recurrent PC/LR
  pair frequencies, sample positions, `MSR.EE` correlation and
  guest instruction-count deltas without exporting original code,
  memory or unredacted traces.
- `derive_v263_hotspot_runner.py` invokes the already-authenticated
  V262 generated runner in a **separate Python process** before
  appending the aggregate-only analyzer. This fixes the accumulated
  recursive Python import-chain limit without increasing global
  recursion limits or changing native game execution.
- `test_v263_hotspot.py` covers synthetic recurrence and
  malformed/unstable sequence detection, original-free runner
  generation, privacy constraints and shell syntax.
- `.github/workflows/wii-v263-hotspot.yml` uses 16 SHA-verified
  owner-original trials, original-free regression, ephemeral
  private files and no proprietary artifact upload.

The initial V263 source-only workflow hit Python's historical
import-depth ceiling, though the owner-original job already passed.
After the independent V262 generator boundary was implemented,
**both** V263 CI jobs passed.

## Next implementation/research gate

1. Inspect the authentic guest branch/control-flow around caller
   `0x8052096C` / return `0x80520970` and callee
   `0x8052F830`, preserving proprietary instruction data only
   in private owner execution.
2. Verify whether the loop is waiting for a timebase deadline,
   a thread flag, a scheduled callback, or another original OS
   condition. The 32-tick spacing by itself does not prove this.
3. Test authentic timebase and callback progression before
   altering runtime behavior. Keep failure diagnostics bounded
   and preserve the original invalid SYSCONF request behavior
   until its actual owner-game request path is reached.

No genuine `main`, first frame or playable PC build was
achieved by V263. The existing hourly task remains unchanged.
