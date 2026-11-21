#!/usr/bin/env python3
"""V186 source-only native IOS second request Starlet ACK and safety tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v185_sc_reply_next_harness import derive as previous
from derive_v186_second_ios_ack_harness import (derive, STOP, HANDOFF, NEXT_TRIAL, PREVIOUS_OBSERVER,
    V153_FIRST_REPLY_GUARD, V186_SCOPED_V153_GUARD)
from derive_v186_second_ios_ack_runner import (
    derive as runner, PRE, ACK, STATE, PASS_PRE, PASS_ACK, PASS_STATE
)
HERE=Path(__file__).resolve().parent

class V186(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_only_service_at_verified_original_yield_and_maintain_guest_pc(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertIn(STOP,self.before)
        # The authenticated stop suffix is deliberately retained *after*
        # the one real IOS service step, not deleted or bypassed.
        self.assertIn(STOP,HANDOFF)
        self.assertLess(HANDOFF.index("scheduler.service_one(ctx.msr)"),
                        HANDOFF.index(STOP))
        self.assertIn(HANDOFF,self.after)
        self.assertIn("addr==0x80529434u&&ctx.lr==0x80526cb0u",HANDOFF)
        self.assertIn("v183_second_msg==1u&&v183_second_ctrl==1u",HANDOFF)
        self.assertIn("v183_second_cmd==V186Ios::Open",HANDOFF)
        self.assertIn("v186_latched=ipc70_bus.pending_native_ios_request()",HANDOFF)
        self.assertIn("v186_empty=ipc70_bus.services().queued_replies()==0u",HANDOFF)
        self.assertIn("scheduler.service_one(ctx.msr)",HANDOFF)
        self.assertIn("V186Ios::Pump::Ack",HANDOFF)
        self.assertIn("v186_cpu=ctx.pc==v186_pc&&ctx.lr==v186_lr",HANDOFF)
        self.assertIn("ctx.is_running=false;throw ExceptionStop{};",HANDOFF)
        self.assertIn(NEXT_TRIAL,self.after)

    def test_native_ios_ack_not_fake_reply_or_reset_guest_cpu(self):
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                      "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick("):
            self.assertEqual(self.before.count(token),self.after.count(token),token)
        self.assertEqual(
            self.after.count("scheduler.service_one(ctx.msr)"),
            self.before.count("scheduler.service_one(ctx.msr)")+1)
        self.assertNotIn("ctx.mmu.write",HANDOFF)
        self.assertNotIn("ipc70_ram.write",HANDOFF)
        self.assertNotIn("ipc70_bus.write",HANDOFF)
        self.assertNotIn("ios_.pump(",HANDOFF)
        self.assertNotRegex(HANDOFF,r'\bctx\.(?:pc|lr|msr|inst_count)\s*=(?!=)')
        self.assertIn("ipc70_ram.read32(v183_second_phys)==V186Ios::Open",HANDOFF)
        self.assertIn("queued_replies()==1u",HANDOFF)
        self.assertIn("v186_result.serviced_steps==1u",HANDOFF)
        self.assertIn("!ipc70_bus.pending_native_ios_request()",HANDOFF)
        self.assertIn("V186Mail::Y2",HANDOFF)
        for source_tag in ("V185_IPC_ENTRY phase=1","V185_SC_NEXT clean=",
                           "V184_SC_BURST calls=","V183_SECOND_CTRL phase=1"):
            self.assertEqual(self.before.count(source_tag),self.after.count(source_tag),source_tag)

    def test_v153_first_reply_assertion_only_loosens_at_verified_second_ack(self):
        self.assertEqual(self.before.count(V153_FIRST_REPLY_GUARD),1)
        self.assertEqual(self.after.count(V186_SCOPED_V153_GUARD),1)
        self.assertIn("v153_bridge&&v153_wire&&v153_mail&&v153_drained&&v153_irq",
                      V186_SCOPED_V153_GUARD)
        self.assertIn("nwii::runtime::v186_ack_seen==1u",
                      V186_SCOPED_V153_GUARD)
        self.assertIn("nwii::runtime::v185_next_seen==1u",
                      V186_SCOPED_V153_GUARD)
        self.assertIn("nwii::runtime::v183_second_ctrl==1u",
                      V186_SCOPED_V153_GUARD)
        self.assertIn("c.pc==0x80529434u&&c.lr==0x80526cb0u",
                      V186_SCOPED_V153_GUARD)
        self.assertEqual(
            self.before.count("V153 original SC IRQ did not deliver queued SYSCONF file-open reply"),
            self.after.count("V153 original SC IRQ did not deliver queued SYSCONF file-open reply"))

    def test_bounded_runner_sixteen_owner_trials_and_native_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v186_second_ios_ack_harness.py",script)
        self.assertIn("V185_SC_NEXT verified=1",script)
        self.assertIn("V186_SECOND_ACK verified=1",script)
        for pattern,line in (
            (PASS_PRE,"V186_IOS_PRE route=1 prior=1 intake=1 clear=1 open=1 idle=1 sc=1"),
            (PASS_ACK,"V186_SECOND_ACK ack=1 y2=1 irq=1 queued=1 consumed=1 original=1 cpu=1 sc=1"),
            (PASS_STATE,"V186_ACK_STATE guest=1 mail=1 service=1")):
            self.assertTrue(re.fullmatch(pattern,line))
        self.assertFalse(re.fullmatch(PASS_ACK,
            "V186_SECOND_ACK ack=0 y2=1 irq=1 queued=1 consumed=1 original=1 cpu=1 sc=1"))
        self.assertTrue(re.fullmatch(PRE,"V186_IOS_PRE route=0 prior=0 intake=0 clear=0 open=0 idle=0 sc=0"))
        self.assertTrue(re.fullmatch(ACK,"V186_SECOND_ACK ack=0 y2=1 irq=1 queued=1 consumed=1 original=1 cpu=1 sc=1"))
        self.assertTrue(re.fullmatch(STATE,"V186_ACK_STATE guest=0 mail=1 service=1"))
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_bounded_owner_native_compiler_pipeline_markers(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn('V186_BUILD unit=$unit',s)
        self.assertIn("V186_BUILD link=1",s)
        self.assertIn("V186_BUILD execute=1",s)
        self.assertIn("V77_COMPILE_UNIT",s)
        self.assertIn("V67_NATIVE_ASSERTION",s)

    def test_source_guards_and_owner_private_workflow(self):
        with self.assertRaises(ValueError):derive("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v186-second-ios-ack.yml").read_text(encoding="utf-8")
        self.assertIn("run_v186_second_ios_ack.sh",wf)
        self.assertIn("V186_SECOND_ACK verified=1",wf)
        self.assertIn("V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=1",wf)
        self.assertIn("  cancel-in-progress: false",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
