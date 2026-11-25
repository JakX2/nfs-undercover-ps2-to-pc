# V694: generated native three-helper control

Extend the verified V692 independent PPC test with an actual nested direct call and real guest LR save/restore around the call. Execute three independent ACK locations (nested helper, resumed second helper, resumed handler) and a deeper-call refusal, in split and non-split compilation with actual MMU writes. Uses production V693 label hooks and checks the ordered native return/ACK transcript. This independent program is not derived from the original game. CI pending.
