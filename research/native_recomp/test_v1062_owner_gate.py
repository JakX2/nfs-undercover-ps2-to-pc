import copy
import unittest
from verify_v1062_owner_gate import BRANCH, REQUIREMENTS, verify


class OwnerGate(unittest.TestCase):
    def setUp(self):
        self.req = REQUIREMENTS[0]
        self.run = dict(id=self.req.run_id, head_sha=self.req.head, head_branch=BRANCH,
                        path=self.req.path, status='completed', conclusion='success', run_attempt=2)
        self.owner = dict(name=self.req.owner, run_id=self.req.run_id,
                          status='completed', conclusion='success')
        self.jobs = dict(total_count=2, jobs=[dict(name='original-free', status='completed',
                                                  conclusion='success'), self.owner])
        self.calls = []

    def fetch(self, path):
        self.calls.append(path)
        base = f'actions/runs/{self.req.run_id}'
        if path == base:
            return self.run
        if path == base + '/attempts/2/jobs?per_page=100':
            return self.jobs
        self.fail('unexpected request')

    def test_new_pinned_requirements(self):
        expected = [(45753506495, 'owner-execution'), (45756409951, 'owner-context'),
                    (45757000670, 'owner-context')]
        self.assertEqual([(r.run_id, r.owner) for r in REQUIREMENTS[-3:]], expected)
        self.assertEqual(len({r.run_id for r in REQUIREMENTS}), len(REQUIREMENTS))
        for req in REQUIREMENTS[-3:]:
            self.req = req
            self.run.update(id=req.run_id, head_sha=req.head, path=req.path)
            self.owner.update(name=req.owner, run_id=req.run_id)
            self.assertTrue(verify(self.fetch, req))
            self.owner['conclusion'] = 'skipped'
            self.assertFalse(verify(self.fetch, req))
            self.owner['conclusion'] = 'success'

    def test_success_and_attempt_pinning(self):
        self.assertTrue(verify(self.fetch, self.req))
        self.assertEqual(self.calls, [f'actions/runs/{self.req.run_id}',
                                      f'actions/runs/{self.req.run_id}/attempts/2/jobs?per_page=100'])

    def test_run_identity_and_incomplete(self):
        for key, value in (('id', 0), ('head_sha', 'wrong'), ('head_branch', 'main'),
                           ('path', 'wrong'), ('status', 'in_progress'), ('conclusion', 'failure'),
                           ('run_attempt', True), ('run_attempt', 0), ('run_attempt', None)):
            with self.subTest(key=key, value=value):
                old = self.run[key]
                self.run[key] = value
                self.calls.clear()
                self.assertFalse(verify(self.fetch, self.req))
                self.assertEqual(len(self.calls), 1)
                self.run[key] = old

    def test_owner_job_is_required(self):
        for key, value in (('name', 'unrelated'), ('run_id', 0), ('status', 'in_progress'),
                           ('conclusion', 'skipped'), ('conclusion', 'cancelled'),
                           ('conclusion', 'failure'), ('conclusion', None)):
            with self.subTest(key=key, value=value):
                old = self.owner[key]
                self.owner[key] = value
                self.assertFalse(verify(self.fetch, self.req))
                self.owner[key] = old

    def test_duplicate_and_incomplete_census(self):
        self.jobs['jobs'].append(copy.copy(self.owner))
        self.jobs['total_count'] = 3
        self.assertFalse(verify(self.fetch, self.req))
        self.jobs['jobs'].pop()
        self.assertFalse(verify(self.fetch, self.req))
        self.jobs['jobs'] = []
        self.jobs['total_count'] = 0
        self.assertFalse(verify(self.fetch, self.req))

    def test_malformed_metadata(self):
        for result in (None, [], {}, {'total_count': True, 'jobs': [self.owner]},
                       {'total_count': 1, 'jobs': [None]}, {'total_count': 1, 'jobs': 'x'}):
            with self.subTest(result=result):
                self.jobs = result
                self.assertFalse(verify(self.fetch, self.req))
        self.run = None
        self.assertFalse(verify(self.fetch, self.req))


if __name__ == '__main__':
    unittest.main()
