# V929: original OSInit post-IRQ-enable frontier census

Authenticate OSInit's complete DOL/ELF body and the V616 interrupt-enable return. Classify bounded reachable original instructions from that return to the first linked boundary, including alternate branches, stores, loads, and whether the original V264 retry helper is the first boundary. No original instruction bytes or PCs are emitted. The analysis is static only and cannot certify execution. V927 focused original resume/BLR has meanwhile passed 16 valid cases and four refusals in owner run 45607942180. V928 private preflight pending.
