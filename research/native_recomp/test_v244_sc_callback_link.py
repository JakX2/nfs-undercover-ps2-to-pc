#!/usr/bin/env python3
"""V244 source-only first callback nested branch/link evidence tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v242_sc_callback_call_route_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v244_sc_callback_link_runner import derive as runner, NEST, FRAME, PATTERN, PASS

HERE=Path(__file__).resolve().parent

class V244(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source);cls.after=derive(source)

    def test_owner_callback_and_saved_link(self):
        for marker in ("addr==0x804f0e04u","v241_cb_count==0u",
                       "userdata+256u","v244_cb_sp=ctx.gpr[1]",
                       "addr==0x80545100u","v238_save_count==1u",
                       "ctx.mmu.read32(sp+36u)",
                       "v244_cb_sp-sp==32u","v244_cb_sp-sp==48u",
                       "saved==0x805192acu","saved==0x804f0f54u",
                       "V244_CB_NEST","V244_FRAME"):
            self.assertIn(marker,TRACE)
        for marker in ("V244_LINK","v244_cb_seen==1u",
                       "v244_save_seen==1u","++v244_submit_seen"):
            self.assertIn(marker,SEND)
        self.assertIn(TRACE,self.after)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertEqual(self.after.count("nwii::runtime::v244_submit_seen==1u&&"),1)
        self.assertNotIn("<<v244_cb_sp",TRACE+SEND)
        self.assertNotIn("<<v244_nested_target",TRACE+SEND)
        with self.assertRaises(ValueError):derive("not a harness")

    def test_read_only_probe(self):
        for word in ("ipc70_bus.write32(","ipc70_ram.write8(",
                     "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(word),self.after.count(word))
        for part in (TRACE,SEND):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                              "<<ctx.gpr","<<ctx.ctr","<<ctx.mmu"):
                self.assertNotIn(forbidden,part)
            self.assertNotRegex(part,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")

    def test_owner_original_16_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("derive_v244_sc_callback_link_harness.py",
                       "V242_SC_CALLBACK_CALL_ROUTE verified=1",
                       "V244_SC_CALLBACK_LINK verified=1"):
            self.assertIn(marker,script)
        good="V244_LINK cb=1 save=1 registered=1 abi=1 userdata=1 frame32=1 frame48=0 outer_lr=1 nested_lr=0 isfs_entry=0 nested_text=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("registered=1","registered=0")))
        self.assertIsNotNone(re.fullmatch(NEST,"V244_CB_NEST registered=1 abi=1 mapped=1 text=1 isfs=0 nand=1 null=0"))
        self.assertIsNotNone(re.fullmatch(FRAME,"V244_FRAME mapped=1 frame32=1 frame48=0 other=0 outer_lr=1 nested_lr=0 text_lr=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v244-sc-callback-link.yml").read_text()
        for item in ("run_v244_sc_callback_link.sh",
                     "test_v244_sc_callback_link.py",
                     "V244_SC_CALLBACK_LINK verified=1"):
            self.assertIn(item,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v244_sc_callback_link.sh").read_text())):
                p=Path(tmp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
