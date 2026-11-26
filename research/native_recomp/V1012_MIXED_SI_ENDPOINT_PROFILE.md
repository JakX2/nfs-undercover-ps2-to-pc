# V1012: controlled mixed SI endpoint experiment

The V1011 source and compiled second-ACK regressions passed (45732514719); full owner execution 45732514831 is independent and still running at implementation time. V991 stopped after second ACK at kind=12. Its launch profile sets every SI endpoint absent. V988/V1007 successful focused fixtures use explicit responding endpoints and seeded active transfer state; they do not establish which branch continuous startup takes.

V1012 holds port 0 absent (the V529 discovery witness requires its no-response completion) and sets only port 1 to the existing synthetic three-byte type response 090000. All other ports, latency, EXI profile, authenticated executable, launch mode and runtime guards remain unchanged. The actual original code must issue any transfer; no injected guest queue, forced callback, fabricated ACK or altered branch is allowed. The alternate profile is fixed, opt-in and restricted to the second-callback launch audit. The existing default file is byte-identical. Source-only tests verify exact profile bytes, exclusive creation, invalid inputs and launch gating.

A mixed-profile run is useful even if it refuses earlier: it is not a substitute for verifying the all-absent path. No continuous second RFI or boot is claimed.
