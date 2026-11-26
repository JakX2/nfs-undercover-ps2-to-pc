
# V1050: correct synthetic alarm epilogue return order

V1047's four early refusal cases passed, but valid and queue-corruption fixtures stopped at the final root BLR. The synthetic fixture restored LR before the restore-IRQ leaf return had been authenticated. Add a distinct caller resume instruction, then restore the original handler return LR before the root BLR. Adjust synthetic visit count to nine. No production witness change. Pending CI.
