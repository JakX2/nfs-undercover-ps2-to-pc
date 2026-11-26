"""Explicit, bounded public output for second interrupt CLI auditors.
Validation remains in each caller's inspect function; output is not proof.
"""
import re
import audit_v922_irq_return as irq
import audit_v932_pending_rfi as pending
import audit_v939_second_vector as vector
import audit_v951_second_dispatch as dispatcher

EXACT=(dispatcher.BEGIN,*dispatcher.EDGES,vector.TRAMP,
       pending.SOURCE,pending.RFI,pending.POLL,*irq.STAGES)
PATTERNS=(dispatcher.RESULT,dispatcher.FAULT,vector.RESULT,vector.FAULT,
          pending.RESULT,pending.DIAG,irq.FAULT)

def public_line(line,exact=(),patterns=()):
    return line in EXACT or line in exact or any(
        re.fullmatch(p,line) for p in (*PATTERNS,*patterns))
