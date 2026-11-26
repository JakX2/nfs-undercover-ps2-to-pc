# V1226: single corrected continuous retry

V1196 owner run 45773050058 linked 411/411 but failed after launch without bounded earlier markers. V1224 fixes a demonstrable cold SRAM profile mismatch; V1225 adds bounded failure diagnosis. Gate the existing owner workflow on both exact-profile DMA tests, retain the original callback-return success criteria, and rerun once. No duplicate full builds, no private artifacts uploaded. This does not yet demonstrate original callback return or boot.
