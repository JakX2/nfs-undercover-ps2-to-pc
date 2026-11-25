# V722: focused original scheduler-enable and no-switch reschedule

V720 owner run 45542554175 verified all 54 original OSLoadContext instructions, seven GQR restores, the native RFI and independently authored resume program in 16 varied trials (8 each split/non-split); two altered saved GPR trials refused. V722 tests the remaining scheduler-enable and reschedule dependencies of the original interrupt dispatcher. It authenticates original ELF/DOL extents and direct calls into original interrupt-control leaves, derives counter/hint SDA offsets privately, and composes a separately authored caller. The valid lane starts with nonzero scheduler nesting and zero run-queue hint, verifies original return/counter/ABI behavior and refuses interpreter/MMIO fallback. A nonzero hint must reach an explicit synthetic guard at the original switch-target boundary; no original thread switch is claimed. Geometry and the OS SDK return-value expectation remain hypotheses until owner CI validates them. The actual original SI handler return is still a separate full-image gate.

## V723 geometry correction

V722 owner run 45542876081 passed the context-loader regression but rejected scheduler geometry before code generation (`unexpected_control`). Admit only CR-tested, non-linking LR returns in the reschedule leaf, with no reserved bits or branch hint field. Add synthetic positive and negative controls; if the original still fails, report only the control class, not instructions or addresses. Native scheduler execution is not yet verified.

## V724: isolate external tail ownership

V723 owner run 45543142512 authenticated scheduler geometry but failed generated-source auditing. The upstream analyzer can absorb a nearby unconditional tail target into its caller even when that target is a separate root. V724 fences all six scratch fixture roots by exact authenticated spans, and audits statically reachable labels rather than demanding alignment/dead words after terminal branches. Adds bounded diagnostic categories and synthetic reachability/ownership tests. No change to complete-image analysis. Owner execution remains pending.
