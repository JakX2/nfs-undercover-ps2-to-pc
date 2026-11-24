# V567: native SC overlay memory geometry

The pinned NWiiRecomp loader represents BSS as a nonzero declared section size with empty backing data. V561 used backing byte length alone to detect low-memory collisions. V567 checks declared half-open ranges including BSS, rejects address overflow, contradictory section metadata, partial source overlap and ambiguous source mappings, while allowing adjacent and empty sections. Existing branch and final RFI checks are unchanged. Rejected overlays leave every section untouched.

Local GCC C++20 ASan/UBSan test with a minimal matching loader declaration: one valid overlay, 15 rejected cases, no sanitizer findings. The same test is integrated into the existing V561 workflow against the actual pinned upstream header. The latter and full native SC execution remain subject to CI. This does not establish original startup progress.
