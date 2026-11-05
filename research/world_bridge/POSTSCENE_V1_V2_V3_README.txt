NFS Undercover -> Carbon PC | Post-scene fields, V3 research kit
==============================================================

NEW IN V3
  carbon_pc_postscene_lane_controls.py
  test_carbon_pc_postscene_lane_controls.py
  CARBON_PC_POSTSCENE_BYTE_LANE_AND_STRICT_THREE_SECTION_GATE.md

INCLUDED FROM V1/V2
  carbon_pc_postscene_dependency_probe.py
  carbon_pc_postscene_cross_section_gate.py
  test_carbon_pc_postscene_dependency_probe.py
  test_carbon_pc_postscene_cross_section_gate.py
  CARBON_PC_POSTSCENE_DEPENDENCY_FIELD_GATE.md
  CARBON_PC_POSTSCENE_CROSS_SECTION_SPECIFICITY_GATE.md

RUN (in a directory alongside existing draft PR #33 world-bridge modules):
  python -m unittest discover -p "test_carbon_pc_postscene*.py" -v
  python carbon_pc_postscene_lane_controls.py --carbon-bun PATH --carbon-stream PATH --sections 141 142

55 tests from V1/V2 + 43 V3 tests = 98/98 synthetic tests passed.
Original Carbon PC 141/142 binaries were NOT run in this session. This package
contains no retail assets, proprietary resource bytes, game-file writer,
or playable patch. Not proof of post-scene function or pointer semantics.

Next: obtain a *third* independently validated same-envelope Carbon PC control.
