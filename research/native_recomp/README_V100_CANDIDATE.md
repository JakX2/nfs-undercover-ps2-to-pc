# V100 verified: original SC status function and chosen branch

Original metadata verified SCReloadConfFileAsync at 0x8052F94C and
its callback entry 0x8051DFF4. Restore original helper at
0x8051DFF4 and original status getter 0x8051E5A4, execute both
through NWiiRecomp and stop at the real selected next boundary
(0x8051DD50 or 0x8051E5BC). Validate caller ABI, committed SC
state, original thread, and pending IOS/STM services. No artificial
branch overrides or forced success return. V101 will handle chosen
SC configuration processing without inventing a config-file reply.

Owner-original run 44394631433 on e7488b9b6e01344889cdd51d6a87afc1d3a2a265 verified 16/16 SC callback entry, original status getter, branch choice 1 (0x8051DD50), inherited STM/FS service, and native thread state. The subsequent 0x8051DD50 body was not yet executed by V100.
