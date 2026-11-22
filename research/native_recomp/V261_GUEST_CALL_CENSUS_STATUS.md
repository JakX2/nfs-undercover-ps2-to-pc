# V261: authenticated 64-call post-IPC guest loop census

Date: 2026-11-22. Branch: `research/wii-native-recomp-preflight`.
Owner-original and public-original-free CI:
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44966859266

## Owner-original result

All **16/16** independent SHA-verified original-game trials passed. V261
observes *exactly the same 64 genuine guest call entries* previously
verified in V260, without widening its execution frontier or changing
PowerPC CPU state, MMIO, IOS services, game code or IPC packet contents.

The raw PC/LR/guest-instruction-counter sequences remain owner-private.
The private analyzer emitted this aggregate, non-code signature:

```text
V261_CALL_CENSUS verified=1
V261_CENSUS trials=16 calls=64 stable=1 distinct=1 unique_pc=8 unique_pairs=10 repeated=54 new_second=0 match32=0 max_freq=19 monotonic=1 digest=df3bf8f6cf964f34 first_pc=8051b070 last_pc=805265d4 last_lr=8052f92c
PASS: 16 owner-original 64-call census trials
```

### Interpretation

- **8 distinct guest callee PCs** and **10 distinct (PC, LR) pairs**
  appear among 64 post-IPC guest function-call events; 54 are repeats.
- Among calls 33-64, **0 new PC/LR pairs** appear compared with calls
  1-32. A single callsite pair occurs **19 times**.
- **0 of 32** corresponding offset-32 call positions match; this is
  *not* a simple exact period-32 cycle.
- All 16 trials report one identical PC/LR sequence digest. The guest
  instruction count strictly increased between observed call entries.
- The final original call is still `PC=0x805265D4`,
  `LR=0x8052F92C`. This checkpoint did not submit a new PPCMSG.

The evidence strongly supports a repeated small-call-set path. It is
**not enough to prove** a deadlock or infinite loop. The call sequence
could include interrupt masking, scheduling, polling or other normal
repetition. Determine caller identity, call-chain cycle, and the
hardware/data condition before altering runtime behavior.

## Original-free work committed

- `derive_v261_guest_call_census_harness.py` uses the V260 exact
  observer seam and emits only bounded read-only PC/LR/instruction
  markers to the ephemeral private native log.
- `analyze_v261_postipc_calls.py` validates 16 complete 64-call
  sequences, their original V260 frontier and monotonic counters;
  reports aggregate uniqueness and fingerprint only.
- `derive_v261_guest_call_census_runner.py` and
  `run_v261_guest_call_census.sh` inherit original startup, 16 trial
  and V260 guards.
- `test_v261_guest_call_census.py` tests synthetic traces, malformed
  ordering and frontier rejects, unchanged native bus write count,
  source-only derivation, shell syntax and workflow privacy.
- `.github/workflows/wii-v261-guest-call-census.yml` uses pinned
  owner-original staging, isolated translation and deletion of raw
  original files, generated game source and private native logs.

The first V261 owner run failed only because a newly added reporter
looked for the V260 wrapper's summary line in the inner native log.
That check was corrected to count 16 true V260 frontier entries in
the native log. The authenticated follow-up run passed both jobs.

## Next root-cause tests

1. Quantify shorter-period callsite recurrence and the top repeated
   PC/LR pair in this same 64-event window without disclosing private
   translated instructions or raw memory bytes.
2. Examine whether the repeated calls represent real scheduler/IRQ
   progress or guest busy-wait and why no new PPCMSG has been reached.
3. Investigate the authentic SYSCONF request when the game's actual
   PowerPC code publishes it. Preserve the previous real -4 IOS
   failure rather than fabricating a successful open.

**Not achieved:** a completed NAND callback, the original game
`main`, full boot, first frame or playable Windows port.
