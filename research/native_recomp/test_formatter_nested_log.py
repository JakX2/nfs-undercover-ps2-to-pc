#!/usr/bin/env python3
import unittest
from validate_formatter_nested_log import verify,markers

def log(second=False):
    tag,_,total=markers(second);visits,loads=(44,2) if second else (35,1)
    conditional=' conditional_load=1' if second else ''
    rows=[]
    for i in range(8):
        rows.append(f'{tag}_TRIAL n={i} native_prefix=1 frame=48 loads={loads} stores=12 nonvolatile=3{conditional} pre_load_stop=1 deferred=1 reply=0 visits={visits}')
        rows.append(f'FORMATTER_NESTED_CELL_TRIAL n={i} cold_match=1 live_match={int(i!=0)} sample_equal={int(i!=0)} guest_load=0')
    return rows+['FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match=8 live_match=7 sample_equal=7 endpoint_only=1 guest_loads=0 guest_writes=0',total]
class Test(unittest.TestCase):
    def test_exact(self):
        for mode in (False,True):self.assertEqual(verify(log(mode),second=mode),tuple(log(mode)[-2:]))
    def test_duplicate(self):
        x=log();x[2]=x[0]
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x)
        x=log();x[3]=x[1]
        with self.assertRaisesRegex(ValueError,'cell trial'):verify(x)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log()[2:])
    def test_false_total(self):
        x=log();x[-2]=x[-2].replace('live_match=7','live_match=8')
        with self.assertRaisesRegex(ValueError,'totals'):verify(x)
    def test_false_equality(self):
        x=log();x[1]=x[1].replace('sample_equal=0','sample_equal=1')
        with self.assertRaisesRegex(ValueError,'consistency'):verify(x)
    def test_native_refusal(self):
        with self.assertRaisesRegex(ValueError,'refusal'):verify(log()+['FORMATTER_NESTED_REFUSAL kind=2'])
    def test_cross_mode(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log(True))
def third_log():
    rows=log()
    for i in range(8):
        rows[2*i]=f'FORMATTER_THIRD_TRIAL n={i} native_prefix=1 frame=48 loads=5 stores=13 nonvolatile=3 authenticated_loads=4 conditional_loads=2 pre_load_stop=1 deferred=1 reply=0 visits=74'
    rows[-1]='FORMATTER_THIRD_NATIVE owner=1 trials=8 native_prefix=8 loads=40 stores=104 nonvolatile=24 authenticated_loads=32 conditional_loads=16 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=592 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return rows
class Third(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(third_log(),third=True),tuple(third_log()[-2:]))
    def test_details(self):
        x=third_log();x[2]=x[2].replace('authenticated_loads=4','authenticated_loads=3')
        with self.assertRaisesRegex(ValueError,'details'):verify(x,third=True)
    def test_totals(self):
        x=third_log();x[-1]=x[-1].replace('authenticated_loads=32','authenticated_loads=24')
        with self.assertRaisesRegex(ValueError,'native totals'):verify(x,third=True)
    def test_counts(self):
        x=third_log();x[0]=x[0].replace('authenticated_loads=4','authenticated_loads=2')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,third=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(third_log(),second=True)
        with self.assertRaisesRegex(ValueError,'mode'):verify(third_log(),second=True,third=True)
