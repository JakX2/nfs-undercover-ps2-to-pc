# V272–V277: original Wii SYSCONF writer provenance and caller chain

Date: 2026-11-22. Branch `research/wii-native-recomp-preflight`.
Original game DOL and ELF, translated code and raw traces remain owner-private.

## Scope and baseline

V265–V271 established that original function `0x8052F830` reads
the SYSCONF state byte at `r13-3176`; its caller at
`0x8052096C` retries while the function returns `1`. The helper
requires a direct status read of `3` to enter the guarded path that
contains status stores `1` and `0`. V269's authenticated
16-trial native observation saw **zero status byte stores**
during the post-IPC 64-guest-call window, with status remaining
`1` and no new IOS request or external IRQ.

The following V272–V277 owner-original ELF audits are **static**
and must not be mistaken for dynamic execution evidence or a boot.

## V272: constant sources of status stores

[Verified V272 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44973523062)

```text
V272_SC_WRITERS stores=11 owner_count=6 const0=1 const1=1 const2=1 const3=0 const_other=0 unknown=8 helper_stores=2 helper_one=1 helper_zero=1
```

Only three of 11 direct `r13-3176` byte stores receive an
immediately preceding `li` instruction. None of those three
sets literal `3`. Eight stores require source-register provenance.

## V273: conservative local source propagation

[Verified corrected V273 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974076247)

```text
V273_SC_PROVENANCE owners=6 stores=11 c0=1 c1=4 c2=1 c3=0 cother=0 status=0 load=4 unknown=1
```

A bounded straight-line PPC register-source analyzer recognizes
`li`, `addi`, `mr`, `ori` and direct loads, but stops at
branches and unsupported writes. The four memory-derived stores
belong to `0x80530BA0` (2) and `0x80530DBC` (2). The
unresolved store is in `0x8052FCA4`. Absence of a statically
proven literal 3 is **not** evidence status 3 is impossible.

The first V273 source-only test wrongly treated a comparison as
an unsupported GPR write. The corrected unsupported-register fixture
and owner-original run are both green.

## V274: exact loaded field geometry

[Verified V274 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974196936)

The four source loads are all `lwz` from pointer base +392
(`0x188`), immediately followed by `stb` to the status byte:

```text
V274_INPUT owner=80530ba0 store_offset=236 kind=load width=word base=pointer disp=392 source_offset=232 copies=0
V274_INPUT owner=80530ba0 store_offset=452 kind=load width=word base=pointer disp=392 source_offset=448 copies=0
V274_INPUT owner=80530dbc store_offset=640 kind=load width=word base=pointer disp=392 source_offset=636 copies=0
V274_INPUT owner=80530dbc store_offset=796 kind=load width=word base=pointer disp=392 source_offset=792 copies=0
```

The 32-bit loaded value is truncated to a byte by the status store.
These are **static load-to-store edges**, not proof the code executes
or that `+0x188` is the same object across separate functions.

## V275/V276: reject false same-object inference

[Verified V275 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974321613)
and [verified corrected V276 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974511580).

```text
V275_SC_FIELD links=4 sections=3 loads=69 word_writes=65 byte_writes=7 half_writes=0 owner_writers=58 near_writer_owners=2 unmapped=0
V275_FIELD_INPUT owner=80530ba0 store_offset=236 load_offset=232 base_reg=29 value_reg=0
V275_FIELD_INPUT owner=80530ba0 store_offset=452 load_offset=448 base_reg=29 value_reg=0
V275_FIELD_INPUT owner=80530dbc store_offset=640 load_offset=636 base_reg=30 value_reg=0
V275_FIELD_INPUT owner=80530dbc store_offset=796 load_offset=792 base_reg=30 value_reg=0
V276_FIELD_AUDIT_SUMMARY owners=2 loads=4 stores=3
V276_LOCAL_WRITE owner=80530ba0 offset=112 width=word base_reg=28 same_base=0 source_reg=4 source=byte0
V276_LOCAL_WRITE owner=80530ba0 offset=328 width=word base_reg=5 same_base=0 source_reg=3 source=byte2
V276_LOCAL_WRITE owner=80530dbc offset=664 width=word base_reg=5 same_base=0 source_reg=3 source=byte2
```

The three local stores at +392 do **not** use the same
PowerPC base registers as the four status-source loads
(`r29` and `r30`). Other pointer aliases could exist,
but a matching displacement alone is insufficient to infer one.
The V276 owner job passed immediately; its initial synthetic test
used a 14-instruction function where the analyzer required 16.
That test fixture was corrected and rerun successfully.

## V277: direct original PowerPC writer callgraph

[Verified V277 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974601819)

```text
V277_SC_CALLS targets=6 direct_calls=28 caller_pairs=27 writer_to_writer=1 unmapped=0
V277_SC_TARGET target=8052f790 calls=4 callers=4
V277_SC_TARGET target=8052f830 calls=12 callers=12
V277_SC_TARGET target=8052f94c calls=1 callers=1
V277_SC_TARGET target=8052fca4 calls=4 callers=3
V277_SC_TARGET target=80530ba0 calls=7 callers=7
V277_SC_TARGET target=80530dbc calls=0 callers=0
V277_SC_CALLER target=8052fca4 rank=2 owner=8052fa60 calls=1
```

The original NAND child function `0x8052FA60`, which
V250/V259 already reached natively, contains a **direct linked
call to `0x8052FCA4`**, the remaining status-byte writer whose
source could not be inferred across a branch in V273.
A static direct call is not proof the branch executes on the
restored NAND callback path. `0x80530DBC` has no direct
`bl` callers in the ELF scan; indirect callbacks and dynamic
dispatch are not covered.

## Current best next gate: V278 original guest execution

V278 adds a candidate-only, bounded read-only guest-entry
observer for `0x8052FCA4`, before and after the authentic V259
IPC helper reentry, and retains V269's MMU pre-store watch.
It will report whether the original status writer is **actually**
entered during each of 16 authenticated NAND callback trials.
The guest PC, LR, registers, memory, timebase, IRQ, IOS packet
and callback scheduler are left unchanged.

Proceed only from observed original execution evidence:
if the writer is entered, classify its authentic callback return
and source value; if it is not, inspect the original callsite
condition and pending asynchronous event. No synthetic success
descriptor or forced status transition is acceptable.

**Still unverified:** second SYSCONF IOS request, complete OS
startup, original `main`, first rendered frame, frontend and
playable gameplay.

The existing hourly Undercover development automation remains
in place, with no duplicate scheduled tasks.
