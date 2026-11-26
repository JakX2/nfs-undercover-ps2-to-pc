# V1149: held third-token scheduler and pending exception join

Reuse the proven LiveEpilogueWitness and ThirdPendingReentry, requiring exact controller, PI cause/mask atomics, CPU tick, captured exception frame and completed native handler return. The original scheduler, context restore and RFI remain guest code. Only the existing native external-entry routine admits the asserted third token. The new component accounts for the outer poll and vector dispatch tick; it is not installed in the full image yet. Add eight positive and twelve negative original-free cases. CI pending.
