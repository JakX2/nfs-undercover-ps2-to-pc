import contextlib
import io
import unittest
from verify_v1062_owner_gate import BRANCH
from verify_v1244_ipc_owner_gate import REQUIREMENTS, classify, gate

class Gate(unittest.TestCase):
    def setUp(self):
        self.runs={r.run_id:dict(id=r.run_id,head_sha=r.head,head_branch=BRANCH,path=r.path,
                    status='completed',conclusion='success',run_attempt=1) for r in REQUIREMENTS}
        self.jobs={r.run_id:dict(total_count=1,jobs=[dict(name=r.owner,run_id=r.run_id,
                    status='completed',conclusion='success')]) for r in REQUIREMENTS}
        self.elapsed=0
    def fetch(self,path):
        parts=path.split('/')
        run=int(parts[2])
        if len(parts)==3:return self.runs[run]
        self.assertEqual('/'.join(parts[3:]),'attempts/1/jobs?per_page=100')
        return self.jobs[run]
    def run_gate(self,wait=False,sleep=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return gate(self.fetch,wait,lambda:self.elapsed,sleep or self.advance)
    def advance(self,seconds):self.elapsed+=seconds
    def test_success(self):self.assertEqual(self.run_gate(),0)
    def test_pending_then_complete(self):
        r=self.runs[REQUIREMENTS[0].run_id]
        r.update(status='in_progress',conclusion=None)
        self.assertEqual(self.run_gate(),1)
        def finish(seconds):
            self.advance(seconds);r.update(status='completed',conclusion='success')
        self.assertEqual(self.run_gate(True,finish),0)
        self.assertEqual(self.elapsed,60)
    def test_pending_timeout(self):
        self.runs[REQUIREMENTS[1].run_id].update(status='queued',conclusion=None)
        self.assertEqual(self.run_gate(True),1)
        self.assertEqual(self.elapsed,2400)
    def test_fail_closed(self):
        req=REQUIREMENTS[0];r=self.runs[req.run_id]
        for k,v in [('head_sha','bad'),('path','bad'),('head_branch','main'),('run_attempt',2),
                    ('run_attempt',True),('conclusion','failure'),('conclusion','cancelled'),
                    ('status','unknown'),('status','queued')]:
            with self.subTest(k=k,v=v):
                old=r[k];r[k]=v
                self.assertEqual(classify(self.fetch,req),'refused')
                r[k]=old
        self.jobs[req.run_id]['jobs'][0]['conclusion']='skipped'
        self.assertEqual(self.run_gate(True),1)
        self.assertEqual(self.elapsed,0)
    def test_pending_identity(self):
        req=REQUIREMENTS[1];r=self.runs[req.run_id]
        r.update(status='in_progress',conclusion=None,head_sha='wrong')
        self.assertEqual(classify(self.fetch,req),'refused')

if __name__=='__main__':unittest.main()
