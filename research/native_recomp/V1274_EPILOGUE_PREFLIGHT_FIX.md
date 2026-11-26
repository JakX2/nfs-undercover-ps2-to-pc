# V1274: correct joined epilogue planner preflight

V1273 source regression passed all 37 reply-dispatch/handler entry checks in run 45797010456. The V1270 planner failed import in run 45796422843 due to an omitted concatenation operator in private header rendering. Correct the renderer, name the dispatcher geometry fields (guard set is index 7, not the original dispatcher word at index 6), add deterministic header/ownership coverage and fixed refusal categories. Trigger the corrected V1271 owner workflow only after source checks. Original RFI and second-vector execution remain unverified.
