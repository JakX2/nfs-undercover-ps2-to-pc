# V712: one SI control-bit contract for backend and diagnostics

V711 review found the duplicate literal could classify reserved COMCSR bits 24/25 incorrectly. Expose the existing backend's exact ControlWriteBits constexpr, reuse it in the diagnostic, and test all 32 single-bit writes against the actual fresh controller's accepted/rejected result. Device behavior unchanged. No transfer authorization added. CI pending.
