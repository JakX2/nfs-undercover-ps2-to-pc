# V1296: verify native MMIO instruction completion

V1295 source verification passed; its owner run 45809594649 was queued at implementation time. V1244 full-image run 45807527343 passed prerequisites and entered private execution. Neither original execution frontier is claimed to have advanced.

Require a native callback for every decoded word accessing an IPC aperture, and verify load destination/update-base results at the next native instruction boundary. New sanitized categories 9 (missing callback), 10 (incorrect architectural result). Ordinary RAM accesses unchanged. No host register writes or additional IOS steps. Four joined regression cases plus 14 standalone cases passed locally for the standalone test under strict warnings, ASan and UBSan; joined CI pending. Existing owner retry left intact.
