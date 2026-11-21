#!/usr/bin/env python3
"""Source-only V234 upstream ISFS async Open provenance tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v233_sc_second_open_abi_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v234_sc_isfs_origin_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v234_sc_isfs_origin_runner import derive as runner, ISFS, ROUTE, PATTERN
HERE=Path(__file__).resolve().parent
class V234(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_actual_source_abi_window_widened(self):
        for x in ("addr==0x804f1e2cu","v183_second_phys==0u",
                  "v234_isfs_count<8u","ctx.gpr[4]","ctx.gpr[5]",
                  "ctx.mmu.get_ptr(v234_p+i)","V234_ISFS",
                  "V234_ROUTE"):
            self.assertIn(x,TRACE)
        for x in ("read32(value+16u)","v233_ios_mode",
                  "v234_isfs_mode","V234_SOURCE","++v234_source_seen"):
            self.assertIn(x,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertNotIn(PREVIOUS_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("broken fixture")
    def test_no_write_or_guest_abi_forgery(self):
        for needle in ("scheduler.service_one(","ipc70_ram.write8(",
                       "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for token in (TRACE,SEND):
            for bad in ("ctx.gpr[3]=","ctx.gpr[4]=","ctx.mmu.write",
                        "ipc70_ram.write","ipc70_bus.write",
                        "<<v234_isfs_mode","<<v234_p"):
                self.assertNotIn(bad,token)
    def test_bounded_owner_runner_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for x in ("derive_v234_sc_isfs_origin_harness.py",
                  "V233_SC_SECOND_OPEN_ABI verified=1",
                  "V234_SC_ISFS_ORIGIN verified=1"):
            self.assertIn(x,script)
        self.assertIsNotNone(re.fullmatch(ISFS,
            "V234_ISFS seq=1 path=1 sysconf=1 modevalid=1 nand_cb=1 guest=1"))
        self.assertIsNotNone(re.fullmatch(ROUTE,
            "V234_ROUTE isfs=1 mode_same=0 isfs_modevalid=1 ios_modevalid=0 ios_cb=1"))
        self.assertIsNotNone(re.fullmatch(PATTERN,
            "V234_SOURCE isfs=1 count=1 ios=1 isfs_valid=1 ios_valid=0 mode_isfs=0 mode_ios=1 nand_cb=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v234-sc-isfs-origin.yml").read_text()
        for x in ("run_v234_sc_isfs_origin.sh",
                  "test_v234_sc_isfs_origin.py",
                  "V234_SC_ISFS_ORIGIN verified=1"):
            self.assertIn(x,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,src in (("runner",script),("wrapper",(HERE/"run_v234_sc_isfs_origin.sh").read_text())):
                path=Path(tmp)/name;path.write_text(src,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)
if __name__=="__main__":
    unittest.main()