def control_log():
    rows=[f'FORMATTER_CONTROL_TRIAL n={i} native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 pre_transfer_stop=1 transfer_executed=0 deferred=1 reply=0 visits=76' for i in range(8)]
    return rows+['FORMATTER_CONTROL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 pre_transfer_stop=8 transfer_executed=0 deferred=8 reply=0 visits=608 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Control(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(control_log(),control=True),tuple(control_log()[-1:]))
    def test_target(self):
        x=control_log();x[0]=x[0].replace('ctr_match=1','ctr_match=0')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,control=True)
    def test_transfer(self):
        x=control_log();x[-1]=x[-1].replace('transfer_executed=0','transfer_executed=1')
        with self.assertRaisesRegex(ValueError,'native aggregate'):verify(x,control=True)
    def test_cell(self):
        with self.assertRaisesRegex(ValueError,'unexpected cell'):verify(control_log()+[log()[1]],control=True)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(control_log()[1:],control=True)
    def test_mixed(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(control_log(),control=True,third=True)
def arrival_log():
    return [f'FORMATTER_ARRIVAL_TRIAL n={i} native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 transfer_executed=1 destination_arrival=1 destination_body=0 deferred=1 reply=0 visits=77' for i in range(8)]+['FORMATTER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 transfer_executed=8 destination_arrival=8 destination_body=0 deferred=8 reply=0 visits=616 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Arrival(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(arrival_log(),arrival=True),tuple(arrival_log()[-1:]))
    def test_transfer(self):
        x=arrival_log();x[0]=x[0].replace('transfer_executed=1','transfer_executed=0')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,arrival=True)
    def test_body(self):
        x=arrival_log();x[-1]=x[-1].replace('destination_body=0','destination_body=8')
        with self.assertRaisesRegex(ValueError,'native aggregate'):verify(x,arrival=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(arrival_log(),arrival=True,control=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(control_log(),arrival=True)
def post_ctr_log():
    return [f'FORMATTER_POST_CTR_TRIAL n={i} native_prefix=1 frame=48 loads=8 stores=13 nonvolatile=3 authenticated_loads=5 local_transfer=1 stack_stop=1 unresolved_load=0 deferred=1 reply=0 visits=84' for i in range(8)]+['FORMATTER_POST_CTR_NATIVE owner=1 trials=8 native_prefix=8 loads=64 stores=104 nonvolatile=24 authenticated_loads=40 local_transfer=8 stack_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=672 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class PostCtr(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(post_ctr_log(),post_ctr=True),tuple(post_ctr_log()[-1:]))
    def test_count(self):
        x=post_ctr_log();x[-1]=x[-1].replace('authenticated_loads=40','authenticated_loads=48')
        with self.assertRaisesRegex(ValueError,'native totals'):verify(x,post_ctr=True)
    def test_details(self):
        x=post_ctr_log();x[1]=x[1].replace('authenticated_loads=5','authenticated_loads=6')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,post_ctr=True)
    def test_unresolved(self):
        x=post_ctr_log();x[0]=x[0].replace('unresolved_load=0','unresolved_load=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,post_ctr=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(post_ctr_log(),post_ctr=True,arrival=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(arrival_log(),post_ctr=True)
def partial_log():
    return [f'FORMATTER_PARTIAL_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 instruction_stop=1 deferred=1 reply=0 visits=95' for i in range(8)]+['FORMATTER_PARTIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 instruction_stop=8 deferred=8 reply=0 visits=760 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Partial(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(partial_log(),partial=True),tuple(partial_log()[-1:]))
    def test_reject_stale_load_totals(self):
        x=partial_log();x[0]=x[0].replace('loads=15','loads=9')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,partial=True)
        x=partial_log();x[-1]=x[-1].replace('loads=120','loads=72')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,partial=True)
    def test_parent(self):
        x=partial_log();x[1]=x[1].replace('parent_overlay=1','parent_overlay=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,partial=True)
    def test_total(self):
        x=partial_log();x[-1]=x[-1].replace('caller_stores=32','caller_stores=24')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,partial=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(partial_log(),partial=True,post_ctr=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(post_ctr_log(),partial=True)
    def test_missing_and_duplicate(self):
        for x in (partial_log()[1:],partial_log()+[partial_log()[0]]):
            with self.assertRaises(ValueError):verify(x,partial=True)
class Special(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_SPECIAL_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 instruction_stop=1 deferred=1 reply=0 visits=96' for i in range(8)]+['FORMATTER_SPECIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 instruction_stop=8 deferred=8 reply=0 visits=768 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,special=True),(x[-1],))
    def test_lr(self):
        x=self.logs();x[0]=x[0].replace('lr_restored=1','lr_restored=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,special=True)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('visits=768','visits=760')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,special=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(partial_log(),special=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),special=True,partial=True)
class Release(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_RELEASE_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 return_stop=1 return_executed=0 deferred=1 reply=0 visits=97' for i in range(8)]+['FORMATTER_RELEASE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 return_stop=8 return_executed=0 deferred=8 reply=0 visits=776 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,release=True),(x[-1],))
    def test_return_not_executed(self):
        x=self.logs();x[0]=x[0].replace('return_executed=0','return_executed=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,release=True)
    def test_registers(self):
        x=self.logs();x[-1]=x[-1].replace('nonvolatile=144','nonvolatile=24')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,release=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(Special().logs(),release=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),release=True,special=True)
class Return(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_RETURN_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_arrival=1 caller_body=0 caller_guard=1 deferred=1 reply=0 visits=98' for i in range(8)]+['FORMATTER_RETURN_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_arrival=8 caller_body=0 caller_guard=8 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,return_mode=True),(x[-1],))
    def test_caller_body(self):
        x=self.logs();x[0]=x[0].replace('caller_body=0','caller_body=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,return_mode=True)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('visits=784','visits=776')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,return_mode=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(Release().logs(),return_mode=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),return_mode=True,release=True)
if __name__=='__main__':unittest.main(verbosity=2)
