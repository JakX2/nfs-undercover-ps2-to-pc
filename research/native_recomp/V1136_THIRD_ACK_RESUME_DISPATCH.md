# V1136: third ACK RFI native dispatch boundary

Extend V1130's two post-RFI polls through the generated outer dispatch tick and first translated resume label, sharing the existing V1007 native epilogue witness. The resume target is a synthetic fixture, not original startup code. Stop before its instruction. Require restored integer/GQR state, matching CPU, exact resume PC and word, and unchanged third-token device ownership. Add 20 synthetic cases and require one ordered terminal marker in the existing 32 private lanes. No full-image route enabled. CI verification pending.
