#!/usr/bin/env python3
"""V375 authentic Y1 boundary, source and privacy invariants."""
import tempfile
import unittest
from pathlib import Path
from derive_v375_nand_y1_boundary import INJECTION,HEAD,MARKER,patch
from analyze_v375_nand_y1_boundary import inspect

BASE=(
  '#include "native_external_irq.h"\n'
  'void previous(){const char* a="V374_NAND_REPLY_GATE n=";'
  'const char* b="V373_NAND_IRQ_TIMELINE n=";}\n'
  'bool v250_candidate_mode=false;unsigned v250_nand_seen=0;\n'
  'void next(){if(v250_candidate_mode&&v250_nand_seen){}'
  'int irq74_vector=0;}\n'+HEAD+'\n}\n'
)

def line(n=1,*,call=1,running=1,dispatch=1,aligned=1,mode=1,ee=1,
         installed=1,preemptible=1,site=3,drained=1):
    return (
      f'V375_NAND_Y1_BOUNDARY n={n} call={call} running={running} '
      f'dispatch={dispatch} aligned={aligned} mode={mode} ee={ee} '
      f'installed={installed} preemptible={preemptible} '
      f'site={site} drained={drained}\n'
    )

def run(text):
    with tempfile.TemporaryDirectory() as folder:
        f=Path(folder)/'owner-secret.log'
        f.write_text(text,encoding='utf-8')
        return inspect(f,0)

class Tests(unittest.TestCase):
    def test_exact_one_read_only_guest_injection(self):
        out=patch(BASE)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.replace(HEAD+INJECTION,HEAD,1),BASE)
        for require in (
            'ctx.pc==addr','ctx.is_running','!ctx.dispatch_saved_ctx',
            'external_exception_pending(ctx.msr)', 'ctx.msr&B::MSR_EE',
            'M::Y1','M::Y2','H::IPC_PPC','irq74_vector.size()',
            'v375_count<24u','const bool preemptible=',
            '" site="','" drained="'
        ):
            self.assertIn(require,INJECTION)
        for forbidden in (
            'enter_external_irq(', 'ios.scheduler', 'service_one(',
            'ipc70_bus.write32(', 'ipc70_bus.tick(', 'ctx.pc=',
            'ctx.msr=', 'ctx.gpr[', 'ctx.srr0=', 'throw ExceptionStop',
            'std::hex','<<ctx.pc','<<addr','std::cout<<ctx.gpr'
        ):
            self.assertNotIn(forbidden,INJECTION)
    def test_fail_closed_on_geometry_drift(self):
        for s in (
            BASE.replace(HEAD,''),
            BASE+HEAD,
            BASE.replace('V373_NAND_IRQ_TIMELINE n=','absent'),
            BASE.replace('native_external_irq.h','different.h'),
            BASE.replace('v250_nand_seen','different_state'),
            patch(BASE),
        ):
            with self.assertRaises(ValueError):
                patch(s)
    def test_first_preemptible_and_site_summary(self):
        s=line(1,call=0,preemptible=0,drained=0,site=1)+line(
          2,preemptible=1,site=3)
        out=run(s)
        self.assertIn('samples=2 first_preemptible=2',out)
        self.assertIn('preemptible_any=1 drained_any=1 site_mask=5',out)
        self.assertNotIn('owner-secret.log',out)
    def test_invalid_untrusted_records_not_positive(self):
        for s in (
            'private '+line(),
            line(1,call=0,preemptible=1),
            line(1,ee=0,preemptible=0),
            line(2),
            line(1,site=4),
            line(25)
        ):
            self.assertIn('samples=0',run(s))
        self.assertIn('samples=1',run(line(1)+line(3)))

if __name__=='__main__':
    unittest.main()
