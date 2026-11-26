# V1329: fix cooperative audit resume address shape

V1328 owner run 45816761132 passed its prerequisites, rebuilt the 48-root private fixture and translated it, then failed in the post-translation audit before native compile. `prepare_v1307_cooperative_fixture.plan` returns the enable resume PC as a scalar integer, but two audit callers indexed it as a tuple. Use the scalar in both checks, add a source regression exercising the actual audit interface, and fail closed on unexpected type errors. Retry the same owner lane. No new original instruction execution claimed.
