# V1322: cooperative RFI emitter semantics

Pinned NWiiRecomp emitter invokes the inline RFI callback only if EE transitions 0->1. The V1315 cooperative save has EE=0 (required by the save witness). Its restore therefore reaches only the outer dispatcher callback. Likewise an mtmsr retaining EE=0 does not poll. Correct the V1317 synthetic contract, reject duplicate post-RFI callbacks, keep exact tick and restored register checks. IRQ RFI witnesses remain unchanged. No original loader execution claimed.
