# V100 candidate: original SC status function and chosen branch

Original metadata verified SCReloadConfFileAsync at 0x8052F94C and
its callback entry 0x8051DFF4. Restore original helper at
0x8051DFF4 and original status getter 0x8051E5A4, execute both
through NWiiRecomp and stop at the real selected next boundary
(0x8051DD50 or 0x8051E5BC). Validate caller ABI, committed SC
state, original thread, and pending IOS/STM services. No artificial
branch overrides or forced success return. V101 will handle chosen
SC configuration processing without inventing a config-file reply.
