# V1407 native asynchronous request-header flush

V1406 owner run 45843920121 verified eight original asynchronous submit paths, all skipping the synchronous queue initializer, 16 instructions and six stores per trial. No request writes occurred during that prefix. V1405 source contract run 45843213172 passed the cache/return and construction tests.

V1407 adds a distinct opt-in owner mode, preserving all prior stops. It reuses the full submit-body word audit and previously installed return trace, the third-caller masked cache observer, and a fresh exact allocation-byte shadow. The original submit return is the stop, before executing the return-site instruction. Both STM descriptors and four prior IOS service steps must remain unchanged. No request enqueue or event registration is claimed. Owner validation pending.

The new workflow gates on the successful V1406 owner run; original files and generated code stay in the private runner. Logs contain only bounded counts and result flags.
