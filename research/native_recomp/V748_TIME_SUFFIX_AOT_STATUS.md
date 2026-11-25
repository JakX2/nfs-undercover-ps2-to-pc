# V748: generated post-time continuation regression

A synthetic handler extends the verified V743 fixture with a conditional branch after the second system-time invocation. One path attempts a fourth linked call and must refuse before entering it; another bypasses the call and must complete the genuine native indirect handler return. Preserves all six older lanes and uses V747 production patches. Both generated modes require eight exact result sequences and zero interpreter fallback. Pending CI.
