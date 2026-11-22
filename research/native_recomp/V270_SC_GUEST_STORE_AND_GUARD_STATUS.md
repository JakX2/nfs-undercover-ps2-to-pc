# V269–V270: actual guest SYSCONF writes and guarded state transitions

Date: 2026-11-22. Branch: `research/wii-native-recomp-preflight`.

## V269: authenticated native guest write watcher

Owner-original run:
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972869334

The V269 owner job passed **16/16 original Wii DOL trials** through
the same original native V260/V263 64-call frontier. The observer
arms the pinned NWiiRecomp `MMU::write8` host-side
`g_watch_addr` / `watch_hit` hook only after the genuine
V259 IPC helper reentry. It filters the precise physical
`r13-3176` SYSCONF byte, not adjacent bytes sharing its word.
The hook observes byte stores **before** the MMU commits them.

```text
V269_SC_WATCH verified=1
V269_SC_WATCH trials=16 frontier=64 stable=1 distinct=1 events=0 min_trial=0 max_trial=0 changed=0 write_zero=0 write_one=0 write_other=0 one_to_one=0 one_to_zero=0
V263_HOTSPOT trials=16 calls=64 stable=1 unique_pc=8 unique_pairs=10 max_freq=19 restore_hits=20 disable_hits=20 total_guest_inst=887 irq_ever=0 request_ever=0 sc_stable=1
V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=1 pc=805265d4 lr=8052f92c
PASS: 16 owner-original SYSCONF pre-store observation trials
```

**Zero actual guest byte-store events occurred** in the 64-call
observation window, although V268 found 11 statically existing
status-byte stores and two inside the repeatedly-called helper
`0x8052F830`. The original SYSCONF status remained `1`.
No extra guest function calls or fake IOS/IRQ events were introduced.
This proves absence of writes **within the bounded window only**,
not that the game can never complete its pending operation.

An initial V269 synthetic negative test expected `wrong_trials`
on a truncated final window; the correctly fail-closed parser
reported `incomplete_window`. The assertion was corrected and
the V269 public-original-free job passed in the subsequent run:
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972910641
The latter owner-native rerun should be checked independently before
claiming it completed.

## V270: original Wii helper write-site conditions

Both public-original-free and SHA-pinned owner-original jobs passed:
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44973182951

```text
V270_GUARD_AUDIT verified=1
V270_SC_SITES reads=1 writes=2 read_offset=28 store1_offset=44 store2_offset=240
V270_SC_STORE rank=1 offset=44 rs=0 prev_kind=1 prev_const=1 skip_cond=1 skip_direct=0
V270_SC_STORE rank=2 offset=240 rs=29 prev_kind=1 prev_const=0 skip_cond=1 skip_direct=0
```

The authentic 71-instruction helper at `0x8052F830` reads
`r13-3176` at offset `+0x1C`. It also contains **two direct,
static status byte stores**, each preceded by an original
`li`-form setting the *stored source register*:

- `+0x2C`: source `r0`, constant **1** (in-progress marker)
- `+0xF0`: source `r29`, constant **0** (cleared marker)

At least one static conditional forward branch can skip **each**
store. This establishes only possible branch guards and intended
stored constants, **not** that either store executes on the observed
native path. The original V269 memory watch verifies they do not
produce any write during the bounded 64-call sample.

## Combined original-game interpretation

V265/V266 proved the caller at `0x8052096C` executes the
original helper and retries while the helper's `r3` return
value compares equal to **1**. V267 proved that helper directly
reads SYSCONF status; V268 mapped six original functions that can
directly write the byte. V269 sees **no** store in the native retry
window. V270 confirms the helper's own direct write paths for
`1` and `0` exist but are conditional.

The remaining blocked startup path appears to require some authentic
completion condition or callback that makes the SYSCONF state
leave `1`. We still need to determine what activates it. The
observed IOS pending request and reply queue were empty; no IRQ
was asserted. Do not manufacture a successful SYSCONF descriptor,
return result or fake guest status update.

## Concrete next engineering gates

1. Audit the control conditions around the original helper's
   status-to-`0` store and determine which original callback or
   service can make that condition true, using only authenticated
   ELF/owner-native traces.
2. Correlate the six verified SYSCONF writer functions with the
   restored first NAND/ISFS callback chain, with attention to
   `0x8051906C`, original IPC request construction, and the
   missing *second* request in V259/V260.
3. When a concrete host runtime mismatch is verified, implement a
   minimal Wii IOS/IPC/memory/scheduler correction, add original-free
   regression tests, and verify owner-original native execution
   progresses beyond 64 genuine calls without forced guest PC,
   CR, r3, memory or a synthesized reply.
4. Continue to the original `main`, first rendered frame,
   frontend, world and gameplay only after authentic startup
   dependencies are supported.

**Not achieved:** successful second SYSCONF IOS_Open,
completed Wii boot, native game main, first frame or playable game.
The existing hourly Undercover task has not been duplicated.
