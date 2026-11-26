# V1225: bounded upstream launch failure diagnostic

Expose exit status and unique original-free audit checkpoint booleans, plus the exact SRAM refusal stage/count, only on failed launch. No raw guest memory, private addresses, instructions or log fragments are printed. The strict terminal audit still decides success. Fix missing Path import in the profile launch regression. CI pending.
