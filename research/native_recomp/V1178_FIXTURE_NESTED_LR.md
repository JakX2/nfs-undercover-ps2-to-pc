# V1178: nested LR restore fixture correction

V1175 live positive fixture was rejected at the native return ABI witness. The synthetic sequence restored the outer LR before the inner return label, which is incompatible with the original call witness. Model the original order with one explicit synthetic LR-restore instruction at each nested return, then BLR. Synthetic visit census increases from 13 to 15; original owner census remains 130. No runtime ABI checks changed. CI pending.
