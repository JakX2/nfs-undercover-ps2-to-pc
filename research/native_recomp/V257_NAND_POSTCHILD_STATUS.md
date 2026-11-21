# Wii native callback continuation: V256 and V257

Date: 2026-11-21. Branch: `research/wii-native-recomp-preflight`.

## Verified native-original checkpoints

- **V256** owner-original workflow [44955517454](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44955517454) passed its public and private jobs. The original translated NAND child entered at `0x8052FA60` and naturally returned to `0x8051E0B8`. The owner test verified the unchanged original CPU state, mapped SC small-data area, IOS reply state and coherent interrupt state across sixteen trials.
- **V257** owner-original job in [44956032722](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44956032722) passed sixteen trials of continued original NAND callback execution. Its first subsequent translated function entry was `pc=8051ad3c`, with `lr=804f0f68`, `guest=1`, `caller=1`, `code=1`, `mapped=1`, `reply=1`, `coherent=1` and `sc=1`. This is **function-entry proof**, not yet execution or return proof for `0x8051AD3C`.
- V257's first public run failed a **test-only** string check that misclassified `ctx.pc == addr` as an assignment. Commit `ec60cc578ead93a181253e9cbd42a79dd4576f28` corrected the assertion to distinguish assignment from equality. That corrected public V257 job passed in [44956089032](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44956089032).

## Execution boundaries

The optional `owner-callback` mode extends the existing owner-native V244 baseline without changing the original PowerPC executable, registers, saved contexts, RAM contents, branch decisions, or native IOS replies. V257 replaces V256's **test stop only** with a normal guest continuation, then stops at the next native PowerPC function entry. The standalone V256 checkpoint remains separately reproducible.

Source-only diagnostic and runner modules:

- `derive_v256_nand_child_return_harness.py`, `derive_v256_nand_child_return_runner.py`
- `derive_v257_nand_postchild_harness.py`, `derive_v257_nand_postchild_runner.py`
- `run_v257_nand_postchild.sh`, `test_v257_nand_postchild.py`
- `.github/workflows/wii-v257-nand-postchild.yml`

Proprietary owner game binaries and privately translated AOT functions remain in the ephemeral owner CI workspace and are deleted by its cleanup step.

## Remaining work

1. V258: execute the newly discovered original PowerPC callee at `0x8051AD3C`, monitoring its natural continuation or return to the caller at `0x804F0F68`. Use bounded, read-only instrumentation, native callbacks and complete original CPU context checks. Preserve all older baseline assertions in their own modes.
2. Diagnose any new runtime dependency (PPC translation, memory aliasing, Wii OS/IOS services or exception handling) from actual owner-native evidence rather than forcing a return or injecting a success value.
3. Resume the original SC initialization and second `/shared2/sys/SYSCONF` IPC request once guest execution reaches the request construction again. The verified negative IOS `-4` reply transport does **not** establish a successful SYSCONF open.
4. Only after additional original execution reaches game startup, frontend and gameplay may the milestone terminology be advanced. **No complete native boot or playable port is claimed here.**
