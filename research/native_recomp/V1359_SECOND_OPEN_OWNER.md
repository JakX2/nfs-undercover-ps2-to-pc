# V1359 original second STM Open entry

V1358 owner job 139926469367 passed all eight original synchronous submit/Open returns and verified descriptor 0. Continue through the ten original STM corridor instructions authenticated by V1337, with exact native labels, direct second call and dispatcher resume. Require the original successful descriptor store (SDA word, value 0), opposite authenticated STM path, mode 0, same selected thread and transport snapshot, unchanged allocator heap and metadata, and exact original second call LR. Stop before executing the second Open, not before its caller. The SDA store form/count is a strict hypothesis to be checked by the owner run; alternate error exit may not execute. Prior lane remains unchanged. No full boot claim.

## V1360 integration correction

V1359 owner run 45826468215/job 139932055211 passed all ten native labels, direct second call and existing resume case; its integrated C++ compile failed because the new local `second` conflicted with the existing second IRQ dispatcher witness in the same trial scope. Rename only the STM witness and its reference. All second-entry predicates remain unchanged. V1359 source-only cases passed 9/9; no owner second-entry execution was established by that run.
