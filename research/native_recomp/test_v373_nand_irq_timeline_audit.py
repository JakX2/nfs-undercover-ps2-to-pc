#!/usr/bin/env python3
"""Original-free V373 post-ACK IRQ timeline audit and privacy tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v373_nand_irq_timeline import inspect
from diagnose_v299_native_log import WINDOW

def sample(n:int,*,ee:int=0,irq:int=1,eligible:int=0,safe:int=1,
           installed:int=1,ready:int=0,y1:int=0,y2:int=1,
           flag:int=1,queued:int=1)->str:
    return (
        f"V373_NAND_IRQ_TIMELINE n={n} ee={ee} irq={irq} "
        f"eligible={eligible} safe={safe} installed={installed} "
        f"ready={ready} y1={y1} y2={y2} flag={flag} queued={queued}\n"
    )

def run(content:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'owner-secret.log'
        path.write_text(content,encoding='utf-8')
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_separates_pending_irq_from_msr_ee(self):
        value=run('private guest state\n'
                  +sample(1,ee=0,irq=1,eligible=0,ready=0)
                  +sample(2,ee=1,irq=1,eligible=1,ready=1,y2=0,flag=0))
        self.assertIn('samples=2 first_ee=2 first_irq=1 first_ready=2',value)
        self.assertIn('ee_any=1 irq_any=1 eligible_any=1',value)
        self.assertIn('y2_any=1 flag_any=1 queued_any=1',value)
        self.assertNotIn('private guest state',value)
        self.assertNotIn('owner-secret.log',value)

    def test_irq_stays_masked_and_reply_is_still_queued(self):
        result=run(sample(1,ee=0,irq=0,eligible=0,ready=0,
                          y1=0,y2=0,flag=0))
        self.assertIn('samples=1 first_ee=0 first_irq=0 first_ready=0',result)
        self.assertIn('irq_any=0 eligible_any=0',result)
        self.assertIn('queued_any=1',result)
        self.assertNotIn('handler_completed',result)

    def test_post_dequeue_y1_is_visible_without_claiming_handler_return(self):
        value=run(sample(1,ee=1,irq=1,eligible=1,ready=1,
                         y1=1,y2=0,flag=1,queued=0))
        self.assertIn('samples=1 first_ee=1 first_irq=1 first_ready=1',value)
        self.assertIn('y1_any=1 y2_any=0 flag_any=1 queued_any=0',value)
        self.assertNotIn('handler_completed',value)

    def test_truncation_and_missing_markers_cannot_fake_readiness(self):
        result=run('prefix '+sample(1)+sample(3,ee=1,eligible=1,ready=1))
        self.assertIn('samples=0',result)
        result=run(sample(1)+sample(3,ee=1,eligible=1,ready=1))
        self.assertIn('samples=1 first_ee=0 first_irq=1 first_ready=0',result)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'owner.log'
            with path.open('wb') as stream:
                stream.write(sample(1).encode('ascii'))
                stream.seek(WINDOW+200)
                stream.write(b'\nend\n')
            self.assertIn('sample_complete=0 samples=1',inspect(path,124))

    def test_malformed_values_and_out_of_range_sequence_fail_closed(self):
        self.assertIn('samples=0',run(sample(1).replace('ee=0','ee=2')))
        self.assertIn('samples=0',run(sample(97)))
        for rc in (-1,256):
            with self.assertRaises(ValueError):
                run('',rc)

if __name__=="__main__":
    unittest.main()
