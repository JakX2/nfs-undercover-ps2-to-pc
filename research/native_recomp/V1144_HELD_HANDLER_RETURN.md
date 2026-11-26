# V1144: held original handler ABI return witness

Capture the native handler's incoming ABI before its prologue, bind it to the same saved exception frame, and join the verified V1138 terminal call without charging another tick. Reuse NativeReturnWitness<15> to authenticate all compiler restore loads, stack unwind, LR, poll and outer dispatch while the third SI token stays asserted. The V1144 API is not enabled in the full image. Add 20 independent original-free synthetic cases covering 8 positive and 12 refusal controls. Verification pending.
