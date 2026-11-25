# V948: continuous second-vector gate

V932 continuous owner run 45711850472, job 139548221079, completed successfully. Full image linked on Linux x64, original startup entered first external SI exception, executed the original handler and returned through scheduler and context loader. Original RFI restored all integer fields and immediately took the genuine pending second external exception, without executing the interrupted startup instruction or changing the held SI source. 86 scheduler/loader visits. This is now the latest verified continuous frontier.

V943 focused owner run 45713942831 confirms second original vector and original trampoline, strict branch and poll path, all 38 saved fields, 16/16 valid cases and 10 invalid-state refusals. The second dispatcher is a synthetic stop in that fixture.

V948 runs the complete translated image with V939 enabled and requires full preflight, link, and the strict ordered second-vector/trampoline execution census in one run. No extra IRQ acknowledgement, no hidden skip, no resumed game instruction or second dispatcher instruction claimed. Existing two V939 preparation runs remain separate and are not canceled. Private owner inputs and generated code remain out of tracked source.
