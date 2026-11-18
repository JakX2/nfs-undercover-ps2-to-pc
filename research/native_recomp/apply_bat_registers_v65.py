#!/usr/bin/env python3
"""Original-free Broadway BAT register storage and ordered-write diagnostics.

The existing flat guest MMU remains in use. This patch records actual BAT
SPR values and ordering; it does not enforce BAT translation or permissions.
"""
import argparse
from pathlib import Path
CTX=Path("nWiiRuntime/include/runtime/cpu_context.h")
EMIT=Path("nWiiRecomp/src/recompiler.cpp")
OLD_C="  uint32_t hid4 = 0; // Wii HID4 guest-visible state"
NEW_C=OLD_C+"""
  std::array<uint32_t,32> bat_registers{};
  std::array<uint32_t,64> bat_write_sprs{},bat_write_values{};
  uint32_t bat_write_count=0;
  static constexpr unsigned bat_index(uint32_t spr) {
    return spr<=543u?spr-528u:16u+spr-560u;
  }
  uint32_t read_bat(uint32_t spr) const {
    return bat_registers.at(bat_index(spr));
  }
  void write_bat(uint32_t spr,uint32_t value) {
    bat_registers.at(bat_index(spr))=value;
    if(bat_write_count<bat_write_sprs.size()){
      bat_write_sprs[bat_write_count]=spr;
      bat_write_values[bat_write_count]=value;
    }
    ++bat_write_count;
  }"""
READ_OLD='''    } else if (spr == 920) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid2; // mfspr HID2\\n";'''
READ_NEW='''    } else if ((spr >= 528 && spr <= 543) || (spr >= 560 && spr <= 575)) {
      out << "    ctx.gpr[" << rD << "] = ctx.read_bat(" << spr << ");\\n";
'''+READ_OLD
WRITE_OLD='''    } else if (spr == 920) {
      out << "    ctx.hid2 = ctx.gpr[" << rS << "]; // mtspr HID2\\n";'''
WRITE_NEW='''    } else if ((spr >= 528 && spr <= 543) || (spr >= 560 && spr <= 575)) {
      out << "    ctx.write_bat(" << spr << ", ctx.gpr[" << rS << "]);\\n";
'''+WRITE_OLD
def apply(root):
    updates={};states=[]
    for relative,edits in ((CTX,((OLD_C,NEW_C),)),(EMIT,((READ_OLD,READ_NEW),(WRITE_OLD,WRITE_NEW)))):
        p=root/relative;c=p.read_text()
        for old,new in edits:
            if c.count(new)==1 and c.count(old)==1:states.append(True);continue
            if c.count(old)!=1 or new in c:raise ValueError("unknown BAT runtime/emitter revision")
            c=c.replace(old,new);states.append(False)
        updates[p]=c
    if any(states) and not all(states):raise ValueError("mixed BAT patch state")
    if all(states):return False
    for p,c in updates.items():p.write_text(c)
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("V65 BAT register diagnostics:",apply(a.root))
