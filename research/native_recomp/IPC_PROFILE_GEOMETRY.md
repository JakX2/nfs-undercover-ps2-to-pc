# Private IPC profile geometry preflight

The previous owner run 45848283031 proved the ring's three native stores and the subsequent helper entry, eight times. The independent profiling memory witness passed 136 synthetic cases in run 45848705833. The next preflight derives the helper from the existing submit call edge and checks exact original DOL/ELF code agreement, reachable bounded leaf control flow, and four uniquely named writable objects. Both original input hashes are verified. No private addresses, words or data are printed, and nothing in this preflight executes or authorizes guest instructions.

The four-object layout and four-store leaf shape are hypotheses until the owner run succeeds. The test corpus is synthetic. A successful preflight is necessary but not sufficient for native integration: runtime effective addresses, values, request integrity, ABI and return edge still need validation.

## Verified results

- Run 45849414950: private geometry authenticated four objects, 32 slots, 32 reachable labels, four stores (two indexed), two return sites and one backward branch. The first refusal was resolved by admitting only CTR setup and non-linking conditional LR returns; no wider writable range was introduced.
- Run 45849598881: 42 source-only instruction/control/ABI witness cases passed with ASan/UBSan.
- Run 45849960908: original native helper return passed 8/8. Each trial visited 41 original instructions, made four observed profiling stores, and passed two polls. All selected a real free profiling slot. Ring, request, masked interrupt state and ABI were preserved; no interpreter fallback or new IOS service occurred.
- Synthetic hook installer testing exposed a duplicate bare continuation-label acceptance. The initial repair had a source serialization error; 3d41093 corrected it. Source run 45850333859 passed the installer regressions and sanitizer tests. Owner run 45850333961 repeated the original native result 8/8 after that correction.

The focused original instruction frontier stops at the real caller continuation before its next instruction. The complete original image has not booted. The device's service count remains four (two earlier Opens); the async event request has not been submitted to IOS.
